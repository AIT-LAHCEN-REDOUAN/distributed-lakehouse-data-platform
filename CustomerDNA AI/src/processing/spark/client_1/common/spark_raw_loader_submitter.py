"""Submit Client 1 Spark Iceberg-load jobs through the spark-master container."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse


try:
    import docker  # type: ignore
except Exception:  # pragma: no cover - optional local dependency
    docker = None


ROWS_LOADED_PATTERN = re.compile(r"Rows loaded:\s*([0-9,]+)")
FILES_READ_PATTERN = re.compile(r"Bronze files read:\s*([0-9,]+)")
DURATION_PATTERN = re.compile(r"Duration \(seconds\):\s*([0-9]+(?:\.[0-9]+)?)")

SPARK_SUBMIT_CONTAINER = os.getenv("CUSTOMERDNA_SPARK_SUBMIT_CONTAINER", "spark-master")
SPARK_MASTER_URL = os.getenv("CUSTOMERDNA_SPARK_MASTER_URL", "spark://spark-master:7077")
SPARK_BIN = os.getenv("CUSTOMERDNA_SPARK_BIN", "/opt/spark/bin/spark-submit")
SPARK_JOBS_ROOT_IN_CONTAINER = os.getenv("CUSTOMERDNA_SPARK_JOBS_ROOT_IN_CONTAINER", "/opt/spark/jobs")
SPARK_JOB_PATH = os.getenv(
    "CUSTOMERDNA_SPARK_JOB_PATH",
    f"{SPARK_JOBS_ROOT_IN_CONTAINER}/client_1/load_hdfs_bronze_to_iceberg.py",
)
SPARK_IVY_HOME = os.getenv("CUSTOMERDNA_SPARK_IVY_HOME", "/opt/spark/work-dir/.ivy2")
SPARK_HOME_DIR = os.getenv("CUSTOMERDNA_SPARK_HOME_DIR", "/opt/spark/work-dir")
ICEBERG_CATALOG_NAME = os.getenv("CUSTOMERDNA_ICEBERG_CATALOG_NAME", "customerdna")
ICEBERG_RAW_NAMESPACE = os.getenv("CUSTOMERDNA_ICEBERG_RAW_NAMESPACE", "raw_data")


@dataclass(frozen=True)
class SparkRawLoadResult:
    rows_loaded: int
    bronze_files_read: int
    duration_seconds: float
    stdout: str


def _build_spark_submit_command(
    *,
    dataset_key: str,
    target_table: str,
    bronze_prefix: str,
    hdfs_namenode_uri: str,
    expected_rows: int | None,
    expected_file_count: int | None,
) -> list[str]:
    parsed_hdfs_uri = urlparse(hdfs_namenode_uri)
    container_safe_hdfs_uri = hdfs_namenode_uri
    if parsed_hdfs_uri.scheme == "hdfs" and parsed_hdfs_uri.hostname in {"localhost", "127.0.0.1"}:
        container_safe_hdfs_uri = urlunparse(
            (
                parsed_hdfs_uri.scheme,
                f"namenode:{parsed_hdfs_uri.port or 9000}",
                parsed_hdfs_uri.path,
                parsed_hdfs_uri.params,
                parsed_hdfs_uri.query,
                parsed_hdfs_uri.fragment,
            )
        )

    return [
        SPARK_BIN,
        "--master",
        SPARK_MASTER_URL,
        "--conf",
        "spark.eventLog.enabled=false",
        SPARK_JOB_PATH,
        "--dataset-key",
        dataset_key,
        "--target-table",
        target_table,
        "--iceberg-catalog",
        ICEBERG_CATALOG_NAME,
        "--iceberg-namespace",
        ICEBERG_RAW_NAMESPACE,
        "--bronze-prefix",
        bronze_prefix,
        "--hdfs-namenode-uri",
        container_safe_hdfs_uri,
        "--expected-rows",
        str(expected_rows or 0),
        "--expected-file-count",
        str(expected_file_count or 0),
    ]


def _parse_result(stdout: str) -> SparkRawLoadResult:
    rows_match = ROWS_LOADED_PATTERN.search(stdout)
    files_match = FILES_READ_PATTERN.search(stdout)
    duration_match = DURATION_PATTERN.search(stdout)

    if not rows_match or not files_match or not duration_match:
        raise RuntimeError("Unable to parse Spark Iceberg-load output summary.")

    return SparkRawLoadResult(
        rows_loaded=int(rows_match.group(1).replace(",", "")),
        bronze_files_read=int(files_match.group(1).replace(",", "")),
        duration_seconds=float(duration_match.group(1)),
        stdout=stdout,
    )


def _run_with_docker_sdk(command: list[str]) -> str:
    client = docker.from_env()
    container = client.containers.get(SPARK_SUBMIT_CONTAINER)
    exec_id = client.api.exec_create(container.id, command)["Id"]
    stream = client.api.exec_start(exec_id, stream=True)
    output_chunks: list[str] = []

    for chunk in stream:
        text = chunk.decode("utf-8", errors="replace")
        print(text, end="" if text.endswith("\n") else "\n")
        output_chunks.append(text)

    exit_code = int(client.api.exec_inspect(exec_id).get("ExitCode", 1))
    stdout = "".join(output_chunks)
    if exit_code != 0:
        raise RuntimeError(
            f"Spark submit failed inside container '{SPARK_SUBMIT_CONTAINER}' with exit code {exit_code}."
        )
    return stdout


def _run_with_docker_cli(command: list[str]) -> str:
    if not shutil.which("docker"):
        raise RuntimeError(
            "Neither the Python docker SDK nor the docker CLI is available for Spark submission."
        )

    docker_command = ["docker", "exec", SPARK_SUBMIT_CONTAINER, *command]
    completed = subprocess.run(
        docker_command,
        check=True,
        capture_output=True,
        text=True,
    )
    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", file=sys.stderr)
    return completed.stdout


def submit_hdfs_bronze_to_iceberg_spark_job(
    *,
    dataset_key: str,
    target_table: str,
    bronze_prefix: str,
    hdfs_namenode_uri: str,
    expected_rows: int | None = None,
    expected_file_count: int | None = None,
) -> SparkRawLoadResult:
    base_command = _build_spark_submit_command(
        dataset_key=dataset_key,
        target_table=target_table,
        bronze_prefix=bronze_prefix,
        hdfs_namenode_uri=hdfs_namenode_uri,
        expected_rows=expected_rows,
        expected_file_count=expected_file_count,
    )

    command = [
        "/bin/sh",
        "-lc",
        (
            f"mkdir -p {shlex.quote(SPARK_IVY_HOME)}/cache {shlex.quote(SPARK_IVY_HOME)}/jars && "
            f"export HOME={shlex.quote(SPARK_HOME_DIR)} "
            f"IVY_HOME={shlex.quote(SPARK_IVY_HOME)} "
            f"SPARK_SUBMIT_OPTS='-Divy.home={SPARK_IVY_HOME} -Divy.cache.dir={SPARK_IVY_HOME}/cache'; "
            f"{shlex.join(base_command)}"
        ),
    ]

    print(f"[SPARK] Submission container: {SPARK_SUBMIT_CONTAINER}")
    print(f"[SPARK] Submit command: {' '.join(base_command)}")

    if docker is not None:
        stdout = _run_with_docker_sdk(command)
    else:
        stdout = _run_with_docker_cli(command)

    return _parse_result(stdout)
