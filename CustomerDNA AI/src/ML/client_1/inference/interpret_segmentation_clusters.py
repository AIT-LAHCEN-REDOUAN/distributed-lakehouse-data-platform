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
        "pandas is required for segmentation interpretation. Install it in your local environment first."
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
        description="Interpret trained segmentation clusters into business-readable segment names and descriptions.",
    )
    parser.add_argument(
        "--use-case",
        default="segmentation",
        help="Use-case config name stored under src/ML/client_1/configs without the .json suffix.",
    )
    parser.add_argument(
        "--training-metrics-path",
        default=None,
        help="Optional explicit segmentation training metrics JSON path.",
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
        "segmentation_kmeans_training_metrics_*.json",
    )


def normalize_label(value: Any) -> str:
    if value is None:
        return "Unknown"
    text = str(value).strip()
    return text if text else "Unknown"


def build_cluster_name(summary_row: pd.Series) -> str:
    customer_count = int(summary_row["customer_count"])
    final_segment = normalize_label(summary_row["reference_final_customer_segment_dominant_value"])
    value_tier = normalize_label(summary_row["reference_customer_value_tier_dominant_value"])
    engagement_tier = normalize_label(summary_row["reference_engagement_tier_dominant_value"])
    sales_band = normalize_label(summary_row["reference_sales_value_band_dominant_value"])
    order_band = normalize_label(summary_row["reference_order_frequency_band_dominant_value"])

    if customer_count <= 1:
        return "Extreme Outlier Customer"
    if final_segment == "Dormant":
        return "Dormant Low-Value Base"
    if final_segment == "Core Customer":
        return "Core Customers Under Watch"
    if final_segment == "VIP Active" and value_tier == "High Value":
        return "High-Value Active Customers"
    if final_segment == "High Value Low Engagement":
        return "High-Value Low-Engagement Customers"
    if final_segment == "Growth Opportunity":
        return "Growth Opportunity Customers"
    if sales_band == "Top Account":
        return "Top-Account Opportunity"
    if order_band == "Frequent Buyer":
        return "Frequent Buyer Cluster"
    if value_tier == "High Value":
        return "High-Value Customer Cluster"
    if engagement_tier in {"Highly Engaged", "Engaged"}:
        return "Engaged Customer Cluster"

    return f"{final_segment} Cluster"


def build_cluster_description(summary_row: pd.Series) -> str:
    customer_count = int(summary_row["customer_count"])
    share = float(summary_row["customer_share"])
    final_segment = normalize_label(summary_row["reference_final_customer_segment_dominant_value"])
    final_segment_share = float(summary_row["reference_final_customer_segment_dominant_share"])
    value_tier = normalize_label(summary_row["reference_customer_value_tier_dominant_value"])
    value_tier_share = float(summary_row["reference_customer_value_tier_dominant_share"])
    engagement_tier = normalize_label(summary_row["reference_engagement_tier_dominant_value"])
    engagement_tier_share = float(summary_row["reference_engagement_tier_dominant_share"])
    order_band = normalize_label(summary_row["reference_order_frequency_band_dominant_value"])
    geography = normalize_label(summary_row["reference_geography_profile_dominant_value"])

    if customer_count <= 1:
        return (
            "This cluster contains a single customer and should be treated as an outlier or edge-case profile "
            "rather than a stable business segment."
        )

    return (
        f"This segment represents {share:.2%} of the customer base ({customer_count} customers). "
        f"It is most strongly associated with the business segment '{final_segment}' "
        f"({final_segment_share:.2%} dominance), value tier '{value_tier}' "
        f"({value_tier_share:.2%}), and engagement tier '{engagement_tier}' "
        f"({engagement_tier_share:.2%}). Typical customers in this cluster are closest to the "
        f"'{order_band}' purchase pattern and the '{geography}' geography profile."
    )


def build_recommended_action(summary_row: pd.Series) -> str:
    customer_count = int(summary_row["customer_count"])
    final_segment = normalize_label(summary_row["reference_final_customer_segment_dominant_value"])
    value_tier = normalize_label(summary_row["reference_customer_value_tier_dominant_value"])
    engagement_tier = normalize_label(summary_row["reference_engagement_tier_dominant_value"])
    retention_status = normalize_label(summary_row["reference_retention_status_dominant_value"])

    if customer_count <= 1:
        return "Review manually as a possible outlier before using it in standard campaign logic."
    if final_segment == "Dormant":
        return "Use reactivation campaigns, low-friction offers, and simple reminder journeys."
    if final_segment == "Core Customer":
        return "Protect retention with loyalty messaging and moderate value reinforcement."
    if final_segment == "VIP Active" and value_tier == "High Value":
        return "Prioritize premium retention, exclusivity campaigns, and high-touch relationship management."
    if final_segment == "High Value Low Engagement":
        return "Focus on engagement recovery through personalized outreach and timely campaign nudges."
    if retention_status in {"High Risk", "Watchlist"}:
        return "Apply churn-prevention messaging and track behavior change closely."
    if engagement_tier in {"Highly Engaged", "Engaged"}:
        return "Use upsell and cross-sell offers while preserving the current experience quality."

    return "Monitor this segment and apply standard lifecycle communication until stronger patterns emerge."


def build_markdown_report(
    *,
    interpretation_payload: dict[str, Any],
    interpreted_summary_df: pd.DataFrame,
) -> str:
    lines = [
        "# Segmentation Cluster Interpretation",
        "",
        f"- Created at: `{interpretation_payload['created_at_utc']}`",
        f"- Use case: `{interpretation_payload['use_case']}`",
        f"- Source training metrics: `{interpretation_payload['training_metrics_path']}`",
        f"- Best cluster count: `{interpretation_payload['best_k']}`",
        f"- Silhouette score: `{interpretation_payload['silhouette_score']:.6f}`",
        "",
        "## Business Segments",
        "",
    ]

    for _, row in interpreted_summary_df.sort_values("cluster_id").iterrows():
        lines.extend(
            [
                f"### Cluster {int(row['cluster_id'])} - {row['cluster_name']}",
                "",
                f"- Customer count: `{int(row['customer_count'])}`",
                f"- Customer share: `{float(row['customer_share']):.2%}`",
                f"- Description: {row['cluster_description']}",
                f"- Recommended action: {row['recommended_action']}",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    common_config = load_common_config()
    use_case_config = load_use_case_config(args.use_case)
    training_metrics_path = Path(args.training_metrics_path) if args.training_metrics_path else find_latest_training_metrics()

    training_metrics = read_json(training_metrics_path)
    artifacts = training_metrics["artifacts"]

    assignments_path = Path(artifacts["assignments_path"])
    summary_path = Path(artifacts["summary_path"])

    if not assignments_path.exists():
        raise FileNotFoundError(f"Cluster assignments file not found: {assignments_path}")
    if not summary_path.exists():
        raise FileNotFoundError(f"Cluster summary file not found: {summary_path}")

    assignments_df = pd.read_csv(assignments_path, low_memory=False)
    summary_df = pd.read_csv(summary_path, low_memory=False)

    summary_df["cluster_name"] = summary_df.apply(build_cluster_name, axis=1)
    summary_df["cluster_description"] = summary_df.apply(build_cluster_description, axis=1)
    summary_df["recommended_action"] = summary_df.apply(build_recommended_action, axis=1)

    cluster_lookup = summary_df[
        ["cluster_id", "cluster_name", "cluster_description", "recommended_action"]
    ].copy()
    interpreted_assignments_df = assignments_df.merge(cluster_lookup, on="cluster_id", how="left")

    created_at = datetime.now(timezone.utc)
    slug = timestamp_slug(common_config, created_at)

    BUSINESS_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    interpreted_summary_path = BUSINESS_SUMMARIES_DIR / f"segmentation_interpreted_cluster_summary_{slug}.csv"
    interpreted_assignments_path = BUSINESS_SUMMARIES_DIR / f"segmentation_interpreted_assignments_{slug}.csv"
    interpretation_metadata_path = MODEL_METADATA_DIR / f"segmentation_cluster_interpretation_{slug}.json"
    interpretation_report_path = BUSINESS_SUMMARIES_DIR / f"segmentation_cluster_interpretation_{slug}.md"

    summary_df.to_csv(interpreted_summary_path, index=False)
    interpreted_assignments_df.to_csv(interpreted_assignments_path, index=False)

    interpretation_payload = {
        "artifact_type": "segmentation_cluster_interpretation",
        "created_at_utc": isoformat_utc(created_at),
        "use_case": use_case_config["use_case"],
        "training_metrics_path": str(training_metrics_path),
        "source_assignments_path": str(assignments_path),
        "source_summary_path": str(summary_path),
        "best_k": int(training_metrics["selected_model"]["best_k"]),
        "silhouette_score": float(training_metrics["selected_model"]["silhouette_score"]),
        "artifacts": {
            "interpreted_summary_path": str(interpreted_summary_path),
            "interpreted_assignments_path": str(interpreted_assignments_path),
            "interpretation_metadata_path": str(interpretation_metadata_path),
            "interpretation_report_path": str(interpretation_report_path),
        },
        "cluster_name_map": {
            str(int(row["cluster_id"])): row["cluster_name"]
            for _, row in summary_df.iterrows()
        },
    }

    interpretation_metadata_path.write_text(
        json.dumps(interpretation_payload, indent=2) + "\n",
        encoding="utf-8",
    )
    interpretation_report_path.write_text(
        build_markdown_report(
            interpretation_payload=interpretation_payload,
            interpreted_summary_df=summary_df,
        ),
        encoding="utf-8",
    )

    print("=" * 80)
    print("CUSTOMERDNA AI - SEGMENTATION CLUSTER INTERPRETATION")
    print("=" * 80)
    print(f"Use case: {use_case_config['use_case']}")
    print(f"Training metrics: {training_metrics_path}")
    print(f"Source assignments: {assignments_path}")
    print(f"Source summary: {summary_path}")
    print(f"Interpreted summary: {interpreted_summary_path}")
    print(f"Interpreted assignments: {interpreted_assignments_path}")
    print(f"Interpretation metadata: {interpretation_metadata_path}")
    print(f"Interpretation report: {interpretation_report_path}")
    print(f"Clusters interpreted: {len(summary_df)}")
    print("Segmentation cluster interpretation completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
