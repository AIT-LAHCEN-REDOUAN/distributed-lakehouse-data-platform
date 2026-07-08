"""Run the Client 1 Kafka-backed raw loading pipeline from clean topics."""

from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


CLIENT_KAFKA_ROOT = Path(__file__).resolve().parent
SRC_ROOT = CLIENT_KAFKA_ROOT.parents[2]
MONITORING_ROOT = SRC_ROOT / "monitoring"

if str(MONITORING_ROOT) not in sys.path:
    sys.path.insert(0, str(MONITORING_ROOT))

from shared.pipeline_metrics import record_raw_load_run  # noqa: E402


ROWS_LOADED_PATTERN = re.compile(r"Rows loaded:\s*([0-9,]+)")
DURATION_PATTERN = re.compile(r"Duration \(seconds\):\s*([0-9]+(?:\.[0-9]+)?)")


@dataclass(frozen=True)
class DatasetPipelineStep:
    """Define one dataset's Kafka producer and raw loader sequence."""

    dataset_key: str
    relative_dir: str
    target_table: str

    @property
    def dataset_dir(self) -> Path:
        return CLIENT_KAFKA_ROOT / self.relative_dir

    @property
    def producer_script(self) -> Path:
        return self.dataset_dir / "produce.py"

    @property
    def loader_script(self) -> Path:
        return self.dataset_dir / "load_to_raw.py"


@dataclass(frozen=True)
class ScriptRunResult:
    """Store subprocess text output for later parsing."""

    stdout: str
    stderr: str


DATASET_STEPS = [
    DatasetPipelineStep("retailrocket_category_tree", "retailrocket_category_tree", "category_tree"),
    DatasetPipelineStep("marketing_campaign", "marketing_campaign", "marketing_campaign"),
    DatasetPipelineStep(
        "ecommerce_customer_churn",
        "ecommerce_customer_churn",
        "e_commerce_customer_churn",
    ),
    DatasetPipelineStep("online_retail", "online_retail", "online_retail"),
    DatasetPipelineStep("retailrocket_events", "retailrocket_events", "events"),
    DatasetPipelineStep(
        "retailrocket_item_properties",
        "retailrocket_item_properties",
        "item_properties",
    ),
]


def run_script(script_path: Path, task_label: str) -> ScriptRunResult:
    """Run a Python script and fail immediately if it exits unsuccessfully."""
    print("-" * 80)
    print(f"[TASK] {task_label}")
    print(f"[SCRIPT] {script_path}")

    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(script_path.parent),
        check=True,
        capture_output=True,
        text=True,
    )
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", file=sys.stderr)
    return ScriptRunResult(stdout=completed.stdout, stderr=completed.stderr)


def extract_rows_loaded(stdout: str) -> int:
    """Parse the loader's final row-count line."""
    match = ROWS_LOADED_PATTERN.search(stdout)
    if not match:
        raise RuntimeError("Unable to parse 'Rows loaded' from loader output.")
    return int(match.group(1).replace(",", ""))


def extract_duration_seconds(stdout: str) -> float | None:
    """Parse the loader's reported duration if present."""
    match = DURATION_PATTERN.search(stdout)
    if not match:
        return None
    return float(match.group(1))


def build_raw_load_summary(
    *,
    status: str,
    started_at: datetime,
    ended_at: datetime,
    tables: list[dict[str, object]],
) -> dict[str, object]:
    """Build a monitoring summary for the entire Client 1 raw-load run."""
    total_rows_inserted = sum(int(table.get("rows_inserted", 0)) for table in tables)
    successful_files = sum(1 for table in tables if table.get("status") == "success")
    failed_files = sum(1 for table in tables if table.get("status") != "success")
    return {
        "status": status,
        "started_at": started_at.astimezone(timezone.utc).isoformat(),
        "ended_at": ended_at.astimezone(timezone.utc).isoformat(),
        "duration_seconds": round(max((ended_at - started_at).total_seconds(), 0.0), 3),
        "total_rows_inserted": total_rows_inserted,
        "successful_files": successful_files,
        "failed_files": failed_files,
        "skipped_files": 0,
        "refreshed_files": successful_files,
        "incremental_files": 0,
        "tables": tables,
    }


def main() -> int:
    """Execute the Kafka raw pipeline from topic reset to raw table load."""
    started_at = datetime.now(timezone.utc)
    start_counter = time.perf_counter()
    table_summaries: list[dict[str, object]] = []

    print("=" * 80)
    print("CUSTOMERDNA AI - CLIENT 1 KAFKA RAW PIPELINE")
    print("=" * 80)
    print("Mode: batch-through-Kafka")
    print("Flow: reset topics -> produce dataset -> load dataset into raw_data")
    print("Dataset order: small datasets first, largest datasets last")
    print("=" * 80)

    try:
        run_script(
            CLIENT_KAFKA_ROOT / "reset_client1_kafka.py",
            "Reset Client 1 Kafka topics and local artifacts",
        )

        for step in DATASET_STEPS:
            run_script(step.producer_script, f"Publish {step.dataset_key} into Kafka")
            loader_result = run_script(
                step.loader_script,
                f"Load {step.dataset_key} from Kafka into raw_data",
            )
            rows_loaded = extract_rows_loaded(loader_result.stdout)
            load_duration = extract_duration_seconds(loader_result.stdout)
            table_summaries.append(
                {
                    "table_name": step.target_table,
                    "load_mode": "full_refresh_from_kafka",
                    "status": "success",
                    "rows_inserted": rows_loaded,
                    "source_rows": rows_loaded,
                    "duration_seconds": load_duration,
                }
            )

        ended_at = datetime.now(timezone.utc)
        duration_seconds = round(time.perf_counter() - start_counter, 3)
        record_raw_load_run(
            build_raw_load_summary(
                status="success",
                started_at=started_at,
                ended_at=ended_at,
                tables=table_summaries,
            )
        )
        print("=" * 80)
        print("[SUCCESS] Client 1 Kafka raw pipeline completed successfully.")
        print(f"[DURATION] {duration_seconds} seconds")
        print("=" * 80)
        return 0
    except subprocess.CalledProcessError as exc:
        ended_at = datetime.now(timezone.utc)
        duration_seconds = round(time.perf_counter() - start_counter, 3)
        failed_step_name = "unknown"
        if exc.cmd:
            failed_step_name = Path(str(exc.cmd[-1])).parent.name
        table_summaries.append(
            {
                "table_name": failed_step_name,
                "load_mode": "full_refresh_from_kafka",
                "status": "failed",
                "rows_inserted": 0,
                "source_rows": 0,
                "duration_seconds": None,
            }
        )
        record_raw_load_run(
            build_raw_load_summary(
                status="failed",
                started_at=started_at,
                ended_at=ended_at,
                tables=table_summaries,
            )
        )
        print("=" * 80)
        print(f"[ERROR] Kafka raw pipeline failed while running: {exc.cmd}")
        print(f"[DURATION] {duration_seconds} seconds")
        print("=" * 80)
        return exc.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
