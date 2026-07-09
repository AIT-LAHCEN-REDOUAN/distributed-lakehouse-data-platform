"""Run the Client 1 Kafka -> MinIO bronze -> PostgreSQL raw pipeline."""

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
CLIENT_MINIO_ROOT = SRC_ROOT / "lake" / "minio" / "client_1"

if str(MONITORING_ROOT) not in sys.path:
    sys.path.insert(0, str(MONITORING_ROOT))

from shared.pipeline_metrics import record_raw_load_run  # noqa: E402

COMMON_DIR = CLIENT_KAFKA_ROOT / "common"
if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from kafka_config import DATASET_ORDER, get_dataset_config  # noqa: E402


ROWS_LOADED_PATTERN = re.compile(r"Rows loaded:\s*([0-9,]+)")
DURATION_PATTERN = re.compile(r"Duration \(seconds\):\s*([0-9]+(?:\.[0-9]+)?)")


@dataclass(frozen=True)
class DatasetPipelineStep:
    """Define one dataset's produce -> bronze -> raw loading sequence."""

    dataset_key: str

    @property
    def dataset_dir(self) -> Path:
        return CLIENT_KAFKA_ROOT / self.dataset_key

    @property
    def producer_script(self) -> Path:
        return self.dataset_dir / "produce.py"

    @property
    def bronze_consumer_script(self) -> Path:
        return self.dataset_dir / "consume.py"

    @property
    def load_event_script(self) -> Path:
        return self.dataset_dir / "load.py"

    @property
    def target_table(self) -> str:
        return str(get_dataset_config(self.dataset_key)["target_table"])


@dataclass(frozen=True)
class ScriptRunResult:
    """Store subprocess text output for later parsing."""

    stdout: str
    stderr: str


DATASET_STEPS = [DatasetPipelineStep(dataset_key) for dataset_key in DATASET_ORDER]


def run_script(command: list[str], cwd: Path, task_label: str) -> ScriptRunResult:
    """Run one subprocess step and surface its full stdout/stderr."""
    print("-" * 80)
    print(f"[TASK] {task_label}")
    print(f"[SCRIPT] {' '.join(command)}")

    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout, end="" if exc.stdout.endswith("\n") else "\n")
        if exc.stderr:
            print(exc.stderr, end="" if exc.stderr.endswith("\n") else "\n", file=sys.stderr)
        raise

    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", file=sys.stderr)
    return ScriptRunResult(stdout=completed.stdout, stderr=completed.stderr)


def extract_rows_loaded(stdout: str) -> int:
    """Parse the loader's final row-count line."""
    match = ROWS_LOADED_PATTERN.search(stdout)
    if not match:
        raise RuntimeError("Unable to parse 'Rows loaded' from bronze loader output.")
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


def record_pipeline_state(
    *,
    status: str,
    started_at: datetime,
    ended_at: datetime,
    table_summaries: list[dict[str, object]],
    success_message: str,
    failure_message: str,
) -> None:
    monitoring_recorded = record_raw_load_run(
        build_raw_load_summary(
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            tables=table_summaries,
        )
    )
    print(success_message if monitoring_recorded else failure_message)


def main() -> int:
    """Execute the full raw pipeline from clean Kafka topics to raw_data tables."""
    started_at = datetime.now(timezone.utc)
    start_counter = time.perf_counter()
    table_summaries: list[dict[str, object]] = []

    print("=" * 80)
    print("CUSTOMERDNA AI - CLIENT 1 KAFKA RAW PIPELINE")
    print("=" * 80)
    print("Mode: source -> Kafka -> MinIO bronze -> Kafka bronze-ready event -> PostgreSQL raw_data")
    print("Flow: reset Kafka -> reset bronze -> produce -> consume to bronze -> publish load event -> consume load event")
    print("Dataset order: small datasets first, largest datasets last")
    print("=" * 80)

    try:
        run_script(
            [sys.executable, str(CLIENT_KAFKA_ROOT / "reset_client1_kafka.py")],
            CLIENT_KAFKA_ROOT,
            "Reset Client 1 Kafka topics and local Kafka artifacts",
        )
        run_script(
            [sys.executable, str(CLIENT_MINIO_ROOT / "reset_client1_bronze.py")],
            CLIENT_MINIO_ROOT,
            "Reset Client 1 MinIO bronze objects",
        )

        for step in DATASET_STEPS:
            try:
                run_script(
                    [sys.executable, str(step.producer_script)],
                    step.dataset_dir,
                    f"Publish {step.dataset_key} into Kafka",
                )
                run_script(
                    [sys.executable, str(step.bronze_consumer_script)],
                    step.dataset_dir,
                    f"Consume {step.dataset_key} from Kafka into MinIO bronze",
                )
                loader_result = run_script(
                    [sys.executable, str(step.load_event_script)],
                    step.dataset_dir,
                    f"Consume {step.dataset_key} bronze-ready event and load raw_data",
                )
                rows_loaded = extract_rows_loaded(loader_result.stdout)
                load_duration = extract_duration_seconds(loader_result.stdout)
                table_summaries.append(
                    {
                        "table_name": step.target_table,
                        "load_mode": "kafka_bronze_ready_event",
                        "status": "success",
                        "rows_inserted": rows_loaded,
                        "source_rows": rows_loaded,
                        "duration_seconds": load_duration,
                    }
                )
            except subprocess.CalledProcessError:
                table_summaries.append(
                    {
                        "table_name": step.target_table,
                        "load_mode": "kafka_bronze_ready_event",
                        "status": "failed",
                        "rows_inserted": 0,
                        "source_rows": 0,
                        "duration_seconds": None,
                    }
                )
                raise

        ended_at = datetime.now(timezone.utc)
        duration_seconds = round(time.perf_counter() - start_counter, 3)
        record_pipeline_state(
            status="success",
            started_at=started_at,
            ended_at=ended_at,
            table_summaries=table_summaries,
            success_message="[MONITORING] Raw load state recorded successfully",
            failure_message="[MONITORING] Raw load state recording failed",
        )
        print("=" * 80)
        print("[SUCCESS] Client 1 Kafka raw pipeline completed successfully.")
        print(f"[DURATION] {duration_seconds} seconds")
        print("=" * 80)
        return 0
    except subprocess.CalledProcessError as exc:
        ended_at = datetime.now(timezone.utc)
        duration_seconds = round(time.perf_counter() - start_counter, 3)
        record_pipeline_state(
            status="failed",
            started_at=started_at,
            ended_at=ended_at,
            table_summaries=table_summaries,
            success_message="[MONITORING] Raw load failure state recorded successfully",
            failure_message="[MONITORING] Raw load failure state recording failed",
        )
        print("=" * 80)
        print(f"[ERROR] Kafka raw pipeline failed while running: {exc.cmd}")
        print(f"[DURATION] {duration_seconds} seconds")
        print("=" * 80)
        return exc.returncode or 1


if __name__ == "__main__":
    raise SystemExit(main())
