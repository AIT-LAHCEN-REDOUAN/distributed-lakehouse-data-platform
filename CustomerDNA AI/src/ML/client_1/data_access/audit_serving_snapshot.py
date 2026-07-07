from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from schema_manifest import (
    EXPERIMENT_REPORTS_DIR,
    MANIFESTS_DIR,
    ensure_report_directories,
    isoformat_utc,
    load_common_config,
    load_use_case_config,
    read_json,
    timestamp_slug,
)


NEAR_CONSTANT_THRESHOLD = 0.98
SKEWNESS_ALERT_THRESHOLD = 2.0
TOP_VALUES_LIMIT = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit the latest ML serving snapshot for a given use case.",
    )
    parser.add_argument(
        "--use-case",
        default="segmentation",
        help="Use-case config name stored under src/ML/client_1/configs without the .json suffix.",
    )
    parser.add_argument(
        "--manifest-path",
        default=None,
        help="Optional explicit manifest path. If omitted, the latest matching manifest is used.",
    )
    return parser.parse_args()


def find_latest_manifest(use_case_config: dict[str, Any]) -> Path:
    prefix = use_case_config["snapshot_prefix"]
    candidates = sorted(
        MANIFESTS_DIR.glob(f"{prefix}_*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )

    if not candidates:
        raise FileNotFoundError(
            f"No manifest found for prefix '{prefix}' in {MANIFESTS_DIR}"
        )

    return candidates[0]


def is_null_like(value: str) -> bool:
    return value.strip() == ""


def try_parse_float(value: str) -> float:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Empty value cannot be parsed as float.")
    return float(cleaned)


def population_std(values: list[float], mean_value: float) -> float:
    if not values:
        return 0.0

    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def skewness(values: list[float], mean_value: float, std_value: float) -> float:
    if len(values) < 3 or std_value == 0:
        return 0.0

    return sum(((value - mean_value) / std_value) ** 3 for value in values) / len(values)


def top_values(counter: Counter[str], limit: int = TOP_VALUES_LIMIT) -> list[dict[str, Any]]:
    return [
        {"value": value, "count": count}
        for value, count in counter.most_common(limit)
    ]


def build_markdown_report(audit_payload: dict[str, Any]) -> str:
    dataset_overview = audit_payload["dataset_overview"]
    primary_key_checks = audit_payload["primary_key_checks"]
    feature_contract = audit_payload["feature_contract"]
    data_quality = audit_payload["data_quality"]

    lines = [
        "# Serving Snapshot Audit",
        "",
        f"- Audit created at: `{audit_payload['audit_created_at_utc']}`",
        f"- Use case: `{audit_payload['use_case']}`",
        f"- Source: `{audit_payload['source_relation']}`",
        f"- Snapshot path: `{audit_payload['snapshot_path']}`",
        "",
        "## Dataset Overview",
        "",
        f"- Rows observed: `{dataset_overview['row_count']}`",
        f"- Columns observed: `{dataset_overview['column_count']}`",
        f"- Numeric columns: `{dataset_overview['numeric_column_count']}`",
        f"- Categorical columns: `{dataset_overview['categorical_column_count']}`",
        "",
        "## Primary Key Checks",
        "",
        f"- Primary key column: `{primary_key_checks['primary_key_column']}`",
        f"- Duplicate primary key rows: `{primary_key_checks['duplicate_primary_key_rows']}`",
        f"- Unique primary key count: `{primary_key_checks['unique_primary_key_count']}`",
        "",
        "## Feature Contract",
        "",
        f"- Candidate feature columns: `{feature_contract['candidate_feature_column_count']}`",
        f"- Non-feature columns: `{feature_contract['non_feature_column_count']}`",
        f"- Reference label columns: `{feature_contract['reference_label_column_count']}`",
        "",
        "## Data Quality Signals",
        "",
        f"- Columns with nulls: `{data_quality['columns_with_nulls_count']}`",
        f"- Constant columns: `{len(data_quality['constant_columns'])}`",
        f"- Near-constant columns: `{len(data_quality['near_constant_columns'])}`",
        f"- Highly skewed numeric columns: `{len(data_quality['high_skew_numeric_columns'])}`",
        "",
    ]

    if data_quality["constant_columns"]:
        lines.extend([
            "### Constant Columns",
            "",
            ", ".join(f"`{column_name}`" for column_name in data_quality["constant_columns"]),
            "",
        ])

    if data_quality["near_constant_columns"]:
        lines.extend([
            "### Near-Constant Columns",
            "",
        ])
        for item in data_quality["near_constant_columns"]:
            lines.append(
                f"- `{item['column_name']}` dominant value `{item['dominant_value']}` with share `{item['dominant_share']:.4f}`"
            )
        lines.append("")

    if data_quality["high_skew_numeric_columns"]:
        lines.extend([
            "### Highly Skewed Numeric Columns",
            "",
        ])
        for item in data_quality["high_skew_numeric_columns"]:
            lines.append(
                f"- `{item['column_name']}` skewness `{item['skewness']:.4f}`, min `{item['min']}`, max `{item['max']}`"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    common_config = load_common_config()
    use_case_config = load_use_case_config(args.use_case)
    manifest_path = Path(args.manifest_path) if args.manifest_path else find_latest_manifest(use_case_config)
    manifest = read_json(manifest_path)
    snapshot_path = Path(manifest["artifacts"]["snapshot_path"])
    primary_key_column = manifest["source"]["primary_key"]
    columns = manifest["table_profile"]["columns"]
    candidate_feature_columns = manifest["modeling_contract"]["candidate_feature_columns"]
    non_feature_columns = manifest["modeling_contract"]["non_feature_columns"]
    reference_label_columns = manifest["modeling_contract"]["reference_label_columns"]

    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_path}")

    counters: dict[str, Counter[str]] = {column_name: Counter() for column_name in columns}
    null_counts = {column_name: 0 for column_name in columns}
    numeric_possible = {column_name: True for column_name in columns}
    numeric_values: dict[str, list[float]] = {column_name: [] for column_name in columns}

    seen_primary_keys: set[str] = set()
    duplicate_primary_key_rows = 0
    row_count = 0

    with snapshot_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)

        for row in reader:
            row_count += 1
            primary_key_value = (row.get(primary_key_column) or "").strip()
            if primary_key_value in seen_primary_keys:
                duplicate_primary_key_rows += 1
            elif primary_key_value:
                seen_primary_keys.add(primary_key_value)

            for column_name in columns:
                raw_value = row.get(column_name, "")
                value = raw_value.strip()

                if is_null_like(value):
                    null_counts[column_name] += 1
                    continue

                counters[column_name][value] += 1

                if numeric_possible[column_name]:
                    try:
                        numeric_values[column_name].append(try_parse_float(value))
                    except ValueError:
                        numeric_possible[column_name] = False
                        numeric_values[column_name] = []

    numeric_columns = [
        column_name
        for column_name in columns
        if numeric_possible[column_name] and numeric_values[column_name]
    ]
    categorical_columns = [
        column_name
        for column_name in columns
        if column_name not in numeric_columns
    ]

    constant_columns: list[str] = []
    near_constant_columns: list[dict[str, Any]] = []
    columns_with_nulls: list[dict[str, Any]] = []
    numeric_profiles: dict[str, Any] = {}
    categorical_profiles: dict[str, Any] = {}

    for column_name in columns:
        non_null_count = sum(counters[column_name].values())
        distinct_count = len(counters[column_name])
        null_count = null_counts[column_name]
        null_ratio = (null_count / row_count) if row_count else 0.0

        if null_count > 0:
            columns_with_nulls.append(
                {
                    "column_name": column_name,
                    "null_count": null_count,
                    "null_ratio": round(null_ratio, 6),
                }
            )

        if distinct_count <= 1:
            constant_columns.append(column_name)

        if non_null_count > 0:
            dominant_value, dominant_count = counters[column_name].most_common(1)[0]
            dominant_share = dominant_count / non_null_count
            if dominant_share >= NEAR_CONSTANT_THRESHOLD:
                near_constant_columns.append(
                    {
                        "column_name": column_name,
                        "dominant_value": dominant_value,
                        "dominant_count": dominant_count,
                        "dominant_share": round(dominant_share, 6),
                    }
                )

        if column_name in numeric_columns:
            values = numeric_values[column_name]
            mean_value = sum(values) / len(values)
            std_value = population_std(values, mean_value)
            skew_value = skewness(values, mean_value, std_value)
            numeric_profiles[column_name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": round(mean_value, 6),
                "std": round(std_value, 6),
                "skewness": round(skew_value, 6),
            }
        else:
            categorical_profiles[column_name] = {
                "count": non_null_count,
                "distinct_count": distinct_count,
                "top_values": top_values(counters[column_name]),
            }

    high_skew_numeric_columns = [
        {
            "column_name": column_name,
            **profile,
        }
        for column_name, profile in numeric_profiles.items()
        if abs(profile["skewness"]) >= SKEWNESS_ALERT_THRESHOLD
    ]
    high_skew_numeric_columns.sort(key=lambda item: abs(item["skewness"]), reverse=True)

    columns_with_nulls.sort(key=lambda item: item["null_count"], reverse=True)
    near_constant_columns.sort(key=lambda item: item["dominant_share"], reverse=True)

    audit_created_at = datetime.now(timezone.utc)
    slug = timestamp_slug(common_config, audit_created_at)
    ensure_report_directories()
    audit_json_path = EXPERIMENT_REPORTS_DIR / f"{use_case_config['snapshot_prefix']}_audit_{slug}.json"
    audit_md_path = EXPERIMENT_REPORTS_DIR / f"{use_case_config['snapshot_prefix']}_audit_{slug}.md"

    audit_payload = {
        "audit_type": "serving_snapshot_feature_audit",
        "audit_created_at_utc": isoformat_utc(audit_created_at),
        "use_case": use_case_config["use_case"],
        "source_relation": f"{manifest['source']['schema_name']}.{manifest['source']['table_name']}",
        "manifest_path": str(manifest_path),
        "snapshot_path": str(snapshot_path),
        "dataset_overview": {
            "row_count": row_count,
            "column_count": len(columns),
            "numeric_column_count": len(numeric_columns),
            "categorical_column_count": len(categorical_columns),
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
        },
        "primary_key_checks": {
            "primary_key_column": primary_key_column,
            "duplicate_primary_key_rows": duplicate_primary_key_rows,
            "unique_primary_key_count": len(seen_primary_keys),
        },
        "feature_contract": {
            "candidate_feature_column_count": len(candidate_feature_columns),
            "candidate_feature_columns": candidate_feature_columns,
            "non_feature_column_count": len(non_feature_columns),
            "non_feature_columns": non_feature_columns,
            "reference_label_column_count": len(reference_label_columns),
            "reference_label_columns": reference_label_columns,
        },
        "data_quality": {
            "columns_with_nulls_count": len(columns_with_nulls),
            "columns_with_nulls": columns_with_nulls,
            "constant_columns": constant_columns,
            "near_constant_columns": near_constant_columns,
            "high_skew_numeric_columns": high_skew_numeric_columns,
        },
        "profiles": {
            "numeric": numeric_profiles,
            "categorical": categorical_profiles,
        },
    }

    with audit_json_path.open("w", encoding="utf-8") as handle:
        json.dump(audit_payload, handle, indent=2)
        handle.write("\n")

    audit_md_path.write_text(build_markdown_report(audit_payload), encoding="utf-8")

    print("=" * 80)
    print("CUSTOMERDNA AI - SERVING SNAPSHOT AUDIT")
    print("=" * 80)
    print(f"Use case: {use_case_config['use_case']}")
    print(f"Manifest: {manifest_path}")
    print(f"Snapshot: {snapshot_path}")
    print(f"Audit JSON: {audit_json_path}")
    print(f"Audit Markdown: {audit_md_path}")
    print(f"Rows audited: {row_count}")
    print(f"Numeric columns: {len(numeric_columns)}")
    print(f"Categorical columns: {len(categorical_columns)}")
    print(f"Duplicate primary key rows: {duplicate_primary_key_rows}")
    print(f"Columns with nulls: {len(columns_with_nulls)}")
    print(f"Constant columns: {len(constant_columns)}")
    print(f"Near-constant columns: {len(near_constant_columns)}")
    print(f"Highly skewed numeric columns: {len(high_skew_numeric_columns)}")
    print("Audit completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
