from __future__ import annotations

from typing import Dict, Tuple

import great_expectations as gx
from great_expectations.checkpoint import Checkpoint
from great_expectations.checkpoint.actions import UpdateDataDocsAction
from great_expectations.core.batch_definition import BatchDefinition
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.validation_definition import ValidationDefinition
from great_expectations.datasource.fluent.sql_datasource import TableAsset

from gx_config import (
    ANALYTICS_CHECKPOINT_NAME,
    ANALYTICS_VALIDATION_NAMES,
    ASSET_CONFIGS,
    DATA_DOCS_ACTION_NAME,
    DATASOURCE_NAME,
    GX_PROJECT_DIR,
    ML_CHECKPOINT_NAME,
    ML_VALIDATION_NAMES,
    RAW_CHECKPOINT_NAME,
    RAW_VALIDATION_NAMES,
    build_connection_string,
    describe_project,
)
from gx_suite_definitions import build_all_suites


def get_context():
    return gx.get_context(mode="file", project_root_dir=str(GX_PROJECT_DIR))


def ensure_datasource(context):
    return context.data_sources.add_or_update_postgres(
        name=DATASOURCE_NAME,
        connection_string=build_connection_string(),
    )


def ensure_table_asset(datasource, asset_config: dict) -> TableAsset:
    asset_name = asset_config["asset_name"]

    if asset_name in datasource.get_asset_names():
        asset = datasource.get_asset(asset_name)
        if (
            getattr(asset, "table_name", None) != asset_config["table_name"]
            or getattr(asset, "schema_name", None) != asset_config["schema_name"]
        ):
            datasource.delete_asset(asset_name)
            asset = datasource.add_table_asset(
                name=asset_name,
                table_name=asset_config["table_name"],
                schema_name=asset_config["schema_name"],
            )
    else:
        asset = datasource.add_table_asset(
            name=asset_name,
            table_name=asset_config["table_name"],
            schema_name=asset_config["schema_name"],
        )

    return asset


def ensure_batch_definition(asset: TableAsset, batch_definition_name: str) -> BatchDefinition:
    try:
        return asset.get_batch_definition(batch_definition_name)
    except Exception:
        return asset.add_batch_definition_whole_table(batch_definition_name)


def ensure_suites(context) -> Dict[str, ExpectationSuite]:
    suites = build_all_suites()
    persisted = {}
    for suite in suites.values():
        persisted[suite.name] = context.suites.add_or_update(suite)
    return persisted


def ensure_validation_definitions(context, suites: Dict[str, ExpectationSuite], datasource):
    persisted = {}

    for asset_config in ASSET_CONFIGS:
        asset = ensure_table_asset(datasource, asset_config)
        batch_definition = ensure_batch_definition(asset, asset_config["batch_definition_name"])
        suite = suites[asset_config["suite_name"]]

        validation = ValidationDefinition(
            name=asset_config["validation_name"],
            data=batch_definition,
            suite=suite,
        )
        persisted[validation.name] = context.validation_definitions.add_or_update(validation)

    return persisted


def ensure_checkpoints(context, validations: Dict[str, ValidationDefinition]):
    actions = [UpdateDataDocsAction(name=DATA_DOCS_ACTION_NAME)]

    raw_checkpoint = Checkpoint(
        name=RAW_CHECKPOINT_NAME,
        validation_definitions=[validations[name] for name in RAW_VALIDATION_NAMES],
        actions=actions,
        result_format="SUMMARY",
    )
    analytics_checkpoint = Checkpoint(
        name=ANALYTICS_CHECKPOINT_NAME,
        validation_definitions=[validations[name] for name in ANALYTICS_VALIDATION_NAMES],
        actions=actions,
        result_format="SUMMARY",
    )
    ml_checkpoint = Checkpoint(
        name=ML_CHECKPOINT_NAME,
        validation_definitions=[validations[name] for name in ML_VALIDATION_NAMES],
        actions=actions,
        result_format="SUMMARY",
    )

    return {
        RAW_CHECKPOINT_NAME: context.checkpoints.add_or_update(raw_checkpoint),
        ANALYTICS_CHECKPOINT_NAME: context.checkpoints.add_or_update(analytics_checkpoint),
        ML_CHECKPOINT_NAME: context.checkpoints.add_or_update(ml_checkpoint),
    }


def bootstrap_gx_project() -> Tuple[object, dict]:
    context = get_context()
    datasource = ensure_datasource(context)
    suites = ensure_suites(context)
    validations = ensure_validation_definitions(context, suites, datasource)
    checkpoints = ensure_checkpoints(context, validations)
    return context, checkpoints


def print_summary(context, checkpoints: dict) -> None:
    print("=" * 80)
    print("CUSTOMERDNA AI - GREAT EXPECTATIONS BOOTSTRAP COMPLETE")
    print("=" * 80)
    print(describe_project())
    print()
    print(f"Context root: {context.root_directory}")
    print(f"Datasource: {DATASOURCE_NAME}")
    print()
    print("Checkpoints:")
    for name in checkpoints:
        print(f"  - {name}")
    print()
    print("Next recommended runs:")
    print("  1. python bootstrap_gx.py")
    print("  2. python run_gx_validations.py --checkpoint raw")
    print("  3. python run_gx_validations.py --checkpoint analytics")
    print("  4. python run_gx_validations.py --checkpoint ml")
    print("=" * 80)


def main() -> None:
    context, checkpoints = bootstrap_gx_project()
    print_summary(context, checkpoints)


if __name__ == "__main__":
    main()
