from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

from bootstrap_gx import bootstrap_gx_project, get_context
from gx_config import (
    ANALYTICS_CHECKPOINT_NAME,
    ML_CHECKPOINT_NAME,
    RAW_CHECKPOINT_NAME,
    SERVING_CHECKPOINT_NAME,
)

MONITORING_SRC_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "monitoring")
)
if MONITORING_SRC_DIR not in sys.path:
    sys.path.append(MONITORING_SRC_DIR)

try:
    from shared.pipeline_metrics import record_gx_checkpoint_run
except Exception:
    record_gx_checkpoint_run = None

CHECKPOINT_OPTIONS = {
    "raw": RAW_CHECKPOINT_NAME,
    "analytics": ANALYTICS_CHECKPOINT_NAME,
    "serving": SERVING_CHECKPOINT_NAME,
    "ml": ML_CHECKPOINT_NAME,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run Great Expectations validations for CustomerDNA AI Client 1.",
    )
    parser.add_argument(
        "--checkpoint",
        choices=["raw", "analytics", "serving", "ml", "all"],
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
            SERVING_CHECKPOINT_NAME,
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
        checkpoint_started_at = datetime.now(timezone.utc)
        try:
            checkpoint = context.checkpoints.get(checkpoint_name)
            result = checkpoint.run()
            checkpoint_ended_at = datetime.now(timezone.utc)
            run_results = getattr(result, "run_results", {}) or {}
            checkpoint_status = "success" if getattr(result, "success", False) else "failed"

            if record_gx_checkpoint_run:
                monitoring_recorded = record_gx_checkpoint_run(
                    {
                        "checkpoint_name": checkpoint_name,
                        "status": checkpoint_status,
                        "started_at": checkpoint_started_at.isoformat(),
                        "ended_at": checkpoint_ended_at.isoformat(),
                        "duration_seconds": round(
                            (checkpoint_ended_at - checkpoint_started_at).total_seconds(),
                            3,
                        ),
                        "validation_results": len(run_results),
                    }
                )
                print(
                    f"[MONITORING] GX checkpoint state recorded for {checkpoint_name}"
                    if monitoring_recorded
                    else f"[MONITORING] GX checkpoint state recording failed for {checkpoint_name}"
                )
            else:
                print(f"[MONITORING] GX checkpoint writer unavailable for {checkpoint_name}")

            print_checkpoint_result(checkpoint_name, result)
        except Exception:
            checkpoint_ended_at = datetime.now(timezone.utc)
            if record_gx_checkpoint_run:
                monitoring_recorded = record_gx_checkpoint_run(
                    {
                        "checkpoint_name": checkpoint_name,
                        "status": "failed",
                        "started_at": checkpoint_started_at.isoformat(),
                        "ended_at": checkpoint_ended_at.isoformat(),
                        "duration_seconds": round(
                            (checkpoint_ended_at - checkpoint_started_at).total_seconds(),
                            3,
                        ),
                        "validation_results": 0,
                    }
                )
                print(
                    f"[MONITORING] GX failure state recorded for {checkpoint_name}"
                    if monitoring_recorded
                    else f"[MONITORING] GX failure state recording failed for {checkpoint_name}"
                )
            raise

    data_docs_sites = context.build_data_docs()
    if data_docs_sites:
        print()
        print("Data Docs:")
        for site_name, site_location in data_docs_sites.items():
            print(f"  - {site_name}: {site_location}")

    print("=" * 80)


if __name__ == "__main__":
    main()
