from __future__ import annotations

import argparse

from bootstrap_gx import bootstrap_gx_project, get_context
from gx_config import (
    ANALYTICS_CHECKPOINT_NAME,
    ML_CHECKPOINT_NAME,
    RAW_CHECKPOINT_NAME,
)


CHECKPOINT_OPTIONS = {
    "raw": RAW_CHECKPOINT_NAME,
    "analytics": ANALYTICS_CHECKPOINT_NAME,
    "ml": ML_CHECKPOINT_NAME,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run Great Expectations validations for CustomerDNA AI Client 1.",
    )
    parser.add_argument(
        "--checkpoint",
        choices=["raw", "analytics", "ml", "all"],
        default="all",
        help="Checkpoint group to run.",
    )
    parser.add_argument(
        "--skip-bootstrap",
        action="store_true",
        help="Use the existing GX context without refreshing assets, suites, and checkpoints first.",
    )
    return parser.parse_args()


def resolve_checkpoint_names(selection: str) -> list[str]:
    if selection == "all":
        return [
            RAW_CHECKPOINT_NAME,
            ANALYTICS_CHECKPOINT_NAME,
            ML_CHECKPOINT_NAME,
        ]
    return [CHECKPOINT_OPTIONS[selection]]


def print_checkpoint_result(name: str, result) -> None:
    run_results = getattr(result, "run_results", {}) or {}
    print(f"[CHECKPOINT] {name}")
    print(f"  Success: {getattr(result, 'success', 'unknown')}")
    print(f"  Validation results: {len(run_results)}")


def main() -> None:
    args = parse_args()

    if args.skip_bootstrap:
        context = get_context()
    else:
        context, _ = bootstrap_gx_project()

    checkpoint_names = resolve_checkpoint_names(args.checkpoint)

    print("=" * 80)
    print("CUSTOMERDNA AI - GREAT EXPECTATIONS VALIDATION RUN")
    print("=" * 80)

    for checkpoint_name in checkpoint_names:
        checkpoint = context.checkpoints.get(checkpoint_name)
        result = checkpoint.run()
        print_checkpoint_result(checkpoint_name, result)

    data_docs_sites = context.build_data_docs()
    if data_docs_sites:
        print()
        print("Data Docs:")
        for site_name, site_location in data_docs_sites.items():
            print(f"  - {site_name}: {site_location}")

    print("=" * 80)


if __name__ == "__main__":
    main()
