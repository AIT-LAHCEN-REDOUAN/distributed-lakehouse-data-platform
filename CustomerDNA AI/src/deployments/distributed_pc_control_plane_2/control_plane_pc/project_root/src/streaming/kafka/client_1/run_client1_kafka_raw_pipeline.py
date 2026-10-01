"""Run the Client 1 Kafka -> HDFS bronze -> Spark -> Iceberg raw pipeline."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


CLIENT_ROOT = Path(__file__).resolve().parent
COMMON_ROOT = CLIENT_ROOT / "common"
PROJECT_SRC_ROOT = CLIENT_ROOT.parents[2]
MONITORING_ROOT = PROJECT_SRC_ROOT / "monitoring"

for import_root in (COMMON_ROOT, MONITORING_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from kafka_config import DATASET_ORDER, get_dataset_config  # noqa: E402
from shared.pipeline_metrics import record_raw_load_run  # noqa: E402


ROWS_LOADED_PATTERN = re.compile(r"Rows loaded:\s*([0-9,]+)")
DURATION_PATTERN = re.compile(r"Duration \(seconds\):\s*([0-9]+(?:\.[0-9]+)?)")
BRONZE_FILES_PATTERN = re.compile(r"Bronze files read:\s*([0-9,]+)")


@dataclass(frozen=True)
class DatasetPipelineStep:
    dataset_key: str
    producer_script: Path
    bronze_consumer_script: Path
    spark_raw_builder_script: Path
    iceberg_table: str


@dataclass(frozen=True)
class StreamedCommandResult:
    stdout: str
    returncode: int


def build_dataset_steps() -> list[DatasetPipelineStep]:
    steps: list[DatasetPipelineStep] = []
    for dataset_key in DATASET_ORDER:
        dataset_dir = CLIENT_ROOT / dataset_key
        dataset_config = get_dataset_config(dataset_key)
        steps.append(
            DatasetPipelineStep(
                dataset_key=dataset_key,
                producer_script=dataset_dir / "produce.py",
                bronze_consumer_script=dataset_dir / "consume.py",
                spark_raw_builder_script=dataset_dir / "load.py",
                iceberg_table=str(dataset_config["target_table"]),
            )
        )
    return steps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Client 1 Kafka -> HDFS bronze -> Spark -> Iceberg raw pipeline."
    )
    parser.add_argument(
        "--resume-from-dataset",
        help="Resume from one dataset key and skip the global reset steps.",
    )
    return parser.parse_args()


def run_python(script_path: Path, *, label: str, extra_args: list[str] | None = None) -> StreamedCommandResult:
    command = [sys.executable, str(script_path)]
    if extra_args:
        command.extend(extra_args)
    print("-" * 80)
    print(f"[TASK] {label}")
    print(f"[SCRIPT] {' '.join(command)}")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    output_lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="")
        output_lines.append(line)

    returncode = process.wait()
    stdout = "".join(output_lines)
    if returncode != 0:
        raise subprocess.CalledProcessError(returncode, command, output=stdout)

    return StreamedCommandResult(stdout=stdout, returncode=returncode)


def echo_output(result: StreamedCommandResult) -> None:
    _ = result


def parse_rows_loaded(stdout: str) -> int:
    match = ROWS_LOADED_PATTERN.search(stdout)
    if not match:
        raise RuntimeError("Unable to parse 'Rows loaded' from Spark raw builder output.")
    return int(match.group(1).replace(",", ""))


def parse_duration(stdout: str) -> float:
    match = DURATION_PATTERN.search(stdout)
    if not match:
        raise RuntimeError("Unable to parse 'Duration (seconds)' from Spark raw builder output.")
    return float(match.group(1))


def parse_bronze_files(stdout: str) -> int:
    match = BRONZE_FILES_PATTERN.search(stdout)
    if not match:
        raise RuntimeError("Unable to parse 'Bronze files read' from Spark raw builder output.")
    return int(match.group(1).replace(",", ""))


def main() -> int:
    args = parse_args()
    dataset_steps = build_dataset_steps()
    started_at = datetime.now(timezone.utc)
    start_counter = time.perf_counter()
    table_summaries: list[dict[str, object]] = []
    failed_datasets: list[str] = []
    skipped_datasets = 0
    resume_from_dataset = (args.resume_from_dataset or "").strip()

    if resume_from_dataset:
        dataset_keys = [step.dataset_key for step in dataset_steps]
        if resume_from_dataset not in dataset_keys:
            raise RuntimeError(
                "Unsupported resume dataset key: "
                f"{resume_from_dataset}. Expected one of: {', '.join(dataset_keys)}"
            )
        resume_index = dataset_keys.index(resume_from_dataset)
        skipped_datasets = resume_index
        dataset_steps = dataset_steps[resume_index:]

    print("=" * 80)
    print("CUSTOMERDNA AI - CLIENT 1 KAFKA HDFS SPARK LAKEHOUSE PIPELINE")
    print("=" * 80)
    if resume_from_dataset:
        print("Mode: resume from failed dataset -> Kafka -> HDFS bronze -> Spark -> Iceberg raw")
        print(
            "Flow: targeted reset for the resume dataset -> produce -> consume to bronze "
            "-> build Iceberg raw tables"
        )
        print(f"Resume dataset: {resume_from_dataset}")
        print(f"Skipped datasets from the original order: {skipped_datasets}")
    else:
        print("Mode: source -> Kafka -> HDFS bronze -> Spark -> Iceberg raw")
        print("Flow: reset Kafka -> reset bronze -> produce -> consume to bronze -> build Iceberg raw tables")
    print("Dataset order: small datasets first, largest datasets last")
    print("=" * 80)

    if resume_from_dataset:
        targeted_reset_result = run_python(
            CLIENT_ROOT / "reset_single_dataset_state.py",
            label=f"Reset dataset state for '{resume_from_dataset}' before resume",
            extra_args=["--dataset-key", resume_from_dataset],
        )
        echo_output(targeted_reset_result)
    else:
        reset_result = run_python(
            CLIENT_ROOT / "reset_client1_kafka.py",
            label="Reset Client 1 Kafka topics and local Kafka artifacts",
        )
        echo_output(reset_result)

        bronze_reset_script = PROJECT_SRC_ROOT / "lake" / "hdfs" / "client_1" / "reset_client1_bronze.py"
        bronze_reset_result = run_python(bronze_reset_script, label="Reset Client 1 HDFS bronze area")
        echo_output(bronze_reset_result)

    for step in dataset_steps:
        try:
            produce_result = run_python(
                step.producer_script,
                label=f"Publish source dataset '{step.dataset_key}' into Kafka",
            )
            echo_output(produce_result)

            bronze_consumer_result = run_python(
                step.bronze_consumer_script,
                label=f"Persist dataset '{step.dataset_key}' from Kafka into HDFS bronze",
            )
            echo_output(bronze_consumer_result)

            spark_builder_result = run_python(
                step.spark_raw_builder_script,
                label=f"Build Iceberg raw table for dataset '{step.dataset_key}' with Spark",
            )
            echo_output(spark_builder_result)

            rows_loaded = parse_rows_loaded(spark_builder_result.stdout)
            bronze_files_read = parse_bronze_files(spark_builder_result.stdout)
            dataset_duration = parse_duration(spark_builder_result.stdout)

            table_summaries.append(
                {
                    "table_name": step.iceberg_table,
                    "iceberg_namespace": "raw_data",
                    "status": "success",
                    "rows_inserted": rows_loaded,
                    "source_rows": rows_loaded,
                    "bronze_files_read": bronze_files_read,
                    "load_mode": "kafka_hdfs_spark_iceberg",
                    "duration_seconds": dataset_duration,
                }
            )
        except subprocess.CalledProcessError as exc:
            failed_datasets.append(step.dataset_key)
            print(f"[ERROR] Dataset '{step.dataset_key}' failed with exit code {exc.returncode}")
            if exc.output:
                print(exc.output.rstrip())
            table_summaries.append(
                {
                    "table_name": step.iceberg_table,
                    "iceberg_namespace": "raw_data",
                    "status": "failed",
                    "rows_inserted": 0,
                    "source_rows": 0,
                    "bronze_files_read": 0,
                    "load_mode": "kafka_hdfs_spark_iceberg",
                    "duration_seconds": 0.0,
                }
            )
            break

    ended_at = datetime.now(timezone.utc)
    total_duration = round(time.perf_counter() - start_counter, 3)
    successful_tables = sum(1 for table in table_summaries if table["status"] == "success")
    total_rows_loaded = sum(int(table["rows_inserted"]) for table in table_summaries)
    total_bronze_files = sum(int(table.get("bronze_files_read", 0)) for table in table_summaries)
    overall_success = len(failed_datasets) == 0 and successful_tables == len(dataset_steps)

    summary = {
        "pipeline_name": "client1_kafka_hdfs_spark_lakehouse_pipeline",
        "status": "success" if overall_success else "failed",
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_seconds": total_duration,
        "successful_files": successful_tables,
        "failed_files": len(failed_datasets),
        "skipped_files": skipped_datasets,
        "refreshed_files": successful_tables,
        "incremental_files": 0,
        "total_rows_inserted": total_rows_loaded,
        "total_bronze_files": total_bronze_files,
        "failed_datasets": failed_datasets,
        "tables": table_summaries,
    }
    record_raw_load_run(summary)

    print("=" * 80)
    if overall_success:
        print("[SUCCESS] Client 1 Kafka HDFS Spark lakehouse pipeline completed successfully.")
    else:
        print("[ERROR] Client 1 Kafka HDFS Spark lakehouse pipeline failed.")
        print(f"Failed datasets: {', '.join(failed_datasets)}")
    print(f"Datasets processed successfully: {successful_tables}/{len(dataset_steps)}")
    if skipped_datasets:
        print(f"Datasets skipped due to resume mode: {skipped_datasets}")
    print(f"Bronze files read this run: {total_bronze_files:,}")
    print(f"Rows loaded into Iceberg raw tables this run: {total_rows_loaded:,}")
    print(f"Duration (seconds): {total_duration}")
    print("=" * 80)

    return 0 if overall_success else 1


if __name__ == "__main__":
    raise SystemExit(main())
