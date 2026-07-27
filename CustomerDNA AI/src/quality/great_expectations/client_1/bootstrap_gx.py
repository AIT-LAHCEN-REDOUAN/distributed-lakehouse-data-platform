"""Bootstrap lightweight Client 1 data-quality assets for the current architecture."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite


QUALITY_ROOT = Path(__file__).resolve().parent
SRC_ROOT = QUALITY_ROOT.parents[2]
KAFKA_COMMON_ROOT = SRC_ROOT / "streaming" / "kafka" / "client_1" / "common"
CHECKPOINTS_DIR = QUALITY_ROOT / "checkpoints"
DATA_DOCS_DIR = QUALITY_ROOT / "data_docs"
ARTIFACTS_DIR = QUALITY_ROOT / "artifacts"
GX_PROJECT_ROOT = QUALITY_ROOT / "gx_project"

DATASOURCE_NAME = "client1_quality_metrics"
ASSET_NAME = "raw_lakehouse_metrics"
BATCH_DEFINITION_NAME = "default"
SUITE_NAME = "raw_lakehouse_metrics_suite"
CHECKPOINT_NAME = "raw_lakehouse_quality_checkpoint"

if str(KAFKA_COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(KAFKA_COMMON_ROOT))

from kafka_config import DATASET_ORDER  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap Client 1 quality-check assets."
    )
    parser.add_argument(
        "--layers",
        default="raw",
        choices=["raw", "all"],
        help="Scope of quality assets to prepare.",
    )
    return parser.parse_args()


def ensure_directories() -> None:
    for directory in (CHECKPOINTS_DIR, DATA_DOCS_DIR, ARTIFACTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


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


def _ensure_expectation_suite(context: gx.DataContext) -> None:
    batch_df = pd.DataFrame(
        [
            {
                "dataset_key": "bootstrap",
                "target_table": "bootstrap",
                "row_count": 1,
                "column_count": 1,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
    )
    asset = _ensure_pandas_asset(context)
    try:
        context.suites.get(SUITE_NAME)
    except Exception:
        context.suites.add(ExpectationSuite(name=SUITE_NAME))

    batch_request = asset.build_batch_request(options={"dataframe": batch_df})
    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=SUITE_NAME,
    )
    validator.expect_column_values_to_be_between("row_count", min_value=1)
    validator.expect_column_values_to_be_between("column_count", min_value=1)
    context.suites.add_or_update(
        validator.get_expectation_suite(discard_failed_expectations=False)
    )


def _ensure_validation_definitions(context: gx.DataContext) -> None:
    asset = _ensure_pandas_asset(context)
    batch_definition = asset.get_batch_definition(BATCH_DEFINITION_NAME)
    suite = context.suites.get(SUITE_NAME)

    for dataset_key in DATASET_ORDER:
        definition_name = f"{CHECKPOINT_NAME}__{dataset_key}"
        try:
            context.validation_definitions.get(definition_name)
        except Exception:
            context.validation_definitions.add(
                gx.ValidationDefinition(
                    data=batch_definition,
                    suite=suite,
                    name=definition_name,
                )
            )


def write_checkpoint_manifest(layers: str) -> list[str]:
    checkpoints = ["raw_lakehouse_quality_checkpoint"]
    if layers == "all":
        checkpoints.append("platform_readiness_checkpoint")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": layers,
        "checkpoints": checkpoints,
    }
    (CHECKPOINTS_DIR / "checkpoint_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return checkpoints


def write_data_docs_placeholder(checkpoints: list[str]) -> None:
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CustomerDNA Quality Docs</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
    h1 {{ color: #1f2937; }}
    code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>CustomerDNA Client 1 Lakehouse Quality Assets</h1>
  <p>This environment includes a Great Expectations project (GX Core) used to generate validation artifacts and HTML Data Docs for reporting.</p>
  <p>Available checkpoints:</p>
  <ul>
    {''.join(f'<li><code>{checkpoint}</code></li>' for checkpoint in checkpoints)}
  </ul>
  <p><strong>GX project root:</strong> <code>{GX_PROJECT_ROOT.as_posix()}</code></p>
  <p>To view Data Docs after running validations, open the generated site under the GX project folder:</p>
  <ul>
    <li><code>gx_project/gx/uncommitted/data_docs/local_site/index.html</code></li>
  </ul>
</body>
</html>
"""
    (DATA_DOCS_DIR / "index.html").write_text(html_content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    ensure_directories()
    context = _get_or_create_context()
    _ensure_expectation_suite(context)
    _ensure_validation_definitions(context)
    checkpoints = write_checkpoint_manifest(args.layers)
    write_data_docs_placeholder(checkpoints)

    print("=" * 80)
    print("CUSTOMERDNA AI - CLIENT 1 QUALITY BOOTSTRAP")
    print("=" * 80)
    print(f"Scope: {args.layers}")
    print("Prepared checkpoints:")
    for checkpoint in checkpoints:
        print(f"  - {checkpoint}")
    print(f"Data docs placeholder: {DATA_DOCS_DIR / 'index.html'}")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
