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
        "pandas and numpy are required for persona training. Install them in your local environment first."
    ) from exc

try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (
        accuracy_score,
        balanced_accuracy_score,
        classification_report,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
    )
    from sklearn.model_selection import train_test_split
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "scikit-learn is required for persona training. Install it in your local environment first."
    ) from exc


CURRENT_DIR = Path(__file__).resolve().parent
CLIENT_ML_ROOT = CURRENT_DIR.parent
DATA_ACCESS_DIR = CLIENT_ML_ROOT / "data_access"
if str(DATA_ACCESS_DIR) not in sys.path:
    sys.path.append(str(DATA_ACCESS_DIR))

from schema_manifest import (  # noqa: E402
    BUSINESS_SUMMARIES_DIR,
    MODEL_METADATA_DIR,
    isoformat_utc,
    load_common_config,
    load_use_case_config,
    read_json,
    timestamp_slug,
)


SAVED_MODELS_DIR = CLIENT_ML_ROOT / "models" / "saved_models"
DEFAULT_TEST_SIZE = 0.2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a baseline persona classification model from the latest processed feature matrix.",
    )
    parser.add_argument(
        "--use-case",
        default="persona",
        help="Use-case config name stored under src/ML/client_1/configs without the .json suffix.",
    )
    parser.add_argument(
        "--preprocessing-metadata-path",
        default=None,
        help="Optional explicit preprocessing metadata JSON path.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=DEFAULT_TEST_SIZE,
        help="Fraction of rows reserved for the holdout test split.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
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


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: list[str],
) -> dict[str, Any]:
    matrix = confusion_matrix(y_true, y_pred, labels=class_names)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "precision_weighted": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "recall_weighted": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "confusion_matrix_labels": class_names,
        "confusion_matrix": matrix.tolist(),
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=class_names,
            output_dict=True,
            zero_division=0,
        ),
    }


def build_candidate_models(random_state: int) -> dict[str, Any]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=3000,
            class_weight="balanced",
            solver="lbfgs",
            random_state=random_state,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=400,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            random_state=random_state,
            n_estimators=300,
            learning_rate=0.05,
            max_depth=3,
        ),
    }


def extract_feature_importance(
    model_name: str,
    model: Any,
    feature_names: list[str],
) -> pd.DataFrame:
    if model_name == "logistic_regression":
        importance = np.mean(np.abs(model.coef_), axis=0)
    else:
        importance = model.feature_importances_

    importance_df = pd.DataFrame(
        {
            "feature_name": feature_names,
            "importance": importance,
        }
    ).sort_values("importance", ascending=False)

    importance_df["importance_rank"] = np.arange(1, len(importance_df) + 1)
    return importance_df


def build_markdown_report(training_payload: dict[str, Any]) -> str:
    selected_model = training_payload["selected_model"]
    selected_metrics = selected_model["test_metrics"]
    candidate_results = training_payload["candidate_results"]

    lines = [
        "# Persona Classification Training Report",
        "",
        f"- Created at: `{training_payload['created_at_utc']}`",
        f"- Use case: `{training_payload['use_case']}`",
        f"- Processed matrix path: `{training_payload['processed_matrix_path']}`",
        f"- Row count: `{training_payload['row_count']}`",
        f"- Feature count: `{training_payload['feature_count']}`",
        f"- Persona class count: `{training_payload['target_profile']['class_count']}`",
        "",
        "## Selected Model",
        "",
        f"- Model name: `{selected_model['model_name']}`",
        f"- Train rows: `{selected_model['train_row_count']}`",
        f"- Test rows: `{selected_model['test_row_count']}`",
        f"- Accuracy: `{selected_metrics['accuracy']:.6f}`",
        f"- Balanced accuracy: `{selected_metrics['balanced_accuracy']:.6f}`",
        f"- Macro precision: `{selected_metrics['precision_macro']:.6f}`",
        f"- Macro recall: `{selected_metrics['recall_macro']:.6f}`",
        f"- Macro F1: `{selected_metrics['f1_macro']:.6f}`",
        f"- Weighted F1: `{selected_metrics['f1_weighted']:.6f}`",
        "",
        "## Candidate Results",
        "",
        "| Model | Accuracy | Balanced Acc. | Macro F1 | Weighted F1 |",
        "|---|---:|---:|---:|---:|",
    ]

    for item in candidate_results:
        metrics = item["test_metrics"]
        lines.append(
            f"| {item['model_name']} | "
            f"{metrics['accuracy']:.6f} | "
            f"{metrics['balanced_accuracy']:.6f} | "
            f"{metrics['f1_macro']:.6f} | "
            f"{metrics['f1_weighted']:.6f} |"
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
    labels_path = Path(preprocessing_metadata["reference_labels_path"])
    selected_features_path = Path(preprocessing_metadata["selected_features_path"])
    preprocessor_path = Path(preprocessing_metadata["preprocessor_path"])
    target_column = preprocessing_metadata["target_column"]

    if not processed_matrix_path.exists():
        raise FileNotFoundError(f"Processed matrix not found: {processed_matrix_path}")
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")
    if not selected_features_path.exists():
        raise FileNotFoundError(f"Selected features metadata not found: {selected_features_path}")
    if not preprocessor_path.exists():
        raise FileNotFoundError(f"Serialized preprocessor not found: {preprocessor_path}")

    selected_features = read_json(selected_features_path)
    reference_label_columns = selected_features["reference_label_columns"]

    processed_df = pd.read_csv(processed_matrix_path, low_memory=False)
    labels_df = pd.read_csv(labels_path, low_memory=False)

    if "customer_id" not in processed_df.columns:
        raise ValueError("Processed matrix must contain customer_id as the first column.")
    if target_column not in labels_df.columns:
        raise ValueError(f"Labels file must contain target column '{target_column}'.")

    modeling_df = processed_df.merge(labels_df, on="customer_id", how="inner")
    if len(modeling_df) != len(processed_df):
        raise ValueError("Processed matrix and labels file could not be aligned 1:1 on customer_id.")

    feature_matrix_df = processed_df.drop(columns=["customer_id"])
    feature_names = feature_matrix_df.columns.tolist()
    feature_matrix = feature_matrix_df.to_numpy(dtype=float)
    target_vector = modeling_df[target_column].astype("string").fillna("Unknown").astype(str).to_numpy()
    class_names = sorted(pd.Series(target_vector).unique().tolist())

    if len(class_names) < 2:
        raise ValueError("Persona target must contain at least two distinct classes.")

    if not 0 < args.test_size < 0.5:
        raise ValueError("--test-size must be greater than 0 and less than 0.5.")

    (
        X_train,
        X_test,
        y_train,
        y_test,
        id_train,
        id_test,
    ) = train_test_split(
        feature_matrix,
        target_vector,
        processed_df["customer_id"].to_numpy(),
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=target_vector,
    )

    candidate_results: list[dict[str, Any]] = []
    best_result: dict[str, Any] | None = None
    best_model_name: str | None = None
    best_model: Any | None = None
    best_predictions: np.ndarray | None = None

    for model_name, model in build_candidate_models(args.random_state).items():
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        metrics = evaluate_predictions(y_test, predictions, class_names)

        result = {
            "model_name": model_name,
            "train_row_count": int(len(X_train)),
            "test_row_count": int(len(X_test)),
            "test_metrics": metrics,
        }
        candidate_results.append(result)

        if best_result is None:
            best_result = result
            best_model_name = model_name
            best_model = model
            best_predictions = predictions
            continue

        current_metrics = metrics
        best_metrics = best_result["test_metrics"]
        better_macro_f1 = current_metrics["f1_macro"] > best_metrics["f1_macro"]
        same_macro_f1 = abs(current_metrics["f1_macro"] - best_metrics["f1_macro"]) < 1e-12
        better_balanced_accuracy = current_metrics["balanced_accuracy"] > best_metrics["balanced_accuracy"]

        if better_macro_f1 or (same_macro_f1 and better_balanced_accuracy):
            best_result = result
            best_model_name = model_name
            best_model = model
            best_predictions = predictions

    if best_result is None or best_model_name is None or best_model is None:
        raise RuntimeError("No valid persona model candidate was produced.")
    if best_predictions is None:
        raise RuntimeError("Best-model predictions were not captured.")

    created_at = datetime.now(timezone.utc)
    slug = timestamp_slug(common_config, created_at)

    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    BUSINESS_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

    model_path = SAVED_MODELS_DIR / f"persona_classifier_model_{slug}.pkl"
    metrics_path = MODEL_METADATA_DIR / f"persona_classifier_training_metrics_{slug}.json"
    predictions_path = BUSINESS_SUMMARIES_DIR / f"persona_holdout_predictions_{slug}.csv"
    importance_path = BUSINESS_SUMMARIES_DIR / f"persona_feature_importance_{slug}.csv"
    report_path = BUSINESS_SUMMARIES_DIR / f"persona_training_report_{slug}.md"

    with model_path.open("wb") as handle:
        pickle.dump(best_model, handle)

    holdout_predictions_df = pd.DataFrame(
        {
            "customer_id": id_test,
            "actual_persona_name": y_test,
            "predicted_persona_name": best_predictions,
            "prediction_correct_flag": (y_test == best_predictions).astype(int),
        }
    )

    holdout_reference_columns = ["customer_id"] + [
        column_name
        for column_name in reference_label_columns
        if column_name in labels_df.columns
    ]
    holdout_predictions_df = holdout_predictions_df.merge(
        labels_df[holdout_reference_columns],
        on="customer_id",
        how="left",
    )
    holdout_predictions_df.to_csv(predictions_path, index=False)

    importance_df = extract_feature_importance(best_model_name, best_model, feature_names)
    importance_df.to_csv(importance_path, index=False)

    training_payload = {
        "artifact_type": "persona_classifier_training",
        "created_at_utc": isoformat_utc(created_at),
        "use_case": use_case_config["use_case"],
        "preprocessing_metadata_path": str(metadata_path),
        "processed_matrix_path": str(processed_matrix_path),
        "reference_labels_path": str(labels_path),
        "selected_features_path": str(selected_features_path),
        "preprocessor_path": str(preprocessor_path),
        "row_count": int(feature_matrix.shape[0]),
        "feature_count": int(feature_matrix.shape[1]),
        "target_profile": {
            "target_column": target_column,
            "class_count": int(len(class_names)),
            "class_names": class_names,
            "class_distribution": {
                str(key): int(value)
                for key, value in pd.Series(target_vector).value_counts(dropna=False).to_dict().items()
            },
        },
        "candidate_results": candidate_results,
        "selected_model": {
            "model_name": best_model_name,
            "train_row_count": int(len(X_train)),
            "test_row_count": int(len(X_test)),
            "test_metrics": best_result["test_metrics"],
        },
        "artifacts": {
            "model_path": str(model_path),
            "metrics_path": str(metrics_path),
            "predictions_path": str(predictions_path),
            "feature_importance_path": str(importance_path),
            "report_path": str(report_path),
        },
    }

    metrics_path.write_text(json.dumps(training_payload, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_markdown_report(training_payload), encoding="utf-8")

    print("=" * 80)
    print("CUSTOMERDNA AI - PERSONA CLASSIFIER TRAINING")
    print("=" * 80)
    print(f"Use case: {use_case_config['use_case']}")
    print(f"Preprocessing metadata: {metadata_path}")
    print(f"Processed matrix: {processed_matrix_path}")
    print(f"Reference labels: {labels_path}")
    print(f"Rows used: {feature_matrix.shape[0]}")
    print(f"Encoded features used: {feature_matrix.shape[1]}")
    print(f"Selected model: {best_model_name}")
    print(f"Accuracy: {best_result['test_metrics']['accuracy']:.6f}")
    print(f"Balanced accuracy: {best_result['test_metrics']['balanced_accuracy']:.6f}")
    print(f"Macro precision: {best_result['test_metrics']['precision_macro']:.6f}")
    print(f"Macro recall: {best_result['test_metrics']['recall_macro']:.6f}")
    print(f"Macro F1: {best_result['test_metrics']['f1_macro']:.6f}")
    print(f"Weighted F1: {best_result['test_metrics']['f1_weighted']:.6f}")
    print(f"Saved model: {model_path}")
    print(f"Metrics JSON: {metrics_path}")
    print(f"Holdout predictions: {predictions_path}")
    print(f"Feature importance: {importance_path}")
    print(f"Training report: {report_path}")
    print("Persona classification training completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
