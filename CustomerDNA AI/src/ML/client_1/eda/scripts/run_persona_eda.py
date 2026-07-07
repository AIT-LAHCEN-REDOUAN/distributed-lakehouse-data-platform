from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import confusion_matrix

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


USE_CASE = "persona"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ML EDA plots and a markdown summary for the persona model.",
    )
    parser.add_argument(
        "--training-metrics-path",
        default=None,
        help="Optional explicit persona training metrics JSON path.",
    )
    return parser.parse_args()


def find_latest_training_metrics() -> Path:
    return find_latest_file(
        MODEL_METADATA_DIR,
        "persona_classifier_training_metrics_*.json",
    )


def plot_class_distribution(class_distribution: dict[str, int], output_path: Path) -> None:
    series = pd.Series(class_distribution).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(11, 6))
    series.plot(kind="bar", ax=ax, color="#4C78A8")
    ax.set_title("Persona Class Distribution")
    ax.set_xlabel("Persona Class")
    ax.set_ylabel("Customer Count")
    ax.tick_params(axis="x", rotation=30)
    for index, value in enumerate(series.tolist()):
        ax.text(index, value, f"{value:,}", ha="center", va="bottom", fontsize=9)
    save_figure(fig, output_path)


def plot_confusion_matrix(
    y_true: list[str],
    y_pred: list[str],
    class_names: list[str],
    output_path: Path,
) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=class_names)
    fig, ax = plt.subplots(figsize=(10, 8))
    image = ax.imshow(matrix, cmap="Blues")
    fig.colorbar(image, ax=ax)
    ax.set_xticks(range(len(class_names)), labels=class_names)
    ax.set_yticks(range(len(class_names)), labels=class_names)
    ax.set_title("Persona Confusion Matrix")
    ax.set_xlabel("Predicted Persona")
    ax.set_ylabel("Actual Persona")
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center", color="black", fontsize=8)
    save_figure(fig, output_path)


def plot_per_class_metrics(classification_report: dict, output_path: Path) -> list[str]:
    rows = []
    for class_name, payload in classification_report.items():
        if class_name in {"accuracy", "macro avg", "weighted avg"}:
            continue
        if not isinstance(payload, dict):
            continue
        rows.append(
            {
                "class_name": class_name,
                "precision": float(payload["precision"]),
                "recall": float(payload["recall"]),
                "f1_score": float(payload["f1-score"]),
            }
        )

    metrics_df = pd.DataFrame(rows).sort_values("f1_score", ascending=False)
    fig, ax = plt.subplots(figsize=(12, 7))
    x = range(len(metrics_df))
    width = 0.25
    ax.bar([i - width for i in x], metrics_df["precision"], width=width, label="Precision", color="#4C78A8")
    ax.bar(x, metrics_df["recall"], width=width, label="Recall", color="#F58518")
    ax.bar([i + width for i in x], metrics_df["f1_score"], width=width, label="F1", color="#54A24B")
    ax.set_xticks(list(x), metrics_df["class_name"], rotation=30, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_title("Per-Class Persona Metrics")
    ax.set_ylabel("Score")
    ax.legend()
    save_figure(fig, output_path)
    return metrics_df.head(3)["class_name"].tolist()


def plot_prediction_distribution(predictions_df: pd.DataFrame, output_path: Path) -> dict[str, int]:
    counts = (
        predictions_df["predicted_persona_name"]
        .astype(str)
        .value_counts()
        .sort_values(ascending=False)
    )
    fig, ax = plt.subplots(figsize=(11, 6))
    counts.plot(kind="bar", ax=ax, color="#F58518")
    ax.set_title("Predicted Persona Distribution")
    ax.set_xlabel("Predicted Persona")
    ax.set_ylabel("Customer Count")
    ax.tick_params(axis="x", rotation=30)
    for index, value in enumerate(counts.tolist()):
        ax.text(index, value, f"{value:,}", ha="center", va="bottom", fontsize=9)
    save_figure(fig, output_path)
    return {str(index): int(value) for index, value in counts.items()}


def plot_group_precision(predictions_df: pd.DataFrame, output_path: Path) -> dict[str, float]:
    summary_df = (
        predictions_df.groupby("predicted_persona_name", dropna=False)["prediction_correct_flag"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.bar(summary_df["predicted_persona_name"], summary_df["prediction_correct_flag"], color="#E45756")
    ax.set_title("Precision Within Predicted Persona Groups")
    ax.set_xlabel("Predicted Persona")
    ax.set_ylabel("Precision")
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="x", rotation=30)
    for index, value in enumerate(summary_df["prediction_correct_flag"].tolist()):
        ax.text(index, value, f"{value:.2f}", ha="center", va="bottom", fontsize=9)
    save_figure(fig, output_path)
    return {
        str(row["predicted_persona_name"]): float(row["prediction_correct_flag"])
        for _, row in summary_df.iterrows()
    }


def plot_feature_importance(feature_importance_df: pd.DataFrame, output_path: Path) -> list[str]:
    top_df = feature_importance_df.sort_values("importance_rank").head(15).copy()
    top_df = top_df.sort_values("importance", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top_df["feature_name"], top_df["importance"], color="#7A5195")
    ax.set_title("Top Persona Feature Importances")
    ax.set_xlabel("Importance")
    ax.set_ylabel("Feature")
    save_figure(fig, output_path)
    return top_df.sort_values("importance", ascending=False)["feature_name"].head(5).tolist()


def build_markdown_report(
    *,
    metrics_payload: dict,
    predictions_df: pd.DataFrame,
    output_paths: dict[str, Path],
    predicted_counts: dict[str, int],
    group_precision: dict[str, float],
    top_features: list[str],
    top_f1_classes: list[str],
) -> str:
    selected_metrics = metrics_payload["selected_model"]["test_metrics"]
    target_profile = metrics_payload["target_profile"]

    observations: list[str] = []
    if selected_metrics["accuracy"] > selected_metrics["balanced_accuracy"]:
        observations.append(
            "Accuracy is much higher than balanced accuracy, which means class imbalance is inflating the global score."
        )
    if selected_metrics["f1_macro"] < selected_metrics["f1_weighted"]:
        observations.append(
            "Weighted F1 is much stronger than macro F1, so the model performs better on frequent personas than on rare ones."
        )
    if group_precision:
        best_group = max(group_precision, key=group_precision.get)
        weakest_group = min(group_precision, key=group_precision.get)
        observations.append(
            f"The strongest predicted persona group is '{best_group}' with precision {group_precision[best_group]:.2%}, while the weakest is '{weakest_group}' with precision {group_precision[weakest_group]:.2%}."
        )
    if not observations:
        observations.append("The persona baseline shows stable behavior without major warning signals.")

    lines = [
        "# Persona ML EDA Report",
        "",
        f"- Training metrics source: `{metrics_payload['artifacts']['metrics_path']}`",
        f"- Holdout predictions source: `{metrics_payload['artifacts']['predictions_path']}`",
        f"- Feature importance source: `{metrics_payload['artifacts']['feature_importance_path']}`",
        f"- Rows in modeled dataset: `{metrics_payload['row_count']}`",
        f"- Holdout rows: `{len(predictions_df)}`",
        "",
        "## Key Metrics",
        "",
        f"- Accuracy: `{selected_metrics['accuracy']:.6f}`",
        f"- Balanced accuracy: `{selected_metrics['balanced_accuracy']:.6f}`",
        f"- Macro precision: `{selected_metrics['precision_macro']:.6f}`",
        f"- Macro recall: `{selected_metrics['recall_macro']:.6f}`",
        f"- Macro F1: `{selected_metrics['f1_macro']:.6f}`",
        f"- Weighted F1: `{selected_metrics['f1_weighted']:.6f}`",
        "",
        "## Class Profile",
        "",
        f"- Persona class count: `{target_profile['class_count']}`",
        "",
        "### Training Class Distribution",
        "",
    ]
    lines.extend(
        [f"- `{class_name}`: `{count}`" for class_name, count in target_profile["class_distribution"].items()]
    )
    lines.extend(
        [
            "",
            "### Holdout Predicted Distribution",
            "",
        ]
    )
    lines.extend([f"- `{class_name}`: `{count}`" for class_name, count in predicted_counts.items()])
    lines.extend(
        [
            "",
            "## Best Per-Class F1 Labels",
            "",
        ]
    )
    lines.extend([f"- `{class_name}`" for class_name in top_f1_classes])
    lines.extend(
        [
            "",
            "## Top Features",
            "",
        ]
    )
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
        "actual_persona_name",
        "predicted_persona_name",
        "prediction_correct_flag",
    }
    missing_prediction_columns = required_prediction_columns.difference(predictions_df.columns)
    if missing_prediction_columns:
        raise ValueError(
            "Missing expected persona prediction columns: " + ", ".join(sorted(missing_prediction_columns))
        )

    class_names = metrics_payload["target_profile"]["class_names"]
    classification_report = metrics_payload["selected_model"]["test_metrics"]["classification_report"]

    output_paths = {
        "class_distribution": directories["plot_dir"] / f"persona_class_distribution_{slug}.png",
        "confusion_matrix": directories["plot_dir"] / f"persona_confusion_matrix_{slug}.png",
        "per_class_metrics": directories["plot_dir"] / f"persona_per_class_metrics_{slug}.png",
        "prediction_distribution": directories["plot_dir"] / f"persona_prediction_distribution_{slug}.png",
        "group_precision": directories["plot_dir"] / f"persona_group_precision_{slug}.png",
        "feature_importance": directories["plot_dir"] / f"persona_feature_importance_top15_{slug}.png",
    }

    plot_class_distribution(metrics_payload["target_profile"]["class_distribution"], output_paths["class_distribution"])
    plot_confusion_matrix(
        y_true=predictions_df["actual_persona_name"].astype(str).tolist(),
        y_pred=predictions_df["predicted_persona_name"].astype(str).tolist(),
        class_names=class_names,
        output_path=output_paths["confusion_matrix"],
    )
    top_f1_classes = plot_per_class_metrics(classification_report, output_paths["per_class_metrics"])
    predicted_counts = plot_prediction_distribution(predictions_df, output_paths["prediction_distribution"])
    group_precision = plot_group_precision(predictions_df, output_paths["group_precision"])
    top_features = plot_feature_importance(feature_importance_df, output_paths["feature_importance"])

    report_text = build_markdown_report(
        metrics_payload=metrics_payload,
        predictions_df=predictions_df,
        output_paths=output_paths,
        predicted_counts=predicted_counts,
        group_precision=group_precision,
        top_features=top_features,
        top_f1_classes=top_f1_classes,
    )
    report_path = directories["report_dir"] / f"persona_ml_eda_report_{slug}.md"
    write_text(report_path, report_text)

    print("=" * 80)
    print("CUSTOMERDNA AI - PERSONA ML EDA")
    print("=" * 80)
    print(f"Training metrics: {metrics_path}")
    print(f"Holdout predictions: {predictions_path}")
    print(f"Feature importance: {feature_importance_path}")
    print(f"Report: {report_path}")
    for label, path in output_paths.items():
        print(f"{label}: {path}")
    print("Persona ML EDA completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
