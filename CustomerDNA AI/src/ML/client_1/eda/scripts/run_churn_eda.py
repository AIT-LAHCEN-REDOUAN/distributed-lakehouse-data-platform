from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import auc, confusion_matrix, precision_recall_curve, roc_curve

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from eda_common import (  # noqa: E402
    MODEL_METADATA_DIR,
    apply_plot_style,
    ensure_use_case_directories,
    find_latest_file,
    read_json,
    save_figure,
    utc_slug,
    write_text,
)


USE_CASE = "churn"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ML EDA plots and a markdown summary for the churn model.",
    )
    parser.add_argument(
        "--training-metrics-path",
        default=None,
        help="Optional explicit churn training metrics JSON path.",
    )
    return parser.parse_args()


def find_latest_training_metrics() -> Path:
    return find_latest_file(
        MODEL_METADATA_DIR,
        "churn_classifier_training_metrics_*.json",
    )


def risk_band(probability: float) -> str:
    if probability >= 0.80:
        return "Critical"
    if probability >= 0.60:
        return "High"
    if probability >= 0.35:
        return "Medium"
    return "Low"


def plot_class_balance(positive_count: int, negative_count: int, output_path: Path) -> None:
    fig, ax = plt.subplots()
    labels = ["Non-Churn", "Churn"]
    values = [negative_count, positive_count]
    colors = ["#4C78A8", "#E45756"]
    ax.bar(labels, values, color=colors)
    ax.set_title("Churn Class Balance")
    ax.set_ylabel("Customer Count")
    for index, value in enumerate(values):
        ax.text(index, value, f"{value:,}", ha="center", va="bottom")
    save_figure(fig, output_path)


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, output_path: Path) -> dict[str, int]:
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    fig, ax = plt.subplots(figsize=(7, 6))
    image = ax.imshow(matrix, cmap="Blues")
    fig.colorbar(image, ax=ax)
    ax.set_xticks([0, 1], labels=["Pred 0", "Pred 1"])
    ax.set_yticks([0, 1], labels=["True 0", "True 1"])
    ax.set_title("Churn Confusion Matrix")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center", color="black")
    save_figure(fig, output_path)
    return {
        "tn": int(matrix[0, 0]),
        "fp": int(matrix[0, 1]),
        "fn": int(matrix[1, 0]),
        "tp": int(matrix[1, 1]),
    }


def plot_roc_curve(y_true: np.ndarray, y_score: np.ndarray, output_path: Path) -> float:
    fpr, tpr, _ = roc_curve(y_true, y_score)
    roc_auc = float(auc(fpr, tpr))
    fig, ax = plt.subplots()
    ax.plot(fpr, tpr, label=f"ROC AUC = {roc_auc:.4f}", color="#2E86AB", linewidth=2)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
    ax.set_title("Churn ROC Curve")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend(loc="lower right")
    save_figure(fig, output_path)
    return roc_auc


def plot_precision_recall_curve(y_true: np.ndarray, y_score: np.ndarray, output_path: Path) -> float:
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    pr_auc = float(auc(recall, precision))
    fig, ax = plt.subplots()
    ax.plot(recall, precision, color="#F58518", linewidth=2, label=f"PR AUC = {pr_auc:.4f}")
    ax.set_title("Churn Precision-Recall Curve")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.legend(loc="lower left")
    save_figure(fig, output_path)
    return pr_auc


def plot_probability_distribution(
    y_true: np.ndarray,
    y_score: np.ndarray,
    output_path: Path,
) -> None:
    fig, ax = plt.subplots()
    bins = np.linspace(0, 1, 21)
    ax.hist(y_score[y_true == 0], bins=bins, alpha=0.65, label="Actual Non-Churn", color="#4C78A8")
    ax.hist(y_score[y_true == 1], bins=bins, alpha=0.65, label="Actual Churn", color="#E45756")
    ax.set_title("Predicted Churn Probability Distribution")
    ax.set_xlabel("Predicted Churn Probability")
    ax.set_ylabel("Customer Count")
    ax.legend()
    save_figure(fig, output_path)


def plot_risk_band_distribution(y_score: np.ndarray, output_path: Path) -> dict[str, int]:
    band_series = pd.Series([risk_band(value) for value in y_score])
    ordered_bands = ["Critical", "High", "Medium", "Low"]
    counts = band_series.value_counts().reindex(ordered_bands, fill_value=0)
    fig, ax = plt.subplots()
    counts.plot(kind="bar", ax=ax, color=["#B22222", "#E67E22", "#F1C40F", "#2ECC71"])
    ax.set_title("Predicted Churn Risk Band Distribution")
    ax.set_xlabel("Risk Band")
    ax.set_ylabel("Customer Count")
    for index, value in enumerate(counts.tolist()):
        ax.text(index, value, f"{value:,}", ha="center", va="bottom")
    save_figure(fig, output_path)
    return {str(index): int(value) for index, value in counts.items()}


def plot_feature_importance(feature_importance_df: pd.DataFrame, output_path: Path) -> list[str]:
    top_df = feature_importance_df.sort_values("importance_rank").head(15).copy()
    top_df = top_df.sort_values("importance", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top_df["feature_name"], top_df["importance"], color="#7A5195")
    ax.set_title("Top 15 Churn Feature Importances")
    ax.set_xlabel("Importance")
    ax.set_ylabel("Feature")
    save_figure(fig, output_path)
    return top_df.sort_values("importance", ascending=False)["feature_name"].head(5).tolist()


def build_markdown_report(
    *,
    metrics_payload: dict,
    predictions_df: pd.DataFrame,
    output_paths: dict[str, Path],
    confusion_values: dict[str, int],
    roc_auc_value: float,
    pr_auc_value: float,
    risk_band_counts: dict[str, int],
    top_features: list[str],
) -> str:
    selected_metrics = metrics_payload["selected_model"]["test_metrics"]
    target_profile = metrics_payload["target_profile"]
    positive_rate = target_profile["positive_rate"]
    row_count = metrics_payload["row_count"]

    observations: list[str] = []
    if positive_rate < 0.10:
        observations.append(
            f"The churn target is clearly imbalanced, with only {positive_rate:.2%} positive churn cases."
        )
    if selected_metrics["roc_auc"] >= 0.95:
        observations.append(
            "The ROC-AUC is extremely strong, which indicates excellent separability between churn and non-churn cases."
        )
    if selected_metrics["recall"] > selected_metrics["precision"]:
        observations.append(
            "Recall is higher than precision, so the model is aggressive in catching churners at the cost of more false positives."
        )
    if not observations:
        observations.append("The churn baseline shows stable behavior without major warning signals.")

    lines = [
        "# Churn ML EDA Report",
        "",
        f"- Training metrics source: `{metrics_payload['artifacts']['metrics_path']}`",
        f"- Holdout predictions source: `{metrics_payload['artifacts']['predictions_path']}`",
        f"- Feature importance source: `{metrics_payload['artifacts']['feature_importance_path']}`",
        f"- Rows in modeled dataset: `{row_count}`",
        f"- Holdout rows: `{len(predictions_df)}`",
        "",
        "## Key Metrics",
        "",
        f"- Accuracy: `{selected_metrics['accuracy']:.6f}`",
        f"- Precision: `{selected_metrics['precision']:.6f}`",
        f"- Recall: `{selected_metrics['recall']:.6f}`",
        f"- F1 score: `{selected_metrics['f1_score']:.6f}`",
        f"- ROC-AUC: `{roc_auc_value:.6f}`",
        f"- PR-AUC: `{pr_auc_value:.6f}`",
        f"- Positive churn rate: `{positive_rate:.2%}`",
        "",
        "## Confusion Matrix",
        "",
        f"- True negative: `{confusion_values['tn']}`",
        f"- False positive: `{confusion_values['fp']}`",
        f"- False negative: `{confusion_values['fn']}`",
        f"- True positive: `{confusion_values['tp']}`",
        "",
        "## Risk Band Counts",
        "",
        f"- Critical: `{risk_band_counts.get('Critical', 0)}`",
        f"- High: `{risk_band_counts.get('High', 0)}`",
        f"- Medium: `{risk_band_counts.get('Medium', 0)}`",
        f"- Low: `{risk_band_counts.get('Low', 0)}`",
        "",
        "## Top Features",
        "",
    ]
    lines.extend([f"- `{feature_name}`" for feature_name in top_features])
    lines.extend(
        [
            "",
            "## Main Findings",
            "",
        ]
    )
    lines.extend([f"- {observation}" for observation in observations])
    lines.extend(
        [
            "",
            "## Generated Plots",
            "",
        ]
    )
    lines.extend([f"- `{path}`" for path in output_paths.values()])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    apply_plot_style()
    directories = ensure_use_case_directories(USE_CASE)
    slug = utc_slug()

    metrics_path = Path(args.training_metrics_path) if args.training_metrics_path else find_latest_training_metrics()
    metrics_payload = read_json(metrics_path)

    predictions_path = Path(metrics_payload["artifacts"]["predictions_path"])
    feature_importance_path = Path(metrics_payload["artifacts"]["feature_importance_path"])

    if not predictions_path.exists():
        raise FileNotFoundError(f"Holdout predictions file not found: {predictions_path}")
    if not feature_importance_path.exists():
        raise FileNotFoundError(f"Feature importance file not found: {feature_importance_path}")

    predictions_df = pd.read_csv(predictions_path, low_memory=False)
    feature_importance_df = pd.read_csv(feature_importance_path, low_memory=False)

    required_prediction_columns = {
        "actual_churn_flag",
        "predicted_churn_probability",
        "predicted_churn_flag",
    }
    missing_prediction_columns = required_prediction_columns.difference(predictions_df.columns)
    if missing_prediction_columns:
        raise ValueError(
            "Missing expected churn prediction columns: " + ", ".join(sorted(missing_prediction_columns))
        )

    y_true = predictions_df["actual_churn_flag"].to_numpy(dtype=int)
    y_pred = predictions_df["predicted_churn_flag"].to_numpy(dtype=int)
    y_score = predictions_df["predicted_churn_probability"].to_numpy(dtype=float)

    output_paths = {
        "class_balance": directories["plot_dir"] / f"churn_class_balance_{slug}.png",
        "confusion_matrix": directories["plot_dir"] / f"churn_confusion_matrix_{slug}.png",
        "roc_curve": directories["plot_dir"] / f"churn_roc_curve_{slug}.png",
        "precision_recall_curve": directories["plot_dir"] / f"churn_precision_recall_curve_{slug}.png",
        "probability_distribution": directories["plot_dir"] / f"churn_probability_distribution_{slug}.png",
        "risk_band_distribution": directories["plot_dir"] / f"churn_risk_band_distribution_{slug}.png",
        "feature_importance": directories["plot_dir"] / f"churn_feature_importance_top15_{slug}.png",
    }

    target_profile = metrics_payload["target_profile"]
    plot_class_balance(
        positive_count=int(target_profile["positive_count"]),
        negative_count=int(target_profile["negative_count"]),
        output_path=output_paths["class_balance"],
    )
    confusion_values = plot_confusion_matrix(y_true, y_pred, output_paths["confusion_matrix"])
    roc_auc_value = plot_roc_curve(y_true, y_score, output_paths["roc_curve"])
    pr_auc_value = plot_precision_recall_curve(y_true, y_score, output_paths["precision_recall_curve"])
    plot_probability_distribution(y_true, y_score, output_paths["probability_distribution"])
    risk_band_counts = plot_risk_band_distribution(y_score, output_paths["risk_band_distribution"])
    top_features = plot_feature_importance(feature_importance_df, output_paths["feature_importance"])

    report_text = build_markdown_report(
        metrics_payload=metrics_payload,
        predictions_df=predictions_df,
        output_paths=output_paths,
        confusion_values=confusion_values,
        roc_auc_value=roc_auc_value,
        pr_auc_value=pr_auc_value,
        risk_band_counts=risk_band_counts,
        top_features=top_features,
    )
    report_path = directories["report_dir"] / f"churn_ml_eda_report_{slug}.md"
    write_text(report_path, report_text)

    print("=" * 80)
    print("CUSTOMERDNA AI - CHURN ML EDA")
    print("=" * 80)
    print(f"Training metrics: {metrics_path}")
    print(f"Holdout predictions: {predictions_path}")
    print(f"Feature importance: {feature_importance_path}")
    print(f"Report: {report_path}")
    for label, path in output_paths.items():
        print(f"{label}: {path}")
    print("Churn ML EDA completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
