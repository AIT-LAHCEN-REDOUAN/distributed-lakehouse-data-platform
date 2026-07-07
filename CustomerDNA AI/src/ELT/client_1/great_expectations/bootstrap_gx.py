from __future__ import annotations

import argparse
from typing import Dict, Iterable, Tuple

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
    SERVING_CHECKPOINT_NAME,
    SERVING_VALIDATION_NAMES,
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bootstrap Great Expectations assets for CustomerDNA AI Client 1.",
    )
    parser.add_argument(
        "--layers",
        choices=["raw", "analytics", "serving", "all"],
        default="all",
        help="Restrict bootstrap to a specific logical layer.",
    )
    return parser.parse_args()


def get_context():
    return gx.get_context(mode="file", project_root_dir=str(GX_PROJECT_DIR))


def ensure_datasource(context):
    return context.data_sources.add_or_update_postgres(
        name=DATASOURCE_NAME,
        connection_string=build_connection_string(),
    )


def resolve_asset_configs(layer_selection: str) -> list[dict]:
    if layer_selection == "all":
        return ASSET_CONFIGS
    return [config for config in ASSET_CONFIGS if config["layer"] == layer_selection]


def resolve_checkpoint_names(layer_selection: str) -> list[str]:
    if layer_selection == "raw":
        return [RAW_CHECKPOINT_NAME]
    if layer_selection == "analytics":
        return [ANALYTICS_CHECKPOINT_NAME]
    if layer_selection == "serving":
        return [SERVING_CHECKPOINT_NAME, ML_CHECKPOINT_NAME]
    return [RAW_CHECKPOINT_NAME, ANALYTICS_CHECKPOINT_NAME, SERVING_CHECKPOINT_NAME, ML_CHECKPOINT_NAME]


def resolve_validation_names_for_checkpoint(checkpoint_name: str) -> list[str]:
    if checkpoint_name == RAW_CHECKPOINT_NAME:
        return RAW_VALIDATION_NAMES
    if checkpoint_name == ANALYTICS_CHECKPOINT_NAME:
        return ANALYTICS_VALIDATION_NAMES
    if checkpoint_name == SERVING_CHECKPOINT_NAME:
        return SERVING_VALIDATION_NAMES
    if checkpoint_name == ML_CHECKPOINT_NAME:
        return ML_VALIDATION_NAMES
    return []


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


def ensure_validation_definitions(context, suites: Dict[str, ExpectationSuite], datasource, asset_configs: Iterable[dict]):
    persisted = {}

    for asset_config in asset_configs:
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


def ensure_checkpoints(context, validations: Dict[str, ValidationDefinition], checkpoint_names: Iterable[str]):
    actions = [UpdateDataDocsAction(name=DATA_DOCS_ACTION_NAME)]
    persisted = {}

    for checkpoint_name in checkpoint_names:
        validation_names = resolve_validation_names_for_checkpoint(checkpoint_name)
        available_validations = [
            validations[name]
            for name in validation_names
            if name in validations
        ]

        if not available_validations:
            continue

        checkpoint = Checkpoint(
            name=checkpoint_name,
            validation_definitions=available_validations,
            actions=actions,
            result_format="SUMMARY",
        )
        persisted[checkpoint_name] = context.checkpoints.add_or_update(checkpoint)

    return persisted


def bootstrap_gx_project(layer_selection: str = "all") -> Tuple[object, dict]:
    context = get_context()
    datasource = ensure_datasource(context)
    suites = ensure_suites(context)
    asset_configs = resolve_asset_configs(layer_selection)
    validations = ensure_validation_definitions(context, suites, datasource, asset_configs)
    checkpoints = ensure_checkpoints(context, validations, resolve_checkpoint_names(layer_selection))
    return context, checkpoints


def print_summary(context, checkpoints: dict, layer_selection: str) -> None:
    print("=" * 80)
    print("CUSTOMERDNA AI - GREAT EXPECTATIONS BOOTSTRAP COMPLETE")
    print("=" * 80)
    print(describe_project())
    print()
    print(f"Context root: {context.root_directory}")
    print(f"Datasource: {DATASOURCE_NAME}")
    print(f"Bootstrap scope: {layer_selection}")
    print()
    print("Checkpoints:")
    for name in checkpoints:
        print(f"  - {name}")
    print()
    print("Next recommended runs:")
    print("  1. python bootstrap_gx.py")
    print("  2. python run_gx_validations.py --checkpoint raw")
    print("  3. python run_gx_validations.py --checkpoint analytics")
    print("  4. python run_gx_validations.py --checkpoint serving")
    print("  5. python run_gx_validations.py --checkpoint ml")
    print("=" * 80)


def main() -> None:
    args = parse_args()
    context, checkpoints = bootstrap_gx_project(layer_selection=args.layers)
    print_summary(context, checkpoints, args.layers)


if __name__ == "__main__":
    main()