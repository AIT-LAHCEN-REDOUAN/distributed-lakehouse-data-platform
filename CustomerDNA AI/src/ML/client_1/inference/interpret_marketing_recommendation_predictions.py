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
        "pandas is required for marketing recommendation interpretation. Install it in your local environment first."
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
        description="Interpret marketing recommendation model predictions into business-readable summaries.",
    )
    parser.add_argument(
        "--use-case",
        default="marketing_recommendation",
        help="Use-case config name stored under src/ML/client_1/configs without the .json suffix.",
    )
    parser.add_argument(
        "--training-metrics-path",
        default=None,
        help="Optional explicit marketing recommendation training metrics JSON path.",
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
        "marketing_recommendation_classifier_training_metrics_*.json",
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


def quality_band(precision_value: float) -> str:
    if precision_value >= 0.75:
        return "High Confidence"
    if precision_value >= 0.50:
        return "Moderate Confidence"
    if precision_value >= 0.30:
        return "Low Confidence"
    return "Very Low Confidence"


def reliability_message(precision_value: float) -> str:
    if precision_value >= 0.75:
        return "This predicted offer class is reliable enough for operational use with normal monitoring."
    if precision_value >= 0.50:
        return "This predicted offer class is directionally useful but should still be reviewed with business rules."
    if precision_value >= 0.30:
        return "This predicted offer class should be treated as weak guidance and combined with stronger rule filters."
    return "This predicted offer class is not reliable on its own and should only be used as exploratory support."


def build_offer_description(row: pd.Series) -> str:
    offer_type = normalize_label(row["predicted_recommended_offer_type"])
    objective = normalize_label(row["recommended_campaign_objective_dominant_value"])
    channel = normalize_label(row["recommended_channel_dominant_value"])
    timing = normalize_label(row["recommended_contact_timing_dominant_value"])
    precision_value = float(row["offer_prediction_precision_within_group"])

    return (
        f"The model predicts the '{offer_type}' offer type for this customer group. "
        f"The dominant linked campaign objective is '{objective}', the usual outbound channel is '{channel}', "
        f"and the dominant timing is '{timing}'. Prediction precision within this predicted group is "
        f"{precision_value:.2%}, which corresponds to a '{row['confidence_band']}' quality level."
    )


def build_markdown_report(
    *,
    interpretation_payload: dict[str, Any],
    summary_df: pd.DataFrame,
    top_features_df: pd.DataFrame,
) -> str:
    selected_model = interpretation_payload["selected_model"]
    metrics = selected_model["test_metrics"]

    lines = [
        "# Marketing Recommendation Prediction Interpretation",
        "",
        f"- Created at: `{interpretation_payload['created_at_utc']}`",
        f"- Use case: `{interpretation_payload['use_case']}`",
        f"- Source training metrics: `{interpretation_payload['training_metrics_path']}`",
        f"- Selected model: `{selected_model['model_name']}`",
        f"- Accuracy: `{metrics['accuracy']:.6f}`",
        f"- Balanced accuracy: `{metrics['balanced_accuracy']:.6f}`",
        f"- Macro F1: `{metrics['f1_macro']:.6f}`",
        f"- Weighted F1: `{metrics['f1_weighted']:.6f}`",
        "",
        "## Offer Group Summary",
        "",
    ]

    for _, row in summary_df.iterrows():
        lines.extend(
            [
                f"### {row['predicted_recommended_offer_type']}",
                "",
                f"- Customers in holdout set: `{int(row['customer_count'])}`",
                f"- Share of holdout set: `{float(row['customer_share']):.2%}`",
                f"- Precision within predicted group: `{float(row['offer_prediction_precision_within_group']):.2%}`",
                f"- Confidence band: `{row['confidence_band']}`",
                f"- Dominant objective: `{row['recommended_campaign_objective_dominant_value']}`",
                f"- Dominant channel: `{row['recommended_channel_dominant_value']}`",
                f"- Dominant timing: `{row['recommended_contact_timing_dominant_value']}`",
                f"- Dominant next best action: `{row['recommended_next_best_action_dominant_value']}`",
                f"- Description: {row['offer_group_description']}",
                f"- Reliability note: {row['reliability_message']}",
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

    predictions_df["prediction_result"] = predictions_df.apply(
        lambda row: "Correct" if row["prediction_correct_flag"] == 1 else "Incorrect",
        axis=1,
    )

    summary_rows: list[dict[str, Any]] = []
    for offer_type in sorted(
        predictions_df["predicted_recommended_offer_type"].dropna().astype(str).unique().tolist()
    ):
        offer_slice = predictions_df[
            predictions_df["predicted_recommended_offer_type"].astype(str) == offer_type
        ].copy()
        if offer_slice.empty:
            continue

        precision_within_group = float(offer_slice["prediction_correct_flag"].mean())
        objective_summary = dominant_value_summary(offer_slice["recommended_campaign_objective"])
        channel_summary = dominant_value_summary(offer_slice["recommended_channel"])
        timing_summary = dominant_value_summary(offer_slice["recommended_contact_timing"])
        action_summary = dominant_value_summary(offer_slice["recommended_next_best_action"])
        priority_summary = dominant_value_summary(offer_slice["recommendation_priority_band"])
        persona_summary = dominant_value_summary(offer_slice["persona_name"])

        summary_rows.append(
            {
                "predicted_recommended_offer_type": offer_type,
                "customer_count": int(len(offer_slice)),
                "customer_share": round(float(len(offer_slice) / len(predictions_df)), 6),
                "offer_prediction_precision_within_group": round(precision_within_group, 6),
                "confidence_band": quality_band(precision_within_group),
                "recommended_campaign_objective_dominant_value": objective_summary["value"],
                "recommended_campaign_objective_dominant_share": objective_summary["share"],
                "recommended_channel_dominant_value": channel_summary["value"],
                "recommended_channel_dominant_share": channel_summary["share"],
                "recommended_contact_timing_dominant_value": timing_summary["value"],
                "recommended_contact_timing_dominant_share": timing_summary["share"],
                "recommended_next_best_action_dominant_value": action_summary["value"],
                "recommended_next_best_action_dominant_share": action_summary["share"],
                "recommendation_priority_band_dominant_value": priority_summary["value"],
                "recommendation_priority_band_dominant_share": priority_summary["share"],
                "persona_name_dominant_value": persona_summary["value"],
                "persona_name_dominant_share": persona_summary["share"],
                "reliability_message": reliability_message(precision_within_group),
            }
        )

    summary_df = pd.DataFrame(summary_rows).sort_values(
        ["customer_count", "predicted_recommended_offer_type"],
        ascending=[False, True],
    )
    summary_df["offer_group_description"] = summary_df.apply(build_offer_description, axis=1)

    offer_lookup = summary_df[
        [
            "predicted_recommended_offer_type",
            "confidence_band",
            "offer_group_description",
            "reliability_message",
        ]
    ].copy()
    interpreted_predictions_df = predictions_df.merge(
        offer_lookup,
        on="predicted_recommended_offer_type",
        how="left",
    )

    top_features_df = feature_importance_df.sort_values("importance_rank").head(15).copy()

    created_at = datetime.now(timezone.utc)
    slug = timestamp_slug(common_config, created_at)

    BUSINESS_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    interpreted_predictions_path = (
        BUSINESS_SUMMARIES_DIR / f"marketing_recommendation_interpreted_predictions_{slug}.csv"
    )
    recommendation_summary_path = (
        BUSINESS_SUMMARIES_DIR / f"marketing_recommendation_offer_summary_{slug}.csv"
    )
    interpretation_metadata_path = (
        MODEL_METADATA_DIR / f"marketing_recommendation_prediction_interpretation_{slug}.json"
    )
    interpretation_report_path = (
        BUSINESS_SUMMARIES_DIR / f"marketing_recommendation_prediction_interpretation_{slug}.md"
    )

    interpreted_predictions_df.to_csv(interpreted_predictions_path, index=False)
    summary_df.to_csv(recommendation_summary_path, index=False)

    interpretation_payload = {
        "artifact_type": "marketing_recommendation_prediction_interpretation",
        "created_at_utc": isoformat_utc(created_at),
        "use_case": use_case_config["use_case"],
        "training_metrics_path": str(training_metrics_path),
        "selected_model": selected_model,
        "source_predictions_path": str(predictions_path),
        "source_feature_importance_path": str(feature_importance_path),
        "artifacts": {
            "interpreted_predictions_path": str(interpreted_predictions_path),
            "recommendation_summary_path": str(recommendation_summary_path),
            "interpretation_metadata_path": str(interpretation_metadata_path),
            "interpretation_report_path": str(interpretation_report_path),
        },
        "top_feature_names": top_features_df["feature_name"].tolist(),
        "predicted_offer_types_summarized": summary_df["predicted_recommended_offer_type"].tolist(),
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
    print("CUSTOMERDNA AI - MARKETING RECOMMENDATION PREDICTION INTERPRETATION")
    print("=" * 80)
    print(f"Use case: {use_case_config['use_case']}")
    print(f"Training metrics: {training_metrics_path}")
    print(f"Source predictions: {predictions_path}")
    print(f"Source feature importance: {feature_importance_path}")
    print(f"Interpreted predictions: {interpreted_predictions_path}")
    print(f"Recommendation summary: {recommendation_summary_path}")
    print(f"Interpretation metadata: {interpretation_metadata_path}")
    print(f"Interpretation report: {interpretation_report_path}")
    print(f"Offer groups summarized: {len(summary_df)}")
    print("Marketing recommendation prediction interpretation completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
