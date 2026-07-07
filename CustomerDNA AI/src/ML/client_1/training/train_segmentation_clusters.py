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
        "pandas and numpy are required for segmentation training. Install them in your local environment first."
    ) from exc

try:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "scikit-learn is required for segmentation training. Install it in your local environment first."
    ) from exc


CURRENT_DIR = Path(__file__).resolve().parent
CLIENT_ML_ROOT = CURRENT_DIR.parent
DATA_ACCESS_DIR = CLIENT_ML_ROOT / "data_access"
if str(DATA_ACCESS_DIR) not in sys.path:
    sys.path.append(str(DATA_ACCESS_DIR))

from schema_manifest import (  # noqa: E402
    BUSINESS_SUMMARIES_DIR,
    MODEL_METADATA_DIR,
    PREPROCESSORS_DIR,
    isoformat_utc,
    load_common_config,
    load_use_case_config,
    read_json,
    timestamp_slug,
)


SAVED_MODELS_DIR = CLIENT_ML_ROOT / "models" / "saved_models"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a baseline customer segmentation clustering model from the latest processed feature matrix.",
    )
    parser.add_argument(
        "--use-case",
        default="segmentation",
        help="Use-case config name stored under src/ML/client_1/configs without the .json suffix.",
    )
    parser.add_argument(
        "--preprocessing-metadata-path",
        default=None,
        help="Optional explicit preprocessing metadata JSON path.",
    )
    parser.add_argument(
        "--k-min",
        type=int,
        default=2,
        help="Minimum number of clusters to test.",
    )
    parser.add_argument(
        "--k-max",
        type=int,
        default=10,
        help="Maximum number of clusters to test.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for K-Means reproducibility.",
    )
    parser.add_argument(
        "--n-init",
        type=int,
        default=20,
        help="Number of K-Means initializations.",
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


def find_latest_preprocessing_metadata(use_case_config: dict[str, Any]) -> Path:
    return find_latest_file(
        MODEL_METADATA_DIR,
        f"{use_case_config['metadata_prefix']}_*.json",
    )


def dominant_value_summary(series: pd.Series) -> dict[str, Any]:
    counts = series.fillna("Unknown").astype(str).value_counts(dropna=False)
    if counts.empty:
        return {"value": "Unknown", "count": 0, "share": 0.0}

    dominant_value = counts.index[0]
    dominant_count = int(counts.iloc[0])
    dominant_share = float(dominant_count / len(series)) if len(series) else 0.0
    return {
        "value": str(dominant_value),
        "count": dominant_count,
        "share": round(dominant_share, 6),
    }


def build_markdown_report(training_payload: dict[str, Any]) -> str:
    selected_model = training_payload["selected_model"]
    candidate_results = training_payload["candidate_results"]

    lines = [
        "# Segmentation Clustering Training Report",
        "",
        f"- Created at: `{training_payload['created_at_utc']}`",
        f"- Use case: `{training_payload['use_case']}`",
        f"- Processed matrix path: `{training_payload['processed_matrix_path']}`",
        f"- Row count: `{training_payload['row_count']}`",
        f"- Feature count: `{training_payload['feature_count']}`",
        "",
        "## Selected Model",
        "",
        f"- Best cluster count: `{selected_model['best_k']}`",
        f"- Silhouette score: `{selected_model['silhouette_score']:.6f}`",
        f"- Inertia: `{selected_model['inertia']:.6f}`",
        f"- Random state: `{selected_model['random_state']}`",
        f"- n_init: `{selected_model['n_init']}`",
        "",
        "## Candidate Results",
        "",
        "| k | Silhouette | Inertia | Cluster Sizes |",
        "|---|---:|---:|---|",
    ]

    for item in candidate_results:
        cluster_sizes = ", ".join(str(size) for size in item["cluster_sizes"])
        lines.append(
            f"| {item['k']} | {item['silhouette_score']:.6f} | {item['inertia']:.6f} | {cluster_sizes} |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    common_config = load_common_config()
    use_case_config = load_use_case_config(args.use_case)
    metadata_path = (
        Path(args.preprocessing_metadata_path)
        if args.preprocessing_metadata_path
        else find_latest_preprocessing_metadata(use_case_config)
    )

    preprocessing_metadata = read_json(metadata_path)
    processed_matrix_path = Path(preprocessing_metadata["processed_matrix_path"])
    reference_labels_path = Path(preprocessing_metadata["reference_labels_path"])
    selected_features_path = Path(preprocessing_metadata["selected_features_path"])
    preprocessor_path = Path(preprocessing_metadata["preprocessor_path"])

    if not processed_matrix_path.exists():
        raise FileNotFoundError(f"Processed matrix not found: {processed_matrix_path}")
    if not reference_labels_path.exists():
        raise FileNotFoundError(f"Reference labels file not found: {reference_labels_path}")
    if not selected_features_path.exists():
        raise FileNotFoundError(f"Selected features metadata not found: {selected_features_path}")
    if not preprocessor_path.exists():
        raise FileNotFoundError(f"Serialized preprocessor not found: {preprocessor_path}")

    selected_features = read_json(selected_features_path)
    reference_label_columns = selected_features["reference_label_columns"]

    processed_df = pd.read_csv(processed_matrix_path, low_memory=False)
    reference_df = pd.read_csv(reference_labels_path, low_memory=False)

    if "customer_id" not in processed_df.columns:
        raise ValueError("Processed matrix must contain customer_id as the first column.")

    feature_matrix_df = processed_df.drop(columns=["customer_id"])
    feature_matrix = feature_matrix_df.to_numpy(dtype=float)

    if feature_matrix.shape[0] < 3:
        raise ValueError("At least 3 rows are required for clustering.")

    if args.k_min < 2:
        raise ValueError("--k-min must be at least 2.")
    if args.k_max < args.k_min:
        raise ValueError("--k-max must be greater than or equal to --k-min.")

    effective_k_max = min(args.k_max, feature_matrix.shape[0] - 1)
    if effective_k_max < args.k_min:
        raise ValueError("Not enough rows to evaluate the requested cluster range.")

    candidate_results: list[dict[str, Any]] = []
    best_result: dict[str, Any] | None = None
    best_model: KMeans | None = None
    best_labels: np.ndarray | None = None

    for k_value in range(args.k_min, effective_k_max + 1):
        model = KMeans(
            n_clusters=k_value,
            random_state=args.random_state,
            n_init=args.n_init,
        )
        labels = model.fit_predict(feature_matrix)
        silhouette = float(silhouette_score(feature_matrix, labels))
        inertia = float(model.inertia_)
        cluster_sizes = np.bincount(labels, minlength=k_value).tolist()

        result = {
            "k": int(k_value),
            "silhouette_score": silhouette,
            "inertia": inertia,
            "cluster_sizes": [int(size) for size in cluster_sizes],
        }
        candidate_results.append(result)

        if best_result is None:
            best_result = result
            best_model = model
            best_labels = labels
            continue

        is_better = silhouette > best_result["silhouette_score"]
        same_silhouette = abs(silhouette - best_result["silhouette_score"]) < 1e-12
        lower_inertia = inertia < best_result["inertia"]
        smaller_k = k_value < best_result["k"]

        if is_better or (same_silhouette and (lower_inertia or (inertia == best_result["inertia"] and smaller_k))):
            best_result = result
            best_model = model
            best_labels = labels

    if best_result is None or best_model is None or best_labels is None:
        raise RuntimeError("No valid clustering candidate was produced.")

    created_at = datetime.now(timezone.utc)
    slug = timestamp_slug(common_config, created_at)

    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    BUSINESS_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

    model_path = SAVED_MODELS_DIR / f"segmentation_kmeans_model_{slug}.pkl"
    metrics_path = MODEL_METADATA_DIR / f"segmentation_kmeans_training_metrics_{slug}.json"
    assignments_path = BUSINESS_SUMMARIES_DIR / f"segmentation_cluster_assignments_{slug}.csv"
    summary_path = BUSINESS_SUMMARIES_DIR / f"segmentation_cluster_summary_{slug}.csv"
    report_path = BUSINESS_SUMMARIES_DIR / f"segmentation_training_report_{slug}.md"

    with model_path.open("wb") as handle:
        pickle.dump(best_model, handle)

    assignments_df = pd.DataFrame(
        {
            "customer_id": processed_df["customer_id"].values,
            "cluster_id": best_labels.astype(int),
            "distance_to_assigned_centroid": np.min(best_model.transform(feature_matrix), axis=1),
        }
    )
    assignments_df = assignments_df.merge(reference_df, on="customer_id", how="left")
    assignments_df.to_csv(assignments_path, index=False)

    summary_rows: list[dict[str, Any]] = []
    for cluster_id in sorted(assignments_df["cluster_id"].unique().tolist()):
        cluster_slice = assignments_df[assignments_df["cluster_id"] == cluster_id].copy()
        summary_row: dict[str, Any] = {
            "cluster_id": int(cluster_id),
            "customer_count": int(len(cluster_slice)),
            "customer_share": round(float(len(cluster_slice) / len(assignments_df)), 6),
            "avg_distance_to_centroid": round(float(cluster_slice["distance_to_assigned_centroid"].mean()), 6),
        }

        for column_name in reference_label_columns:
            dominant_summary = dominant_value_summary(cluster_slice[column_name])
            summary_row[f"{column_name}_dominant_value"] = dominant_summary["value"]
            summary_row[f"{column_name}_dominant_share"] = dominant_summary["share"]

        summary_rows.append(summary_row)

    summary_df = pd.DataFrame(summary_rows).sort_values("cluster_id")
    summary_df.to_csv(summary_path, index=False)

    training_payload = {
        "artifact_type": "segmentation_kmeans_training",
        "created_at_utc": isoformat_utc(created_at),
        "use_case": use_case_config["use_case"],
        "preprocessing_metadata_path": str(metadata_path),
        "processed_matrix_path": str(processed_matrix_path),
        "reference_labels_path": str(reference_labels_path),
        "selected_features_path": str(selected_features_path),
        "preprocessor_path": str(preprocessor_path),
        "row_count": int(feature_matrix.shape[0]),
        "feature_count": int(feature_matrix.shape[1]),
        "candidate_results": candidate_results,
        "selected_model": {
            "best_k": int(best_result["k"]),
            "silhouette_score": float(best_result["silhouette_score"]),
            "inertia": float(best_result["inertia"]),
            "cluster_sizes": best_result["cluster_sizes"],
            "random_state": int(args.random_state),
            "n_init": int(args.n_init),
        },
        "artifacts": {
            "model_path": str(model_path),
            "metrics_path": str(metrics_path),
            "assignments_path": str(assignments_path),
            "summary_path": str(summary_path),
            "report_path": str(report_path),
        },
    }

    metrics_path.write_text(json.dumps(training_payload, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_markdown_report(training_payload), encoding="utf-8")

    print("=" * 80)
    print("CUSTOMERDNA AI - SEGMENTATION CLUSTER TRAINING")
    print("=" * 80)
    print(f"Use case: {use_case_config['use_case']}")
    print(f"Preprocessing metadata: {metadata_path}")
    print(f"Processed matrix: {processed_matrix_path}")
    print(f"Reference labels: {reference_labels_path}")
    print(f"Rows used: {feature_matrix.shape[0]}")
    print(f"Encoded features used: {feature_matrix.shape[1]}")
    print(f"Cluster range tested: {args.k_min} to {effective_k_max}")
    print(f"Best k: {best_result['k']}")
    print(f"Best silhouette score: {best_result['silhouette_score']:.6f}")
    print(f"Best inertia: {best_result['inertia']:.6f}")
    print(f"Saved model: {model_path}")
    print(f"Metrics JSON: {metrics_path}")
    print(f"Cluster assignments: {assignments_path}")
    print(f"Cluster summary: {summary_path}")
    print(f"Training report: {report_path}")
    print("Segmentation clustering training completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
