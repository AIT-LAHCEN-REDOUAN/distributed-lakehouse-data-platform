from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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


USE_CASE = "ltv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ML EDA plots and a markdown summary for the LTV model.",
    )
    parser.add_argument(
        "--training-metrics-path",
        default=None,
        help="Optional explicit LTV training metrics JSON path.",
    )
    return parser.parse_args()


def find_latest_training_metrics() -> Path:
    return find_latest_file(
        MODEL_METADATA_DIR,
        "ltv_regressor_training_metrics_*.json",
    )


def assign_value_bands(predictions_df: pd.DataFrame) -> pd.Series:
    rank_values = predictions_df["predicted_ltv_value"].rank(method="first")
    return pd.qcut(rank_values, q=4, labels=["Low", "Medium", "High", "Premium"]).astype(str)


def plot_target_distribution(actual_values: np.ndarray, output_path: Path) -> None:
    fig, ax = plt.subplots()
    ax.hist(actual_values, bins=40, color="#4C78A8", alpha=0.85, edgecolor="white")
    ax.set_title("Actual LTV Distribution")
    ax.set_xlabel("Actual LTV Value")
    ax.set_ylabel("Customer Count")
    save_figure(fig, output_path)


def plot_prediction_distribution(predicted_values: np.ndarray, output_path: Path) -> None:
    fig, ax = plt.subplots()
    ax.hist(predicted_values, bins=40, color="#F58518", alpha=0.85, edgecolor="white")
    ax.set_title("Predicted LTV Distribution")
    ax.set_xlabel("Predicted LTV Value")
    ax.set_ylabel("Customer Count")
    save_figure(fig, output_path)


def plot_actual_vs_predicted(
    actual_values: np.ndarray,
    predicted_values: np.ndarray,
    output_path: Path,
) -> None:
    fig, ax = plt.subplots()
    ax.scatter(actual_values, predicted_values, alpha=0.35, color="#54A24B", s=18)
    min_value = float(min(actual_values.min(), predicted_values.min()))
    max_value = float(max(actual_values.max(), predicted_values.max()))
    ax.plot([min_value, max_value], [min_value, max_value], linestyle="--", color="black")
    ax.set_title("Actual vs Predicted LTV")
    ax.set_xlabel("Actual LTV Value")
    ax.set_ylabel("Predicted LTV Value")
    save_figure(fig, output_path)


def plot_residual_distribution(residuals: np.ndarray, output_path: Path) -> None:
    fig, ax = plt.subplots()
    ax.hist(residuals, bins=40, color="#E45756", alpha=0.85, edgecolor="white")
    ax.axvline(0, linestyle="--", color="black")
    ax.set_title("LTV Residual Distribution")
    ax.set_xlabel("Residual (Actual - Predicted)")
    ax.set_ylabel("Customer Count")
    save_figure(fig, output_path)


def plot_residuals_vs_predicted(
    predicted_values: np.ndarray,
    residuals: np.ndarray,
    output_path: Path,
) -> None:
    fig, ax = plt.subplots()
    ax.scatter(predicted_values, residuals, alpha=0.35, color="#7A5195", s=18)
    ax.axhline(0, linestyle="--", color="black")
    ax.set_title("Residuals vs Predicted LTV")
    ax.set_xlabel("Predicted LTV Value")
    ax.set_ylabel("Residual (Actual - Predicted)")
    save_figure(fig, output_path)


def plot_value_band_distribution(predictions_df: pd.DataFrame, output_path: Path) -> dict[str, int]:
    predictions_df = predictions_df.copy()
    predictions_df["predicted_value_band"] = assign_value_bands(predictions_df)
    ordered_bands = ["Premium", "High", "Medium", "Low"]
    counts = predictions_df["predicted_value_band"].value_counts().reindex(ordered_bands, fill_value=0)
    fig, ax = plt.subplots()
    counts.plot(kind="bar", ax=ax, color=["#B22222", "#E67E22", "#F1C40F", "#2ECC71"])
    ax.set_title("Predicted LTV Value Band Distribution")
    ax.set_xlabel("Value Band")
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
    ax.set_title("Top 15 LTV Feature Importances")
    ax.set_xlabel("Importance")
    ax.set_ylabel("Feature")
    save_figure(fig, output_path)
    return top_df.sort_values("importance", ascending=False)["feature_name"].head(5).tolist()


def build_markdown_report(
    *,
    metrics_payload: dict,
    predictions_df: pd.DataFrame,
    output_paths: dict[str, Path],
    value_band_counts: dict[str, int],
    top_features: list[str],
) -> str:
    selected_metrics = metrics_payload["selected_model"]["test_metrics"]
    target_profile = metrics_payload["target_profile"]
    residuals = predictions_df["prediction_error"].to_numpy(dtype=float)
    negative_target_count = int(target_profile["negative_count"])

    observations: list[str] = []
    if negative_target_count > 0:
        observations.append(
            f"The LTV target contains {negative_target_count} negative values, which confirms the need to keep the raw target instead of forcing a log transform."
        )
    if selected_metrics["r2_score"] < 0.4:
        observations.append(
            "The baseline explains part of the LTV variance, but this remains a difficult regression problem with substantial unexplained variation."
        )
    if abs(float(np.mean(residuals))) < 1e-6:
        observations.append("Residuals are centered close to zero, which suggests limited overall prediction bias.")
    if selected_metrics["rmse"] > selected_metrics["mae"] * 5:
        observations.append(
            "RMSE is much larger than MAE, which suggests a long-tail error pattern and a few high-impact prediction misses."
        )
    if not observations:
        observations.append("The LTV baseline shows stable regression behavior without major warning signals.")

    lines = [
        "# LTV ML EDA Report",
        "",
        f"- Training metrics source: `{metrics_payload['artifacts']['metrics_path']}`",
        f"- Holdout predictions source: `{metrics_payload['artifacts']['predictions_path']}`",
        f"- Feature importance source: `{metrics_payload['artifacts']['feature_importance_path']}`",
        f"- Rows in modeled dataset: `{metrics_payload['row_count']}`",
        f"- Holdout rows: `{len(predictions_df)}`",
        "",
        "## Key Metrics",
        "",
        f"- MAE: `{selected_metrics['mae']:.6f}`",
        f"- RMSE: `{selected_metrics['rmse']:.6f}`",
        f"- R²: `{selected_metrics['r2_score']:.6f}`",
        f"- Explained variance: `{selected_metrics['explained_variance']:.6f}`",
        f"- Median absolute error: `{selected_metrics['median_absolute_error']:.6f}`",
        "",
        "## Target Profile",
        "",
        f"- Target mean: `{target_profile['target_mean']:.6f}`",
        f"- Target median: `{target_profile['target_median']:.6f}`",
        f"- Target min: `{target_profile['target_min']:.6f}`",
        f"- Target max: `{target_profile['target_max']:.6f}`",
        f"- Negative targets: `{negative_target_count}`",
        "",
        "## Predicted Value Bands",
        "",
        f"- Premium: `{value_band_counts.get('Premium', 0)}`",
        f"- High: `{value_band_counts.get('High', 0)}`",
        f"- Medium: `{value_band_counts.get('Medium', 0)}`",
        f"- Low: `{value_band_counts.get('Low', 0)}`",
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
        "actual_ltv_value",
        "predicted_ltv_value",
        "prediction_error",
        "absolute_error",
    }
    missing_prediction_columns = required_prediction_columns.difference(predictions_df.columns)
    if missing_prediction_columns:
        raise ValueError(
            "Missing expected LTV prediction columns: " + ", ".join(sorted(missing_prediction_columns))
        )

    actual_values = predictions_df["actual_ltv_value"].to_numpy(dtype=float)
    predicted_values = predictions_df["predicted_ltv_value"].to_numpy(dtype=float)
    residuals = predictions_df["prediction_error"].to_numpy(dtype=float)

    output_paths = {
        "target_distribution": directories["plot_dir"] / f"ltv_target_distribution_{slug}.png",
        "prediction_distribution": directories["plot_dir"] / f"ltv_prediction_distribution_{slug}.png",
        "actual_vs_predicted": directories["plot_dir"] / f"ltv_actual_vs_predicted_{slug}.png",
        "residual_distribution": directories["plot_dir"] / f"ltv_residual_distribution_{slug}.png",
        "residuals_vs_predicted": directories["plot_dir"] / f"ltv_residuals_vs_predicted_{slug}.png",
        "value_band_distribution": directories["plot_dir"] / f"ltv_value_band_distribution_{slug}.png",
        "feature_importance": directories["plot_dir"] / f"ltv_feature_importance_top15_{slug}.png",
    }

    plot_target_distribution(actual_values, output_paths["target_distribution"])
    plot_prediction_distribution(predicted_values, output_paths["prediction_distribution"])
    plot_actual_vs_predicted(actual_values, predicted_values, output_paths["actual_vs_predicted"])
    plot_residual_distribution(residuals, output_paths["residual_distribution"])
    plot_residuals_vs_predicted(predicted_values, residuals, output_paths["residuals_vs_predicted"])
    value_band_counts = plot_value_band_distribution(predictions_df, output_paths["value_band_distribution"])
    top_features = plot_feature_importance(feature_importance_df, output_paths["feature_importance"])

    report_text = build_markdown_report(
        metrics_payload=metrics_payload,
        predictions_df=predictions_df,
        output_paths=output_paths,
        value_band_counts=value_band_counts,
        top_features=top_features,
    )
    report_path = directories["report_dir"] / f"ltv_ml_eda_report_{slug}.md"
    write_text(report_path, report_text)

    print("=" * 80)
    print("CUSTOMERDNA AI - LTV ML EDA")
    print("=" * 80)
    print(f"Training metrics: {metrics_path}")
    print(f"Holdout predictions: {predictions_path}")
    print(f"Feature importance: {feature_importance_path}")
    print(f"Report: {report_path}")
    for label, path in output_paths.items():
        print(f"{label}: {path}")
    print("LTV ML EDA completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
