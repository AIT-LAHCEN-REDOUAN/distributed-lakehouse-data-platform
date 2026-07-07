from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CLIENT_ML_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = CLIENT_ML_ROOT.parents[2]

CONFIGS_DIR = CLIENT_ML_ROOT / "configs"
DATASETS_DIR = CLIENT_ML_ROOT / "datasets"
SNAPSHOTS_DIR = DATASETS_DIR / "snapshots"
MANIFESTS_DIR = DATASETS_DIR / "manifests"
SAMPLES_DIR = DATASETS_DIR / "samples"
PROCESSED_DIR = DATASETS_DIR / "processed"
REPORTS_DIR = CLIENT_ML_ROOT / "reports"
EXPERIMENT_REPORTS_DIR = REPORTS_DIR / "experiment_reports"
BUSINESS_SUMMARIES_DIR = REPORTS_DIR / "business_summaries"
MODELS_DIR = CLIENT_ML_ROOT / "models"
PREPROCESSORS_DIR = MODELS_DIR / "preprocessors"
MODEL_METADATA_DIR = MODELS_DIR / "model_metadata"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime | None = None) -> str:
    current = value or utc_now()
    return current.astimezone(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")

    return payload


def load_common_config() -> dict[str, Any]:
    return read_json(CONFIGS_DIR / "common.json")


def load_use_case_config(use_case: str) -> dict[str, Any]:
    return read_json(CONFIGS_DIR / f"{use_case}.json")


def load_env_file(path: Path) -> dict[str, str]:
    env_vars: dict[str, str] = {}

    if not path.exists():
        raise FileNotFoundError(f"Environment file not found: {path}")

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        env_vars[key.strip()] = value.strip()

    return env_vars


def resolve_client_env_path(common_config: dict[str, Any]) -> Path:
    relative_path = common_config["source_env_relative_path"]
    return PROJECT_ROOT / relative_path


def build_connection_config(
    common_config: dict[str, Any],
    env_vars: dict[str, str],
) -> dict[str, Any]:
    return {
        "host": env_vars.get("CUSTOMERDNA_POSTGRES_HOST", "localhost"),
        "port": int(env_vars.get("CUSTOMERDNA_POSTGRES_PORT", "5440")),
        "user": env_vars.get("CUSTOMERDNA_POSTGRES_USER", "postgres"),
        "password": env_vars.get("CUSTOMERDNA_POSTGRES_PASSWORD", ""),
        "dbname": common_config["database_name"],
    }


def ensure_dataset_directories() -> None:
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def ensure_report_directories() -> None:
    EXPERIMENT_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    BUSINESS_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)


def ensure_model_directories() -> None:
    PREPROCESSORS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_METADATA_DIR.mkdir(parents=True, exist_ok=True)


def timestamp_slug(common_config: dict[str, Any], current_time: datetime | None = None) -> str:
    current = current_time or utc_now()
    return current.strftime(common_config["snapshot_timestamp_format"])


def snapshot_artifact_paths(
    use_case_config: dict[str, Any],
    common_config: dict[str, Any],
    current_time: datetime | None = None,
) -> dict[str, Path]:
    current = current_time or utc_now()
    slug = timestamp_slug(common_config, current)

    return {
        "snapshot_path": SNAPSHOTS_DIR / f"{use_case_config['snapshot_prefix']}_{slug}.csv",
        "sample_path": SAMPLES_DIR / f"{use_case_config['sample_prefix']}_{slug}.csv",
        "manifest_path": MANIFESTS_DIR / f"{use_case_config['snapshot_prefix']}_{slug}.json",
        "timestamp_slug": Path(slug),
    }


def preprocessing_artifact_paths(
    use_case_config: dict[str, Any],
    common_config: dict[str, Any],
    current_time: datetime | None = None,
) -> dict[str, Path]:
    current = current_time or utc_now()
    slug = timestamp_slug(common_config, current)

    return {
        "processed_matrix_path": PROCESSED_DIR / f"{use_case_config['processed_prefix']}_{slug}.csv",
        "reference_labels_path": PROCESSED_DIR / f"{use_case_config['reference_prefix']}_{slug}.csv",
        "preprocessing_metadata_path": MODEL_METADATA_DIR / f"{use_case_config['metadata_prefix']}_{slug}.json",
        "selected_features_path": MODEL_METADATA_DIR / f"{use_case_config['selected_features_prefix']}_{slug}.json",
        "preprocessor_path": PREPROCESSORS_DIR / f"{use_case_config['preprocessor_prefix']}_{slug}.pkl",
    }


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def build_snapshot_manifest(
    *,
    common_config: dict[str, Any],
    use_case_config: dict[str, Any],
    row_count: int,
    sample_row_count: int,
    columns: list[str],
    artifact_paths: dict[str, Path],
    extracted_at: datetime,
) -> dict[str, Any]:
    non_feature_columns = set(use_case_config.get("non_feature_columns", []))
    reference_label_columns = use_case_config.get("reference_label_columns", [])
    binary_flag_columns = use_case_config.get("binary_flag_columns", [])
    candidate_feature_columns = [
        column_name
        for column_name in columns
        if column_name not in non_feature_columns
    ]

    return {
        "manifest_type": "training_snapshot",
        "created_at_utc": isoformat_utc(extracted_at),
        "client": {
            "client_id": common_config["client_id"],
            "client_name": common_config["client_name"],
        },
        "source": {
            "database_name": common_config["database_name"],
            "schema_name": common_config["serving_schema"],
            "table_name": use_case_config["source_table"],
            "primary_key": use_case_config["primary_key"],
            "order_by": use_case_config.get("order_by", []),
        },
        "artifacts": {
            "snapshot_path": str(artifact_paths["snapshot_path"]),
            "sample_path": str(artifact_paths["sample_path"]),
            "manifest_path": str(artifact_paths["manifest_path"]),
        },
        "table_profile": {
            "row_count": row_count,
            "sample_row_count": sample_row_count,
            "column_count": len(columns),
            "columns": columns,
        },
        "modeling_contract": {
            "use_case": use_case_config["use_case"],
            "reference_label_columns": reference_label_columns,
            "binary_flag_columns": binary_flag_columns,
            "non_feature_columns": sorted(non_feature_columns),
            "candidate_feature_columns": candidate_feature_columns,
        },
        "notes": use_case_config.get("notes", ""),
    }
