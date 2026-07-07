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
        "pandas is required for churn interpretation. Install it in your local environment first."
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
        description="Interpret churn model predictions into business-readable risk tiers and actions.",
    )
    parser.add_argument(
        "--use-case",
        default="churn",
        help="Use-case config name stored under src/ML/client_1/configs without the .json suffix.",
    )
    parser.add_argument(
        "--training-metrics-path",
        default=None,
        help="Optional explicit churn training metrics JSON path.",
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
        "churn_classifier_training_metrics_*.json",
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


def risk_band(probability: float) -> str:
    if probability >= 0.80:
        return "Critical"
    if probability >= 0.60:
        return "High"
    if probability >= 0.35:
        return "Medium"
    return "Low"


def recommended_action(row: pd.Series) -> str:
    band = row["predicted_risk_band"]
    retention_status = normalize_label(row.get("reference_retention_status"))
    customer_segment = normalize_label(row.get("reference_final_customer_segment"))
    value_tier = normalize_label(row.get("reference_customer_value_tier"))

    if band == "Critical":
        return (
            "Launch immediate retention intervention with personalized outreach, complaint resolution, "
            "and high-priority incentive follow-up."
        )
    if band == "High":
        return (
            "Place in proactive churn-prevention campaign with targeted offers and close journey monitoring."
        )
    if band == "Medium":
        return (
            "Use watchlist treatment: reminder messaging, engagement nudges, and satisfaction follow-up."
        )
    if retention_status in {"High Risk", "Watchlist"}:
        return "Maintain monitoring cadence and verify whether behavioral deterioration continues."
    if customer_segment in {"VIP Active", "Core Customer"} and value_tier == "High Value":
        return "Preserve loyalty with premium experience and avoid unnecessary discount-heavy campaigns."
    return "Continue standard lifecycle communication and monitor for new churn signals."


def build_markdown_report(
    *,
    interpretation_payload: dict[str, Any],
    summary_df: pd.DataFrame,
    top_features_df: pd.DataFrame,
) -> str:
    selected_model = interpretation_payload["selected_model"]
    metrics = selected_model["test_metrics"]

    lines = [
        "# Churn Prediction Interpretation",
        "",
        f"- Created at: `{interpretation_payload['created_at_utc']}`",
        f"- Use case: `{interpretation_payload['use_case']}`",
        f"- Source training metrics: `{interpretation_payload['training_metrics_path']}`",
        f"- Selected model: `{selected_model['model_name']}`",
        f"- Accuracy: `{metrics['accuracy']:.6f}`",
        f"- Precision: `{metrics['precision']:.6f}`",
        f"- Recall: `{metrics['recall']:.6f}`",
        f"- F1 score: `{metrics['f1_score']:.6f}`",
        f"- ROC-AUC: `{metrics['roc_auc']:.6f}`",
        f"- Average precision: `{metrics['average_precision']:.6f}`",
        "",
        "## Risk Band Summary",
        "",
    ]

    for _, row in summary_df.iterrows():
        lines.extend(
            [
                f"### {row['predicted_risk_band']} Risk",
                "",
                f"- Customers in holdout set: `{int(row['customer_count'])}`",
                f"- Share of holdout set: `{float(row['customer_share']):.2%}`",
                f"- Average predicted churn probability: `{float(row['avg_predicted_probability']):.4f}`",
                f"- Actual churn rate in band: `{float(row['actual_churn_rate']):.2%}`",
                f"- Dominant retention status: `{row['reference_retention_status_dominant_value']}`",
                f"- Dominant churn risk band: `{row['reference_churn_risk_band_dominant_value']}`",
                f"- Dominant customer segment: `{row['reference_final_customer_segment_dominant_value']}`",
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

    predictions_df["predicted_risk_band"] = predictions_df["predicted_churn_probability"].apply(risk_band)
    predictions_df["recommended_action"] = predictions_df.apply(recommended_action, axis=1)
    predictions_df["prediction_result"] = predictions_df.apply(
        lambda row: (
            "True Positive" if row["actual_churn_flag"] == 1 and row["predicted_churn_flag"] == 1 else
            "True Negative" if row["actual_churn_flag"] == 0 and row["predicted_churn_flag"] == 0 else
            "False Positive" if row["actual_churn_flag"] == 0 and row["predicted_churn_flag"] == 1 else
            "False Negative"
        ),
        axis=1,
    )

    summary_rows: list[dict[str, Any]] = []
    for band in ["Critical", "High", "Medium", "Low"]:
        band_slice = predictions_df[predictions_df["predicted_risk_band"] == band].copy()
        if band_slice.empty:
            continue

        retention_summary = dominant_value_summary(band_slice["reference_retention_status"])
        churn_band_summary = dominant_value_summary(band_slice["reference_churn_risk_band"])
        segment_summary = dominant_value_summary(band_slice["reference_final_customer_segment"])
        value_tier_summary = dominant_value_summary(band_slice["reference_customer_value_tier"])

        summary_rows.append(
            {
                "predicted_risk_band": band,
                "customer_count": int(len(band_slice)),
                "customer_share": round(float(len(band_slice) / len(predictions_df)), 6),
                "avg_predicted_probability": round(float(band_slice["predicted_churn_probability"].mean()), 6),
                "actual_churn_rate": round(float(band_slice["actual_churn_flag"].mean()), 6),
                "reference_retention_status_dominant_value": retention_summary["value"],
                "reference_retention_status_dominant_share": retention_summary["share"],
                "reference_churn_risk_band_dominant_value": churn_band_summary["value"],
                "reference_churn_risk_band_dominant_share": churn_band_summary["share"],
                "reference_final_customer_segment_dominant_value": segment_summary["value"],
                "reference_final_customer_segment_dominant_share": segment_summary["share"],
                "reference_customer_value_tier_dominant_value": value_tier_summary["value"],
                "reference_customer_value_tier_dominant_share": value_tier_summary["share"],
                "recommended_action": band_slice["recommended_action"].mode().iloc[0],
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    top_features_df = feature_importance_df.sort_values("importance_rank").head(15).copy()

    created_at = datetime.now(timezone.utc)
    slug = timestamp_slug(common_config, created_at)

    BUSINESS_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    interpreted_predictions_path = BUSINESS_SUMMARIES_DIR / f"churn_interpreted_predictions_{slug}.csv"
    risk_summary_path = BUSINESS_SUMMARIES_DIR / f"churn_risk_band_summary_{slug}.csv"
    interpretation_metadata_path = MODEL_METADATA_DIR / f"churn_prediction_interpretation_{slug}.json"
    interpretation_report_path = BUSINESS_SUMMARIES_DIR / f"churn_prediction_interpretation_{slug}.md"

    predictions_df.to_csv(interpreted_predictions_path, index=False)
    summary_df.to_csv(risk_summary_path, index=False)

    interpretation_payload = {
        "artifact_type": "churn_prediction_interpretation",
        "created_at_utc": isoformat_utc(created_at),
        "use_case": use_case_config["use_case"],
        "training_metrics_path": str(training_metrics_path),
        "selected_model": selected_model,
        "source_predictions_path": str(predictions_path),
        "source_feature_importance_path": str(feature_importance_path),
        "artifacts": {
            "interpreted_predictions_path": str(interpreted_predictions_path),
            "risk_summary_path": str(risk_summary_path),
            "interpretation_metadata_path": str(interpretation_metadata_path),
            "interpretation_report_path": str(interpretation_report_path),
        },
        "risk_band_thresholds": {
            "Critical": ">= 0.80",
            "High": ">= 0.60 and < 0.80",
            "Medium": ">= 0.35 and < 0.60",
            "Low": "< 0.35",
        },
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
    print("CUSTOMERDNA AI - CHURN PREDICTION INTERPRETATION")
    print("=" * 80)
    print(f"Use case: {use_case_config['use_case']}")
    print(f"Training metrics: {training_metrics_path}")
    print(f"Source predictions: {predictions_path}")
    print(f"Source feature importance: {feature_importance_path}")
    print(f"Interpreted predictions: {interpreted_predictions_path}")
    print(f"Risk summary: {risk_summary_path}")
    print(f"Interpretation metadata: {interpretation_metadata_path}")
    print(f"Interpretation report: {interpretation_report_path}")
    print(f"Risk bands summarized: {len(summary_df)}")
    print("Churn prediction interpretation completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
