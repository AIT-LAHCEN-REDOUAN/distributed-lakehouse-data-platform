"""Run lightweight Client 1 lakehouse quality validations and persist monitoring state."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import great_expectations as gx

from bootstrap_gx import _ensure_expectation_suite, _ensure_validation_definitions


QUALITY_ROOT = Path(__file__).resolve().parent
SRC_ROOT = QUALITY_ROOT.parents[2]
KAFKA_COMMON_ROOT = SRC_ROOT / "streaming" / "kafka" / "client_1" / "common"
MONITORING_ROOT = SRC_ROOT / "monitoring"
TRINO_COMMON_ROOT = SRC_ROOT / "query" / "trino" / "client_1" / "common"
ARTIFACTS_DIR = QUALITY_ROOT / "artifacts"
GX_PROJECT_ROOT = QUALITY_ROOT / "gx_project"

DATASOURCE_NAME = "client1_quality_metrics"
ASSET_NAME = "raw_lakehouse_metrics"
BATCH_DEFINITION_NAME = "default"
SUITE_NAME = "raw_lakehouse_metrics_suite"
CHECKPOINT_NAME = "raw_lakehouse_quality_checkpoint"

for import_root in (KAFKA_COMMON_ROOT, MONITORING_ROOT, TRINO_COMMON_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from kafka_config import DATASET_ORDER, get_dataset_config  # noqa: E402
from shared.pipeline_metrics import record_gx_checkpoint_run  # noqa: E402
from trino_rest import TRINO_CATALOG, TRINO_SCHEMA, execute_trino_statement  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Client 1 lightweight lakehouse quality validations."
    )
    parser.add_argument(
        "--checkpoint",
        required=True,
        choices=["raw"],
        help="Checkpoint name to validate.",
    )
    parser.add_argument(
        "--skip-bootstrap",
        action="store_true",
        help="Accepted for compatibility with the Airflow workflow.",
    )
    return parser.parse_args()


def query_row_count(table_name: str) -> int:
    result = execute_trino_statement(
        f"SELECT COUNT(*) AS row_count FROM {TRINO_CATALOG}.{TRINO_SCHEMA}.{table_name}"
    )
    if not result["rows"]:
        raise RuntimeError(f"Trino returned no rows while validating table '{table_name}'.")
    return int(result["rows"][0][0])


def query_column_count(table_name: str) -> int:
    result = execute_trino_statement(
        f"SHOW COLUMNS FROM {TRINO_CATALOG}.{TRINO_SCHEMA}.{table_name}"
    )
    return len(result.get("rows", []))


def _get_or_create_context() -> gx.DataContext:
    GX_PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    return gx.get_context(project_root_dir=str(GX_PROJECT_ROOT))


def _ensure_pandas_asset(context: gx.DataContext) -> object:
    try:
        datasource = context.data_sources.get(DATASOURCE_NAME)
    except Exception:
        datasource = context.data_sources.add_pandas(name=DATASOURCE_NAME)

    try:
        asset = datasource.get_asset(ASSET_NAME)
    except Exception:
        asset = datasource.add_dataframe_asset(name=ASSET_NAME)

    try:
        asset.get_batch_definition(BATCH_DEFINITION_NAME)
    except Exception:
        asset.add_batch_definition_whole_dataframe(BATCH_DEFINITION_NAME)

    return asset


def run_raw_checkpoint() -> dict[str, object]:
    started_at = datetime.now(timezone.utc)
    validations: list[dict[str, object]] = []

    context = _get_or_create_context()
    asset = _ensure_pandas_asset(context)
    _ensure_expectation_suite(context)
    _ensure_validation_definitions(context)
    try:
        suite = context.suites.get(SUITE_NAME)
    except Exception as exc:
        raise RuntimeError(
            f"Expectation suite '{SUITE_NAME}' is missing. Run bootstrap_gx.py before validations."
        ) from exc

    batch_definition = asset.get_batch_definition(BATCH_DEFINITION_NAME)

    for dataset_key in DATASET_ORDER:
        target_table = str(get_dataset_config(dataset_key)["target_table"])
        row_count = query_row_count(target_table)
        column_count = query_column_count(target_table)
        batch_df = pd.DataFrame(
            [
                {
                    "dataset_key": dataset_key,
                    "target_table": f"{TRINO_SCHEMA}.{target_table}",
                    "row_count": row_count,
                    "column_count": column_count,
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                }
            ]
        )
        definition_name = f"{CHECKPOINT_NAME}__{dataset_key}"
        try:
            validation_definition = context.validation_definitions.get(definition_name)
        except Exception:
            validation_definition = context.validation_definitions.add(
                gx.ValidationDefinition(
                    data=batch_definition,
                    suite=suite,
                    name=definition_name,
                )
            )

        validation_result = validation_definition.run(
            batch_parameters={"dataframe": batch_df},
        )
        validation_success = bool(getattr(validation_result, "success", False))
        validations.append(
            {
                "dataset_key": dataset_key,
                "target_table": f"{TRINO_SCHEMA}.{target_table}",
                "row_count": row_count,
                "column_count": column_count,
                "success": validation_success,
                "validation_definition": definition_name,
            }
        )

    ended_at = datetime.now(timezone.utc)
    context.build_data_docs()
    overall_success = all(bool(item["success"]) for item in validations)
    return {
        "checkpoint_name": CHECKPOINT_NAME,
        "status": "success" if overall_success else "failed",
        "success": overall_success,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_seconds": round((ended_at - started_at).total_seconds(), 3),
        "validation_count": len(validations),
        "validation_results": len(validations),
        "validations": validations,
    }


def persist_artifact(summary: dict[str, object]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = ARTIFACTS_DIR / f"{summary['checkpoint_name']}_latest.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return output_path


def main() -> int:
    args = parse_args()

    if args.checkpoint != "raw":
        raise RuntimeError(f"Unsupported checkpoint: {args.checkpoint}")

    start_counter = time.perf_counter()
    summary = run_raw_checkpoint()
    summary["duration_seconds"] = round(time.perf_counter() - start_counter, 3)
    artifact_path = persist_artifact(summary)
    monitoring_recorded = record_gx_checkpoint_run(summary)

    print("=" * 80)
    print("CUSTOMERDNA AI - CLIENT 1 LAKEHOUSE QUALITY VALIDATION")
    print("=" * 80)
    print(f"Checkpoint: {summary['checkpoint_name']}")
    print(f"Success: {summary['success']}")
    print(f"Validation results: {summary['validation_count']}")
    print(f"Artifact: {artifact_path}")
    print(f"Monitoring recorded: {monitoring_recorded}")
    print("=" * 80)

    return 0 if summary["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
