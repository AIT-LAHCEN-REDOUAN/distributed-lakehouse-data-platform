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


USE_CASE = "marketing_recommendation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ML EDA plots and a markdown summary for the marketing recommendation model.",
    )
    parser.add_argument(
        "--training-metrics-path",
        default=None,
        help="Optional explicit marketing recommendation training metrics JSON path.",
    )
    parser.add_argument(
        "--interpretation-metadata-path",
        default=None,
        help="Optional explicit marketing recommendation interpretation metadata JSON path.",
    )
    return parser.parse_args()


def find_latest_training_metrics() -> Path:
    return find_latest_file(
        MODEL_METADATA_DIR,
        "marketing_recommendation_classifier_training_metrics_*.json",
    )


def find_latest_interpretation_metadata() -> Path:
    return find_latest_file(
        MODEL_METADATA_DIR,
        "marketing_recommendation_prediction_interpretation_*.json",
    )


def plot_candidate_model_comparison(candidate_df: pd.DataFrame, output_path: Path) -> str:
    plot_df = candidate_df.copy()
    plot_df["label"] = plot_df["model_name"].str.replace("_", " ").str.title()
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(plot_df))
    width = 0.25
    ax.bar([i - width for i in x], plot_df["accuracy"], width=width, label="Accuracy", color="#4C78A8")
    ax.bar(x, plot_df["balanced_accuracy"], width=width, label="Balanced Accuracy", color="#F58518")
    ax.bar([i + width for i in x], plot_df["f1_macro"], width=width, label="Macro F1", color="#54A24B")
    ax.set_xticks(list(x), plot_df["label"], rotation=15, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_title("Candidate Model Performance Comparison")
    ax.set_ylabel("Score")
    ax.legend()
    save_figure(fig, output_path)
    best_model = str(plot_df.sort_values("accuracy", ascending=False).iloc[0]["model_name"])
    return best_model


def plot_class_distribution(class_distribution: dict[str, int], output_path: Path) -> None:
    series = pd.Series(class_distribution).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(11, 6))
    series.plot(kind="bar", ax=ax, color="#4C78A8")
    ax.set_title("Recommendation Class Distribution")
    ax.set_xlabel("Recommended Offer Type")
    ax.set_ylabel("Customer Count")
    ax.tick_params(axis="x", rotation=25)
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
    ax.set_title("Recommendation Confusion Matrix")
    ax.set_xlabel("Predicted Offer Type")
    ax.set_ylabel("Actual Offer Type")
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
    ax.set_title("Per-Class Recommendation Metrics")
    ax.set_ylabel("Score")
    ax.legend()
    save_figure(fig, output_path)
    return metrics_df.head(2)["class_name"].tolist()


def plot_prediction_distribution(predictions_df: pd.DataFrame, output_path: Path) -> dict[str, int]:
    counts = (
        predictions_df["predicted_recommended_offer_type"]
        .astype(str)
        .value_counts()
        .sort_values(ascending=False)
    )
    fig, ax = plt.subplots(figsize=(11, 6))
    counts.plot(kind="bar", ax=ax, color="#F58518")
    ax.set_title("Predicted Recommendation Distribution")
    ax.set_xlabel("Predicted Offer Type")
    ax.set_ylabel("Holdout Customer Count")
    ax.tick_params(axis="x", rotation=25)
    for index, value in enumerate(counts.tolist()):
        ax.text(index, value, f"{value:,}", ha="center", va="bottom", fontsize=9)
    save_figure(fig, output_path)
    return {str(index): int(value) for index, value in counts.items()}


def plot_group_precision(summary_df: pd.DataFrame, output_path: Path) -> dict[str, float]:
    plot_df = summary_df.copy().sort_values("offer_prediction_precision_within_group", ascending=False)
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.bar(
        plot_df["predicted_recommended_offer_type"],
        plot_df["offer_prediction_precision_within_group"],
        color="#E45756",
    )
    ax.set_title("Precision Within Predicted Offer Groups")
    ax.set_xlabel("Predicted Offer Type")
    ax.set_ylabel("Precision")
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="x", rotation=20)
    for index, value in enumerate(plot_df["offer_prediction_precision_within_group"].tolist()):
        ax.text(index, value, f"{value:.2f}", ha="center", va="bottom", fontsize=9)
    save_figure(fig, output_path)
    return {
        str(row["predicted_recommended_offer_type"]): float(row["offer_prediction_precision_within_group"])
        for _, row in plot_df.iterrows()
    }


def plot_feature_importance(feature_importance_df: pd.DataFrame, output_path: Path) -> list[str]:
    top_df = feature_importance_df.sort_values("importance_rank").head(15).copy()
    top_df = top_df.sort_values("importance", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top_df["feature_name"], top_df["importance"], color="#7A5195")
    ax.set_title("Top Recommendation Feature Importances")
    ax.set_xlabel("Importance")
    ax.set_ylabel("Feature")
    save_figure(fig, output_path)
    return top_df.sort_values("importance", ascending=False)["feature_name"].tolist()


def build_markdown_report(
    *,
    metrics_payload: dict,
    interpretation_payload: dict,
    predictions_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    output_paths: dict[str, Path],
    predicted_counts: dict[str, int],
    group_precision: dict[str, float],
    top_features: list[str],
    strongest_classes: list[str],
    best_model_name: str,
) -> str:
    selected_metrics = metrics_payload["selected_model"]["test_metrics"]
    target_profile = metrics_payload["target_profile"]

    observations: list[str] = []
    if selected_metrics["accuracy"] > selected_metrics["balanced_accuracy"]:
        observations.append(
            "Accuracy is noticeably higher than balanced accuracy, which means the model is benefiting from class imbalance."
        )
    if selected_metrics["f1_macro"] < selected_metrics["f1_weighted"]:
        observations.append(
            "Weighted F1 is much stronger than macro F1, so the model mainly performs on frequent offer classes and struggles on rare ones."
        )
    if group_precision:
        best_group = max(group_precision, key=group_precision.get)
        weakest_group = min(group_precision, key=group_precision.get)
        observations.append(
            f"The strongest predicted offer group is '{best_group}' with precision {group_precision[best_group]:.2%}, while the weakest is '{weakest_group}' with precision {group_precision[weakest_group]:.2%}."
        )
    if len(predicted_counts) < target_profile["class_count"]:
        observations.append(
            "The model does not actively predict every business offer class in the holdout set, which is a strong signal of limited class separability."
        )
    if not observations:
        observations.append("The recommendation baseline behaves consistently without major warning signs.")

    lines = [
        "# Marketing Recommendation ML EDA Report",
        "",
        f"- Training metrics source: `{metrics_payload['artifacts']['metrics_path']}`",
        f"- Holdout predictions source: `{metrics_payload['artifacts']['predictions_path']}`",
        f"- Feature importance source: `{metrics_payload['artifacts']['feature_importance_path']}`",
        f"- Interpreted recommendation summary source: `{interpretation_payload['artifacts']['recommendation_summary_path']}`",
        f"- Rows in modeled dataset: `{metrics_payload['row_count']}`",
        f"- Holdout rows: `{len(predictions_df)}`",
        "",
        "## Selected Model",
        "",
        f"- Selected model: `{metrics_payload['selected_model']['model_name']}`",
        f"- Best accuracy among candidates: `{best_model_name}`",
        f"- Accuracy: `{selected_metrics['accuracy']:.6f}`",
        f"- Balanced accuracy: `{selected_metrics['balanced_accuracy']:.6f}`",
        f"- Macro precision: `{selected_metrics['precision_macro']:.6f}`",
        f"- Macro recall: `{selected_metrics['recall_macro']:.6f}`",
        f"- Macro F1: `{selected_metrics['f1_macro']:.6f}`",
        f"- Weighted F1: `{selected_metrics['f1_weighted']:.6f}`",
        "",
        "## Training Class Distribution",
        "",
    ]
    lines.extend(
        [f"- `{class_name}`: `{count}`" for class_name, count in target_profile["class_distribution"].items()]
    )
    lines.extend(
        [
            "",
            "## Holdout Predicted Distribution",
            "",
        ]
    )
    lines.extend([f"- `{class_name}`: `{count}`" for class_name, count in predicted_counts.items()])
    lines.extend(
        [
            "",
            "## Strongest Predicted Classes",
            "",
        ]
    )
    lines.extend([f"- `{class_name}`" for class_name in strongest_classes])
    lines.extend(
        [
            "",
            "## Recommendation Group Summary",
            "",
        ]
    )
    for _, row in summary_df.sort_values("customer_count", ascending=False).iterrows():
        lines.extend(
            [
                f"### {row['predicted_recommended_offer_type']}",
                "",
                f"- Customer count: `{int(row['customer_count'])}`",
                f"- Customer share: `{float(row['customer_share']):.2%}`",
                f"- Precision within predicted group: `{float(row['offer_prediction_precision_within_group']):.2%}`",
                f"- Confidence band: `{row['confidence_band']}`",
                f"- Dominant objective: `{row['recommended_campaign_objective_dominant_value']}` (`{float(row['recommended_campaign_objective_dominant_share']):.2%}`)",
                f"- Dominant channel: `{row['recommended_channel_dominant_value']}` (`{float(row['recommended_channel_dominant_share']):.2%}`)",
                f"- Dominant persona: `{row['persona_name_dominant_value']}` (`{float(row['persona_name_dominant_share']):.2%}`)",
                f"- Reliability note: {row['reliability_message']}",
                "",
            ]
        )
    lines.extend(
        [
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
    interpretation_path = (
        Path(args.interpretation_metadata_path)
        if args.interpretation_metadata_path
        else find_latest_interpretation_metadata()
    )

    metrics_payload = read_json(metrics_path)
    interpretation_payload = read_json(interpretation_path)

    predictions_path = Path(metrics_payload["artifacts"]["predictions_path"])
    feature_importance_path = Path(metrics_payload["artifacts"]["feature_importance_path"])
    summary_path = Path(interpretation_payload["artifacts"]["recommendation_summary_path"])

    if not predictions_path.exists():
        raise FileNotFoundError(f"Holdout predictions file not found: {predictions_path}")
    if not feature_importance_path.exists():
        raise FileNotFoundError(f"Feature importance file not found: {feature_importance_path}")
    if not summary_path.exists():
        raise FileNotFoundError(f"Recommendation summary file not found: {summary_path}")

    predictions_df = pd.read_csv(predictions_path, low_memory=False)
    feature_importance_df = pd.read_csv(feature_importance_path, low_memory=False)
    summary_df = pd.read_csv(summary_path, low_memory=False)

    required_prediction_columns = {
        "actual_recommended_offer_type",
        "predicted_recommended_offer_type",
        "prediction_correct_flag",
    }
    missing_prediction_columns = required_prediction_columns.difference(predictions_df.columns)
    if missing_prediction_columns:
        raise ValueError(
            "Missing expected recommendation prediction columns: " + ", ".join(sorted(missing_prediction_columns))
        )

    required_summary_columns = {
        "predicted_recommended_offer_type",
        "customer_count",
        "customer_share",
        "offer_prediction_precision_within_group",
        "confidence_band",
        "recommended_campaign_objective_dominant_value",
        "recommended_campaign_objective_dominant_share",
        "recommended_channel_dominant_value",
        "recommended_channel_dominant_share",
        "persona_name_dominant_value",
        "persona_name_dominant_share",
        "reliability_message",
    }
    missing_summary_columns = required_summary_columns.difference(summary_df.columns)
    if missing_summary_columns:
        raise ValueError(
            "Missing expected recommendation summary columns: " + ", ".join(sorted(missing_summary_columns))
        )

    class_names = metrics_payload["target_profile"]["class_names"]
    classification_report = metrics_payload["selected_model"]["test_metrics"]["classification_report"]
    candidate_df = pd.DataFrame(
        [
            {
                "model_name": item["model_name"],
                "accuracy": item["test_metrics"]["accuracy"],
                "balanced_accuracy": item["test_metrics"]["balanced_accuracy"],
                "f1_macro": item["test_metrics"]["f1_macro"],
            }
            for item in metrics_payload["candidate_results"]
        ]
    )

    output_paths = {
        "candidate_models": directories["plot_dir"] / f"marketing_candidate_models_{slug}.png",
        "class_distribution": directories["plot_dir"] / f"marketing_class_distribution_{slug}.png",
        "confusion_matrix": directories["plot_dir"] / f"marketing_confusion_matrix_{slug}.png",
        "per_class_metrics": directories["plot_dir"] / f"marketing_per_class_metrics_{slug}.png",
        "prediction_distribution": directories["plot_dir"] / f"marketing_prediction_distribution_{slug}.png",
        "group_precision": directories["plot_dir"] / f"marketing_group_precision_{slug}.png",
        "feature_importance": directories["plot_dir"] / f"marketing_feature_importance_{slug}.png",
    }

    best_model_name = plot_candidate_model_comparison(candidate_df, output_paths["candidate_models"])
    plot_class_distribution(metrics_payload["target_profile"]["class_distribution"], output_paths["class_distribution"])
    plot_confusion_matrix(
        y_true=predictions_df["actual_recommended_offer_type"].astype(str).tolist(),
        y_pred=predictions_df["predicted_recommended_offer_type"].astype(str).tolist(),
        class_names=class_names,
        output_path=output_paths["confusion_matrix"],
    )
    strongest_classes = plot_per_class_metrics(classification_report, output_paths["per_class_metrics"])
    predicted_counts = plot_prediction_distribution(predictions_df, output_paths["prediction_distribution"])
    group_precision = plot_group_precision(summary_df, output_paths["group_precision"])
    top_features = plot_feature_importance(feature_importance_df, output_paths["feature_importance"])

    report_text = build_markdown_report(
        metrics_payload=metrics_payload,
        interpretation_payload=interpretation_payload,
        predictions_df=predictions_df,
        summary_df=summary_df,
        output_paths=output_paths,
        predicted_counts=predicted_counts,
        group_precision=group_precision,
        top_features=top_features,
        strongest_classes=strongest_classes,
        best_model_name=best_model_name,
    )
    report_path = directories["report_dir"] / f"marketing_recommendation_ml_eda_report_{slug}.md"
    write_text(report_path, report_text)

    print("=" * 80)
    print("CUSTOMERDNA AI - MARKETING RECOMMENDATION ML EDA")
    print("=" * 80)
    print(f"Training metrics: {metrics_path}")
    print(f"Interpretation metadata: {interpretation_path}")
    print(f"Holdout predictions: {predictions_path}")
    print(f"Feature importance: {feature_importance_path}")
    print(f"Recommendation summary: {summary_path}")
    print(f"Report: {report_path}")
    for label, path in output_paths.items():
        print(f"{label}: {path}")
    print("Marketing recommendation ML EDA completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
