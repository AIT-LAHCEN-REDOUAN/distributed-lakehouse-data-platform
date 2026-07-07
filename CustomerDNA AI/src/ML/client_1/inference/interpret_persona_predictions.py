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
        "pandas is required for persona interpretation. Install it in your local environment first."
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
        description="Interpret persona model predictions into business-readable persona summaries and actions.",
    )
    parser.add_argument(
        "--use-case",
        default="persona",
        help="Use-case config name stored under src/ML/client_1/configs without the .json suffix.",
    )
    parser.add_argument(
        "--training-metrics-path",
        default=None,
        help="Optional explicit persona training metrics JSON path.",
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
        "persona_classifier_training_metrics_*.json",
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


def build_persona_description(row: pd.Series) -> str:
    persona_name = normalize_label(row["predicted_persona_name"])
    lifecycle_stage = normalize_label(row["lifecycle_stage_dominant_value"])
    digital_affinity = normalize_label(row["digital_affinity_dominant_value"])
    price_sensitivity = normalize_label(row["price_sensitivity_dominant_value"])
    value_tier = normalize_label(row["customer_value_tier_dominant_value"])
    accuracy = float(row["persona_prediction_precision_within_group"])

    return (
        f"This predicted persona group is dominated by customers labeled as '{persona_name}'. "
        f"They are most commonly in the '{lifecycle_stage}' lifecycle stage, show "
        f"'{digital_affinity}' behavior, and tend toward '{price_sensitivity}'. "
        f"The dominant value tier is '{value_tier}', and the holdout precision for this predicted "
        f"persona is {accuracy:.2%}."
    )


def recommended_action(persona_name: str) -> str:
    persona_name = normalize_label(persona_name)
    if persona_name == "Premium Loyalist":
        return "Protect loyalty with premium offers, recognition, and high-touch personalized journeys."
    if persona_name == "At-Risk High Spender":
        return "Prioritize retention recovery with curated offers and urgent engagement follow-up."
    if persona_name == "Growth Challenger":
        return "Use conversion-acceleration campaigns, bundles, and progressive upsell strategies."
    if persona_name == "Dormant Customer":
        return "Launch reactivation journeys with simple incentives and reminder messaging."
    if persona_name == "Lost Customer":
        return "Treat as win-back segment and control spend carefully with selective reactivation offers."
    if persona_name == "Promo-Driven Regular":
        return "Lead with promotion-sensitive campaigns and savings-oriented product messaging."
    if persona_name == "Digital Explorer":
        return "Use digital-first recommendations, app engagement nudges, and online cross-sell journeys."
    return "Maintain personalized lifecycle communication and monitor behavior shifts."


def build_markdown_report(
    *,
    interpretation_payload: dict[str, Any],
    summary_df: pd.DataFrame,
    top_features_df: pd.DataFrame,
) -> str:
    selected_model = interpretation_payload["selected_model"]
    metrics = selected_model["test_metrics"]

    lines = [
        "# Persona Prediction Interpretation",
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
        "## Persona Group Summary",
        "",
    ]

    for _, row in summary_df.iterrows():
        lines.extend(
            [
                f"### {row['predicted_persona_name']}",
                "",
                f"- Customers in holdout set: `{int(row['customer_count'])}`",
                f"- Share of holdout set: `{float(row['customer_share']):.2%}`",
                f"- Dominant lifecycle stage: `{row['lifecycle_stage_dominant_value']}`",
                f"- Dominant digital affinity: `{row['digital_affinity_dominant_value']}`",
                f"- Dominant price sensitivity: `{row['price_sensitivity_dominant_value']}`",
                f"- Persona precision within group: `{float(row['persona_prediction_precision_within_group']):.2%}`",
                f"- Description: {row['persona_group_description']}",
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

    predictions_df["prediction_result"] = predictions_df.apply(
        lambda row: "Correct" if row["prediction_correct_flag"] == 1 else "Incorrect",
        axis=1,
    )
    predictions_df["recommended_action"] = predictions_df["predicted_persona_name"].apply(recommended_action)

    summary_rows: list[dict[str, Any]] = []
    for persona_name in sorted(predictions_df["predicted_persona_name"].dropna().astype(str).unique().tolist()):
        persona_slice = predictions_df[predictions_df["predicted_persona_name"].astype(str) == persona_name].copy()
        if persona_slice.empty:
            continue

        lifecycle_summary = dominant_value_summary(persona_slice["lifecycle_stage"])
        digital_summary = dominant_value_summary(persona_slice["digital_affinity"])
        price_summary = dominant_value_summary(persona_slice["price_sensitivity"])
        channel_summary = dominant_value_summary(persona_slice["channel_preference_profile"])
        value_tier_summary = dominant_value_summary(persona_slice["customer_value_tier"])
        retention_summary = dominant_value_summary(persona_slice["retention_status"])

        precision_within_group = float(persona_slice["prediction_correct_flag"].mean())

        summary_row = {
            "predicted_persona_name": persona_name,
            "customer_count": int(len(persona_slice)),
            "customer_share": round(float(len(persona_slice) / len(predictions_df)), 6),
            "persona_prediction_precision_within_group": round(precision_within_group, 6),
            "lifecycle_stage_dominant_value": lifecycle_summary["value"],
            "lifecycle_stage_dominant_share": lifecycle_summary["share"],
            "digital_affinity_dominant_value": digital_summary["value"],
            "digital_affinity_dominant_share": digital_summary["share"],
            "price_sensitivity_dominant_value": price_summary["value"],
            "price_sensitivity_dominant_share": price_summary["share"],
            "channel_preference_profile_dominant_value": channel_summary["value"],
            "channel_preference_profile_dominant_share": channel_summary["share"],
            "customer_value_tier_dominant_value": value_tier_summary["value"],
            "customer_value_tier_dominant_share": value_tier_summary["share"],
            "retention_status_dominant_value": retention_summary["value"],
            "retention_status_dominant_share": retention_summary["share"],
            "recommended_action": recommended_action(persona_name),
        }
        summary_rows.append(summary_row)

    summary_df = pd.DataFrame(summary_rows).sort_values(
        ["customer_count", "predicted_persona_name"],
        ascending=[False, True],
    )
    summary_df["persona_group_description"] = summary_df.apply(build_persona_description, axis=1)

    persona_lookup = summary_df[
        ["predicted_persona_name", "persona_group_description", "recommended_action"]
    ].copy()
    interpreted_predictions_df = predictions_df.merge(
        persona_lookup,
        on="predicted_persona_name",
        how="left",
    )

    top_features_df = feature_importance_df.sort_values("importance_rank").head(15).copy()

    created_at = datetime.now(timezone.utc)
    slug = timestamp_slug(common_config, created_at)

    BUSINESS_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    interpreted_predictions_path = BUSINESS_SUMMARIES_DIR / f"persona_interpreted_predictions_{slug}.csv"
    persona_summary_path = BUSINESS_SUMMARIES_DIR / f"persona_group_summary_{slug}.csv"
    interpretation_metadata_path = MODEL_METADATA_DIR / f"persona_prediction_interpretation_{slug}.json"
    interpretation_report_path = BUSINESS_SUMMARIES_DIR / f"persona_prediction_interpretation_{slug}.md"

    interpreted_predictions_df.to_csv(interpreted_predictions_path, index=False)
    summary_df.to_csv(persona_summary_path, index=False)

    interpretation_payload = {
        "artifact_type": "persona_prediction_interpretation",
        "created_at_utc": isoformat_utc(created_at),
        "use_case": use_case_config["use_case"],
        "training_metrics_path": str(training_metrics_path),
        "selected_model": selected_model,
        "source_predictions_path": str(predictions_path),
        "source_feature_importance_path": str(feature_importance_path),
        "artifacts": {
            "interpreted_predictions_path": str(interpreted_predictions_path),
            "persona_summary_path": str(persona_summary_path),
            "interpretation_metadata_path": str(interpretation_metadata_path),
            "interpretation_report_path": str(interpretation_report_path),
        },
        "top_feature_names": top_features_df["feature_name"].tolist(),
        "persona_names_summarized": summary_df["predicted_persona_name"].tolist(),
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
    print("CUSTOMERDNA AI - PERSONA PREDICTION INTERPRETATION")
    print("=" * 80)
    print(f"Use case: {use_case_config['use_case']}")
    print(f"Training metrics: {training_metrics_path}")
    print(f"Source predictions: {predictions_path}")
    print(f"Source feature importance: {feature_importance_path}")
    print(f"Interpreted predictions: {interpreted_predictions_path}")
    print(f"Persona summary: {persona_summary_path}")
    print(f"Interpretation metadata: {interpretation_metadata_path}")
    print(f"Interpretation report: {interpretation_report_path}")
    print(f"Persona groups summarized: {len(summary_df)}")
    print("Persona prediction interpretation completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
