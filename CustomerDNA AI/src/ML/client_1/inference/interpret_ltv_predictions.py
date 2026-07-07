from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "pandas is required for LTV interpretation. Install it in your local environment first."
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interpret LTV model predictions into business-readable value bands and actions.",
    )
    parser.add_argument(
        "--use-case",
        default="ltv",
        help="Use-case config name stored under src/ML/client_1/configs without the .json suffix.",
    )
    parser.add_argument(
        "--training-metrics-path",
        default=None,
        help="Optional explicit LTV training metrics JSON path.",
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


def find_latest_training_metrics() -> Path:
    return find_latest_file(
        MODEL_METADATA_DIR,
        "ltv_regressor_training_metrics_*.json",
    )


def normalize_label(value: Any) -> str:
    if value is None:
        return "Unknown"
    text = str(value).strip()
    return text if text else "Unknown"


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


def assign_value_bands(predictions_df: pd.DataFrame) -> pd.Series:
    rank_values = predictions_df["predicted_ltv_value"].rank(method="first")
    band_codes = pd.qcut(rank_values, q=4, labels=["Low", "Medium", "High", "Premium"])
    return band_codes.astype(str)


def recommended_action(row: pd.Series) -> str:
    band = row["predicted_value_band"]
    segment = normalize_label(row.get("reference_final_customer_segment"))
    sales_band = normalize_label(row.get("reference_sales_value_band"))
    value_tier = normalize_label(row.get("reference_customer_value_tier"))

    if band == "Premium":
        return (
            "Prioritize white-glove retention, personalized upsell, and premium-service treatment to protect "
            "future value."
        )
    if band == "High":
        return (
            "Use cross-sell and loyalty reinforcement campaigns to grow wallet share while preserving retention."
        )
    if band == "Medium":
        return (
            "Target with growth campaigns, product discovery, and engagement journeys to increase future value."
        )
    if segment == "Dormant" or sales_band == "No Sales":
        return "Apply low-cost reactivation and nurture journeys rather than high-cost premium interventions."
    if value_tier in {"Low Value", "Unclassified"}:
        return "Keep in standard lifecycle programs and monitor for progression into stronger value bands."
    return "Use cost-efficient lifecycle communication and monitor future value movement."


def build_markdown_report(
    *,
    interpretation_payload: dict[str, Any],
    summary_df: pd.DataFrame,
    top_features_df: pd.DataFrame,
) -> str:
    selected_model = interpretation_payload["selected_model"]
    metrics = selected_model["test_metrics"]

    lines = [
        "# LTV Prediction Interpretation",
        "",
        f"- Created at: `{interpretation_payload['created_at_utc']}`",
        f"- Use case: `{interpretation_payload['use_case']}`",
        f"- Source training metrics: `{interpretation_payload['training_metrics_path']}`",
        f"- Selected model: `{selected_model['model_name']}`",
        f"- MAE: `{metrics['mae']:.6f}`",
        f"- RMSE: `{metrics['rmse']:.6f}`",
        f"- R²: `{metrics['r2_score']:.6f}`",
        f"- Explained variance: `{metrics['explained_variance']:.6f}`",
        "",
        "## Value Band Summary",
        "",
    ]

    for _, row in summary_df.iterrows():
        lines.extend(
            [
                f"### {row['predicted_value_band']} Value",
                "",
                f"- Customers in holdout set: `{int(row['customer_count'])}`",
                f"- Share of holdout set: `{float(row['customer_share']):.2%}`",
                f"- Average predicted LTV: `{float(row['avg_predicted_ltv']):.2f}`",
                f"- Average actual LTV: `{float(row['avg_actual_ltv']):.2f}`",
                f"- Median actual LTV: `{float(row['median_actual_ltv']):.2f}`",
                f"- Dominant value tier: `{row['reference_customer_value_tier_dominant_value']}`",
                f"- Dominant sales band: `{row['reference_sales_value_band_dominant_value']}`",
                f"- Dominant segment: `{row['reference_final_customer_segment_dominant_value']}`",
                f"- Recommended action: {row['recommended_action']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Top Model Drivers",
            "",
            "| Rank | Feature | Importance |",
            "|---:|---|---:|",
        ]
    )

    for _, row in top_features_df.iterrows():
        lines.append(
            f"| {int(row['importance_rank'])} | {row['feature_name']} | {float(row['importance']):.6f} |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    common_config = load_common_config()
    use_case_config = load_use_case_config(args.use_case)
    training_metrics_path = Path(args.training_metrics_path) if args.training_metrics_path else find_latest_training_metrics()

    training_metrics = read_json(training_metrics_path)
    artifacts = training_metrics["artifacts"]
    selected_model = training_metrics["selected_model"]

    predictions_path = Path(artifacts["predictions_path"])
    feature_importance_path = Path(artifacts["feature_importance_path"])

    if not predictions_path.exists():
        raise FileNotFoundError(f"Holdout predictions file not found: {predictions_path}")
    if not feature_importance_path.exists():
        raise FileNotFoundError(f"Feature importance file not found: {feature_importance_path}")

    predictions_df = pd.read_csv(predictions_path, low_memory=False)
    feature_importance_df = pd.read_csv(feature_importance_path, low_memory=False)

    predictions_df["predicted_value_band"] = assign_value_bands(predictions_df)
    predictions_df["recommended_action"] = predictions_df.apply(recommended_action, axis=1)
    predictions_df["prediction_abs_error_band"] = pd.cut(
        predictions_df["absolute_error"],
        bins=[-float("inf"), 50, 250, 1000, float("inf")],
        labels=["Very Low Error", "Low Error", "Moderate Error", "High Error"],
    ).astype(str)

    summary_rows: list[dict[str, Any]] = []
    for band in ["Premium", "High", "Medium", "Low"]:
        band_slice = predictions_df[predictions_df["predicted_value_band"] == band].copy()
        if band_slice.empty:
            continue

        value_tier_summary = dominant_value_summary(band_slice["reference_customer_value_tier"])
        sales_band_summary = dominant_value_summary(band_slice["reference_sales_value_band"])
        segment_summary = dominant_value_summary(band_slice["reference_final_customer_segment"])

        summary_rows.append(
            {
                "predicted_value_band": band,
                "customer_count": int(len(band_slice)),
                "customer_share": round(float(len(band_slice) / len(predictions_df)), 6),
                "avg_predicted_ltv": round(float(band_slice["predicted_ltv_value"].mean()), 6),
                "avg_actual_ltv": round(float(band_slice["actual_ltv_value"].mean()), 6),
                "median_actual_ltv": round(float(band_slice["actual_ltv_value"].median()), 6),
                "avg_absolute_error": round(float(band_slice["absolute_error"].mean()), 6),
                "reference_customer_value_tier_dominant_value": value_tier_summary["value"],
                "reference_customer_value_tier_dominant_share": value_tier_summary["share"],
                "reference_sales_value_band_dominant_value": sales_band_summary["value"],
                "reference_sales_value_band_dominant_share": sales_band_summary["share"],
                "reference_final_customer_segment_dominant_value": segment_summary["value"],
                "reference_final_customer_segment_dominant_share": segment_summary["share"],
                "recommended_action": band_slice["recommended_action"].mode().iloc[0],
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    top_features_df = feature_importance_df.sort_values("importance_rank").head(15).copy()

    created_at = datetime.now(timezone.utc)
    slug = timestamp_slug(common_config, created_at)

    BUSINESS_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    interpreted_predictions_path = BUSINESS_SUMMARIES_DIR / f"ltv_interpreted_predictions_{slug}.csv"
    value_band_summary_path = BUSINESS_SUMMARIES_DIR / f"ltv_value_band_summary_{slug}.csv"
    interpretation_metadata_path = MODEL_METADATA_DIR / f"ltv_prediction_interpretation_{slug}.json"
    interpretation_report_path = BUSINESS_SUMMARIES_DIR / f"ltv_prediction_interpretation_{slug}.md"

    predictions_df.to_csv(interpreted_predictions_path, index=False)
    summary_df.to_csv(value_band_summary_path, index=False)

    interpretation_payload = {
        "artifact_type": "ltv_prediction_interpretation",
        "created_at_utc": isoformat_utc(created_at),
        "use_case": use_case_config["use_case"],
        "training_metrics_path": str(training_metrics_path),
        "selected_model": selected_model,
        "source_predictions_path": str(predictions_path),
        "source_feature_importance_path": str(feature_importance_path),
        "artifacts": {
            "interpreted_predictions_path": str(interpreted_predictions_path),
            "value_band_summary_path": str(value_band_summary_path),
            "interpretation_metadata_path": str(interpretation_metadata_path),
            "interpretation_report_path": str(interpretation_report_path),
        },
        "value_band_method": "Quartile-based ranking on holdout predicted LTV values.",
        "top_feature_names": top_features_df["feature_name"].tolist(),
    }

    interpretation_metadata_path.write_text(
        json.dumps(interpretation_payload, indent=2) + "\n",
        encoding="utf-8",
    )
    interpretation_report_path.write_text(
        build_markdown_report(
            interpretation_payload=interpretation_payload,
            summary_df=summary_df,
            top_features_df=top_features_df,
        ),
        encoding="utf-8",
    )

    print("=" * 80)
    print("CUSTOMERDNA AI - LTV PREDICTION INTERPRETATION")
    print("=" * 80)
    print(f"Use case: {use_case_config['use_case']}")
    print(f"Training metrics: {training_metrics_path}")
    print(f"Source predictions: {predictions_path}")
    print(f"Source feature importance: {feature_importance_path}")
    print(f"Interpreted predictions: {interpreted_predictions_path}")
    print(f"Value band summary: {value_band_summary_path}")
    print(f"Interpretation metadata: {interpretation_metadata_path}")
    print(f"Interpretation report: {interpretation_report_path}")
    print(f"Value bands summarized: {len(summary_df)}")
    print("LTV prediction interpretation completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
