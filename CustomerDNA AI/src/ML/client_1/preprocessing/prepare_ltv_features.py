from __future__ import annotations

import argparse
import json
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import numpy as np
    import pandas as pd
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "pandas and numpy are required for LTV preprocessing. Install them in your local environment first."
    ) from exc

try:
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "scikit-learn is required for LTV preprocessing. Install it in your local environment first."
    ) from exc

CURRENT_DIR = Path(__file__).resolve().parent
CLIENT_ML_ROOT = CURRENT_DIR.parent
DATA_ACCESS_DIR = CLIENT_ML_ROOT / "data_access"
if str(DATA_ACCESS_DIR) not in sys.path:
    sys.path.append(str(DATA_ACCESS_DIR))

from schema_manifest import (  # noqa: E402
    EXPERIMENT_REPORTS_DIR,
    ensure_dataset_directories,
    ensure_model_directories,
    isoformat_utc,
    load_common_config,
    load_use_case_config,
    preprocessing_artifact_paths,
    read_json,
)


SKEW_TRANSFORM_MIN_THRESHOLD = 2.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare regression-ready features from the latest LTV serving snapshot.",
    )
    parser.add_argument(
        "--use-case",
        default="ltv",
        help="Use-case config name stored under src/ML/client_1/configs without the .json suffix.",
    )
    parser.add_argument(
        "--manifest-path",
        default=None,
        help="Optional explicit snapshot manifest path.",
    )
    parser.add_argument(
        "--audit-path",
        default=None,
        help="Optional explicit audit JSON path.",
    )
    return parser.parse_args()


def find_latest_file(directory: Path, pattern: str) -> Path:
    candidates = sorted(
        directory.glob(pattern),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No files found for pattern '{pattern}' in {directory}")
    return candidates[0]


def find_latest_manifest(use_case_config: dict[str, Any]) -> Path:
    return find_latest_file(
        CLIENT_ML_ROOT / "datasets" / "manifests",
        f"{use_case_config['snapshot_prefix']}_*.json",
    )


def find_latest_audit(use_case_config: dict[str, Any]) -> Path:
    return find_latest_file(
        EXPERIMENT_REPORTS_DIR,
        f"{use_case_config['snapshot_prefix']}_audit_*.json",
    )


def build_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def main() -> None:
    args = parse_args()
    common_config = load_common_config()
    use_case_config = load_use_case_config(args.use_case)
    preprocessing_config = use_case_config.get("preprocessing", {})
    target_column = use_case_config["target_column"]
    transformed_target_column = f"{target_column}_transformed"

    manifest_path = Path(args.manifest_path) if args.manifest_path else find_latest_manifest(use_case_config)
    audit_path = Path(args.audit_path) if args.audit_path else find_latest_audit(use_case_config)

    manifest = read_json(manifest_path)
    audit = read_json(audit_path)
    snapshot_path = Path(manifest["artifacts"]["snapshot_path"])
    primary_key_column = manifest["source"]["primary_key"]
    reference_label_columns = manifest["modeling_contract"]["reference_label_columns"]
    candidate_feature_columns = manifest["modeling_contract"]["candidate_feature_columns"]
    non_feature_columns = manifest["modeling_contract"]["non_feature_columns"]

    if audit["primary_key_checks"]["duplicate_primary_key_rows"] != 0:
        raise ValueError("Duplicate primary keys detected in the audit. Fix snapshot integrity before preprocessing.")

    df = pd.read_csv(snapshot_path, low_memory=False)

    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' was not found in the snapshot.")

    target_series = pd.to_numeric(df[target_column], errors="coerce")
    if target_series.isna().any():
        raise ValueError(f"Target column '{target_column}' contains non-numeric values after coercion.")

    target_negative_count = int((target_series < 0).sum())
    requested_log1p_to_target = bool(preprocessing_config.get("apply_log1p_to_target", True))
    apply_log1p_to_target = requested_log1p_to_target and target_negative_count == 0
    target_log_transform_skipped_reason = None

    if requested_log1p_to_target and target_negative_count > 0:
        target_log_transform_skipped_reason = (
            "Target contains negative values, so log1p transform was skipped and the raw target was preserved."
        )

    transformed_target_series = np.log1p(target_series) if apply_log1p_to_target else target_series.copy()

    null_columns = {
        item["column_name"]
        for item in audit["data_quality"]["columns_with_nulls"]
    }
    selected_null_columns = sorted(null_columns.intersection(candidate_feature_columns))
    if selected_null_columns:
        raise ValueError(
            "Selected feature columns still contain nulls: " + ", ".join(selected_null_columns)
        )

    constant_columns = set(audit["data_quality"]["constant_columns"])
    near_constant_columns = {
        item["column_name"]
        for item in audit["data_quality"]["near_constant_columns"]
    }
    leakage_exclusion_columns = set(use_case_config.get("leakage_exclusion_columns", []))

    raw_feature_columns = list(candidate_feature_columns)
    dropped_columns: list[str] = []

    dropped_columns.extend(
        sorted(
            column_name
            for column_name in leakage_exclusion_columns.intersection(raw_feature_columns)
            if column_name not in dropped_columns
        )
    )

    if preprocessing_config.get("drop_constant_columns", True):
        dropped_columns.extend(sorted(constant_columns.intersection(raw_feature_columns)))

    if preprocessing_config.get("drop_near_constant_columns", True):
        dropped_columns.extend(
            sorted(
                column_name
                for column_name in near_constant_columns.intersection(raw_feature_columns)
                if column_name not in dropped_columns
            )
        )

    selected_feature_columns = [
        column_name
        for column_name in raw_feature_columns
        if column_name not in dropped_columns
    ]

    audit_numeric_columns = set(audit["dataset_overview"]["numeric_columns"])
    audit_categorical_columns = set(audit["dataset_overview"]["categorical_columns"])

    numeric_feature_columns = [
        column_name
        for column_name in selected_feature_columns
        if column_name in audit_numeric_columns and column_name != primary_key_column
    ]
    categorical_feature_columns = [
        column_name
        for column_name in selected_feature_columns
        if column_name in audit_categorical_columns and column_name not in reference_label_columns
    ]

    feature_df = df[selected_feature_columns].copy()

    for column_name in categorical_feature_columns:
        feature_df[column_name] = feature_df[column_name].astype("string").fillna("Unknown")

    for column_name in numeric_feature_columns:
        feature_df[column_name] = pd.to_numeric(feature_df[column_name], errors="coerce")

    numeric_null_columns = [
        column_name
        for column_name in numeric_feature_columns
        if feature_df[column_name].isna().any()
    ]
    if numeric_null_columns:
        raise ValueError(
            "Numeric feature columns contain non-numeric values after coercion: "
            + ", ".join(numeric_null_columns)
        )

    high_skew_threshold = float(
        preprocessing_config.get("high_skew_threshold", SKEW_TRANSFORM_MIN_THRESHOLD)
    )
    skew_candidates = {
        item["column_name"]: item
        for item in audit["data_quality"]["high_skew_numeric_columns"]
    }

    log_transformed_numeric_columns: list[str] = []
    skipped_skew_columns: list[str] = []

    if preprocessing_config.get("apply_log1p_to_non_negative_high_skew_numeric", True):
        for column_name in numeric_feature_columns:
            profile = skew_candidates.get(column_name)
            if not profile:
                continue
            if abs(float(profile["skewness"])) < high_skew_threshold:
                continue
            if float(profile["min"]) < 0:
                skipped_skew_columns.append(column_name)
                continue

            feature_df[column_name] = np.log1p(feature_df[column_name])
            log_transformed_numeric_columns.append(column_name)

    transformer_parts = []
    if numeric_feature_columns:
        transformer_parts.append(("numeric", StandardScaler(), numeric_feature_columns))
    if categorical_feature_columns:
        transformer_parts.append(("categorical", build_encoder(), categorical_feature_columns))

    preprocessor = ColumnTransformer(
        transformers=transformer_parts,
        remainder="drop",
    )

    transformed_matrix = preprocessor.fit_transform(feature_df)
    encoded_feature_names = preprocessor.get_feature_names_out().tolist()

    processed_df = pd.DataFrame(transformed_matrix, columns=encoded_feature_names)
    processed_df.insert(0, primary_key_column, df[primary_key_column].values)

    label_columns = [primary_key_column, target_column, transformed_target_column] + [
        column_name
        for column_name in reference_label_columns
        if column_name not in {primary_key_column, target_column, transformed_target_column}
    ]
    labels_df = pd.DataFrame({primary_key_column: df[primary_key_column].values})
    labels_df[target_column] = target_series
    labels_df[transformed_target_column] = transformed_target_series
    for column_name in reference_label_columns:
        labels_df[column_name] = df[column_name].values

    ensure_dataset_directories()
    ensure_model_directories()
    artifact_paths = preprocessing_artifact_paths(
        use_case_config=use_case_config,
        common_config=common_config,
        current_time=datetime.now(timezone.utc),
    )

    processed_df.to_csv(artifact_paths["processed_matrix_path"], index=False)
    labels_df[label_columns].to_csv(artifact_paths["reference_labels_path"], index=False)

    with artifact_paths["preprocessor_path"].open("wb") as handle:
        pickle.dump(preprocessor, handle)

    selected_features_payload = {
        "use_case": use_case_config["use_case"],
        "created_at_utc": isoformat_utc(),
        "target_column": target_column,
        "transformed_target_column": transformed_target_column,
        "raw_feature_columns": selected_feature_columns,
        "numeric_feature_columns": numeric_feature_columns,
        "categorical_feature_columns": categorical_feature_columns,
        "reference_label_columns": reference_label_columns,
        "encoded_feature_columns": encoded_feature_names,
    }
    artifact_paths["selected_features_path"].write_text(
        json.dumps(selected_features_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    preprocessing_metadata = {
        "artifact_type": "ltv_preprocessing",
        "created_at_utc": isoformat_utc(),
        "use_case": use_case_config["use_case"],
        "target_column": target_column,
        "transformed_target_column": transformed_target_column,
        "manifest_path": str(manifest_path),
        "audit_path": str(audit_path),
        "snapshot_path": str(snapshot_path),
        "processed_matrix_path": str(artifact_paths["processed_matrix_path"]),
        "reference_labels_path": str(artifact_paths["reference_labels_path"]),
        "selected_features_path": str(artifact_paths["selected_features_path"]),
        "preprocessor_path": str(artifact_paths["preprocessor_path"]),
        "row_count": int(processed_df.shape[0]),
        "target_min": float(target_series.min()),
        "target_max": float(target_series.max()),
        "target_mean": float(target_series.mean()),
        "target_median": float(target_series.median()),
        "target_zero_count": int((target_series == 0).sum()),
        "target_negative_count": target_negative_count,
        "target_log_transform_requested": requested_log1p_to_target,
        "target_log_transformed": apply_log1p_to_target,
        "target_log_transform_skipped_reason": target_log_transform_skipped_reason,
        "encoded_feature_count": int(len(encoded_feature_names)),
        "raw_feature_count": int(len(selected_feature_columns)),
        "dropped_columns": dropped_columns,
        "dropped_constant_columns": sorted(constant_columns.intersection(raw_feature_columns)),
        "dropped_near_constant_columns": sorted(near_constant_columns.intersection(raw_feature_columns)),
        "dropped_leakage_columns": sorted(leakage_exclusion_columns.intersection(raw_feature_columns)),
        "log_transformed_numeric_columns": log_transformed_numeric_columns,
        "skipped_high_skew_columns_due_to_negative_values": skipped_skew_columns,
        "non_feature_columns": non_feature_columns,
        "preprocessing_rules": preprocessing_config,
    }
    artifact_paths["preprocessing_metadata_path"].write_text(
        json.dumps(preprocessing_metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    print("=" * 80)
    print("CUSTOMERDNA AI - LTV PREPROCESSING")
    print("=" * 80)
    print(f"Use case: {use_case_config['use_case']}")
    print(f"Manifest: {manifest_path}")
    print(f"Audit: {audit_path}")
    print(f"Snapshot: {snapshot_path}")
    print(f"Processed matrix: {artifact_paths['processed_matrix_path']}")
    print(f"Reference labels: {artifact_paths['reference_labels_path']}")
    print(f"Selected features metadata: {artifact_paths['selected_features_path']}")
    print(f"Preprocessing metadata: {artifact_paths['preprocessing_metadata_path']}")
    print(f"Serialized preprocessor: {artifact_paths['preprocessor_path']}")
    print(f"Rows processed: {processed_df.shape[0]}")
    print(f"Raw feature columns kept: {len(selected_feature_columns)}")
    print(f"Encoded feature columns produced: {len(encoded_feature_names)}")
    print(f"Dropped columns: {len(dropped_columns)}")
    print(f"Log-transformed numeric columns: {len(log_transformed_numeric_columns)}")
    print(f"Target negative values: {target_negative_count}")
    print(f"Target log-transformed: {apply_log1p_to_target}")
    if target_log_transform_skipped_reason:
        print(f"Target log-transform note: {target_log_transform_skipped_reason}")
    print("Preprocessing completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
