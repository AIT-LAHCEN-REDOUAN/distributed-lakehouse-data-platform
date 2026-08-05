from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import requests
from dotenv import load_dotenv


def _resolve_customerdna_root() -> Path:
    env_root = os.getenv("CUSTOMERDNA_PROJECT_ROOT_IN_CONTAINER")
    if env_root:
        candidate = Path(env_root)
        if candidate.exists():
            return candidate

    airflow_default = Path("/opt/airflow/CustomerDNA_AI")
    if airflow_default.exists():
        return airflow_default

    current = Path(__file__).resolve()
    for candidate in (current.parent, *current.parents):
        if (candidate / "src").exists():
            return candidate
        if candidate.name == "CustomerDNA AI" and (candidate / "src").exists():
            return candidate

    raise FileNotFoundError(
        "Could not resolve the CustomerDNA project root for Airflow DAG execution."
    )


CUSTOMERDNA_ROOT = _resolve_customerdna_root()

AIRFLOW_ROOT = CUSTOMERDNA_ROOT / "src" / "airflow"
HDFS_ROOT = CUSTOMERDNA_ROOT / "src" / "lake" / "hdfs"
SPARK_ROOT = CUSTOMERDNA_ROOT / "src" / "processing" / "spark"
HIVE_ROOT = CUSTOMERDNA_ROOT / "src" / "catalog" / "hive"
TRINO_ROOT = CUSTOMERDNA_ROOT / "src" / "query" / "trino"
GX_DIR = CUSTOMERDNA_ROOT / "src" / "quality" / "great_expectations" / "client_1"
CLIENT_KAFKA_DIR = CUSTOMERDNA_ROOT / "src" / "streaming" / "kafka" / "client_1"
MONITORING_ROOT = CUSTOMERDNA_ROOT / "src" / "monitoring"
DBT_SPARK_ROOT = CUSTOMERDNA_ROOT / "src" / "transformation" / "dbt_spark" / "client_1"

LOCAL_KAFKA_BOOTSTRAP_VALUES = {"", "localhost:9092", "127.0.0.1:9092"}
LOCAL_HDFS_WEB_ENDPOINTS = {"", "localhost:9870", "127.0.0.1:9870", "http://localhost:9870"}
LOCAL_HDFS_NAMENODE_URIS = {"", "hdfs://localhost:9000", "hdfs://127.0.0.1:9000"}
LOCAL_SPARK_THRIFT_HOSTS = {"", "localhost", "127.0.0.1"}

DEFAULT_CONTAINER_SAFE_KAFKA_BOOTSTRAP = "broker:29092"
DEFAULT_CONTAINER_SAFE_HDFS_WEB = "namenode:9870"
DEFAULT_CONTAINER_SAFE_HDFS_URI = "hdfs://namenode:9000"
DEFAULT_CONTAINER_SAFE_HIVE_METASTORE_HOST = "hive-metastore"
DEFAULT_CONTAINER_SAFE_HIVE_METASTORE_PORT = "9083"
DEFAULT_CONTAINER_SAFE_SPARK_MASTER_UI = "http://spark-master:8086"
DEFAULT_CONTAINER_SAFE_SPARK_THRIFT_HOST = "spark-thrift-server"
DEFAULT_CONTAINER_SAFE_SPARK_THRIFT_PORT = "10000"
DEFAULT_CONTAINER_SAFE_TRINO_URL = "http://trino:8080"


for env_path in (
    AIRFLOW_ROOT / ".env",
    HDFS_ROOT / ".env",
    SPARK_ROOT / ".env",
    HIVE_ROOT / ".env",
    TRINO_ROOT / ".env",
):
    if env_path.exists():
        load_dotenv(env_path, override=False)

if str(MONITORING_ROOT) not in sys.path:
    sys.path.insert(0, str(MONITORING_ROOT))

from shared.pipeline_metrics import record_task_run  # noqa: E402


DEFAULT_ARGS = {
    "owner": "customerdna",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=2),
}


def build_runtime_env() -> dict[str, str]:
    env = os.environ.copy()

    if env.get("CUSTOMERDNA_KAFKA_BOOTSTRAP_SERVERS", "").strip() in LOCAL_KAFKA_BOOTSTRAP_VALUES:
        env["CUSTOMERDNA_KAFKA_BOOTSTRAP_SERVERS"] = env.get(
            "CUSTOMERDNA_AIRFLOW_KAFKA_BOOTSTRAP_SERVERS",
            DEFAULT_CONTAINER_SAFE_KAFKA_BOOTSTRAP,
        )

    if env.get("CUSTOMERDNA_HDFS_WEB_ENDPOINT", "").strip() in LOCAL_HDFS_WEB_ENDPOINTS:
        env["CUSTOMERDNA_HDFS_WEB_ENDPOINT"] = env.get(
            "CUSTOMERDNA_AIRFLOW_HDFS_WEB_ENDPOINT",
            DEFAULT_CONTAINER_SAFE_HDFS_WEB,
        )

    if env.get("CUSTOMERDNA_HDFS_NAMENODE_URI", "").strip() in LOCAL_HDFS_NAMENODE_URIS:
        env["CUSTOMERDNA_HDFS_NAMENODE_URI"] = env.get(
            "CUSTOMERDNA_AIRFLOW_HDFS_NAMENODE_URI",
            DEFAULT_CONTAINER_SAFE_HDFS_URI,
        )

    env.setdefault(
        "CUSTOMERDNA_HIVE_METASTORE_HOST",
        env.get("CUSTOMERDNA_AIRFLOW_HIVE_METASTORE_HOST", DEFAULT_CONTAINER_SAFE_HIVE_METASTORE_HOST),
    )
    env.setdefault(
        "CUSTOMERDNA_HIVE_METASTORE_PORT",
        env.get("CUSTOMERDNA_AIRFLOW_HIVE_METASTORE_PORT", DEFAULT_CONTAINER_SAFE_HIVE_METASTORE_PORT),
    )
    env.setdefault(
        "CUSTOMERDNA_SPARK_MASTER_UI_URL",
        env.get("CUSTOMERDNA_AIRFLOW_SPARK_MASTER_UI_URL", DEFAULT_CONTAINER_SAFE_SPARK_MASTER_UI),
    )
    env.setdefault(
        "CUSTOMERDNA_TRINO_URL",
        env.get("CUSTOMERDNA_AIRFLOW_TRINO_URL", DEFAULT_CONTAINER_SAFE_TRINO_URL),
    )
    env.setdefault("CUSTOMERDNA_TRINO_CATALOG", "lakehouse")
    env.setdefault("CUSTOMERDNA_TRINO_SCHEMA", "raw_data")
    env.setdefault("CUSTOMERDNA_TRINO_USER", "airflow")
    env.setdefault("CUSTOMERDNA_ICEBERG_RAW_NAMESPACE", "raw_data")

    if env.get("CUSTOMERDNA_DBT_SPARK_HOST", "").strip() in LOCAL_SPARK_THRIFT_HOSTS:
        env["CUSTOMERDNA_DBT_SPARK_HOST"] = env.get(
            "CUSTOMERDNA_AIRFLOW_DBT_SPARK_HOST",
            DEFAULT_CONTAINER_SAFE_SPARK_THRIFT_HOST,
        )
    env.setdefault(
        "CUSTOMERDNA_DBT_SPARK_PORT",
        env.get("CUSTOMERDNA_AIRFLOW_DBT_SPARK_PORT", DEFAULT_CONTAINER_SAFE_SPARK_THRIFT_PORT),
    )
    env.setdefault("CUSTOMERDNA_DBT_SPARK_USER", "airflow")
    env["DBT_PROFILES_DIR"] = str(DBT_SPARK_ROOT)

    return env


def run_command(command: list[str], *, cwd: Path, label: str) -> None:
    started_at = datetime.now(timezone.utc)
    env = build_runtime_env()
    print(f"[TASK] {label}")
    print(f"[CWD] {cwd}")
    print(f"[CMD] {' '.join(command)}")
    print(f"[KAFKA BOOTSTRAP] {env.get('CUSTOMERDNA_KAFKA_BOOTSTRAP_SERVERS')}")
    print(f"[HDFS WEB ENDPOINT] {env.get('CUSTOMERDNA_HDFS_WEB_ENDPOINT')}")
    print(f"[HDFS NAMENODE URI] {env.get('CUSTOMERDNA_HDFS_NAMENODE_URI')}")
    print(f"[SPARK MASTER UI] {env.get('CUSTOMERDNA_SPARK_MASTER_UI_URL')}")
    print(f"[SPARK THRIFT] {env.get('CUSTOMERDNA_DBT_SPARK_HOST')}:{env.get('CUSTOMERDNA_DBT_SPARK_PORT')}")
    print(f"[TRINO URL] {env.get('CUSTOMERDNA_TRINO_URL')}")

    try:
        subprocess.run(
            command,
            check=True,
            cwd=str(cwd),
            env=env,
            text=True,
        )
        _record_airflow_task_run(
            status="success",
            task_label=label,
            started_at=started_at,
            ended_at=datetime.now(timezone.utc),
            command=command,
            cwd=cwd,
        )
    except Exception:
        _record_airflow_task_run(
            status="failed",
            task_label=label,
            started_at=started_at,
            ended_at=datetime.now(timezone.utc),
            command=command,
            cwd=cwd,
        )
        raise


def run_monitored_callable(
    *,
    label: str,
    cwd: Path,
    callback: Callable[[], None],
    command: list[str] | None = None,
) -> None:
    started_at = datetime.now(timezone.utc)
    env = build_runtime_env()
    tracked_command = command or ["python", "<inline_validation>"]

    print(f"[TASK] {label}")
    print(f"[CWD] {cwd}")
    print(f"[CMD] {' '.join(tracked_command)}")
    print(f"[KAFKA BOOTSTRAP] {env.get('CUSTOMERDNA_KAFKA_BOOTSTRAP_SERVERS')}")
    print(f"[HDFS WEB ENDPOINT] {env.get('CUSTOMERDNA_HDFS_WEB_ENDPOINT')}")
    print(f"[HDFS NAMENODE URI] {env.get('CUSTOMERDNA_HDFS_NAMENODE_URI')}")
    print(f"[SPARK MASTER UI] {env.get('CUSTOMERDNA_SPARK_MASTER_UI_URL')}")
    print(f"[SPARK THRIFT] {env.get('CUSTOMERDNA_DBT_SPARK_HOST')}:{env.get('CUSTOMERDNA_DBT_SPARK_PORT')}")
    print(f"[TRINO URL] {env.get('CUSTOMERDNA_TRINO_URL')}")

    try:
        callback()
        _record_airflow_task_run(
            status="success",
            task_label=label,
            started_at=started_at,
            ended_at=datetime.now(timezone.utc),
            command=tracked_command,
            cwd=cwd,
        )
    except Exception:
        _record_airflow_task_run(
            status="failed",
            task_label=label,
            started_at=started_at,
            ended_at=datetime.now(timezone.utc),
            command=tracked_command,
            cwd=cwd,
        )
        raise


def _get_airflow_context() -> dict:
    for module_name in (
        "airflow.sdk",
        "airflow.decorators",
        "airflow.operators.python",
    ):
        try:
            module = __import__(module_name, fromlist=["get_current_context"])
            return module.get_current_context()
        except Exception:
            continue

    return {}


def _record_airflow_task_run(
    *,
    status: str,
    task_label: str,
    started_at: datetime,
    ended_at: datetime,
    command: list[str],
    cwd: Path,
) -> None:
    context = _get_airflow_context()

    dag = context.get("dag")
    task = context.get("task")
    dag_run = context.get("dag_run")

    dag_id = getattr(dag, "dag_id", context.get("dag_id", "unknown_dag"))
    task_id = getattr(task, "task_id", context.get("task_id", "unknown_task"))
    run_id = getattr(dag_run, "run_id", context.get("run_id", "manual"))

    record_task_run(
        dag_id=dag_id,
        task_id=task_id,
        run_id=run_id,
        task_label=task_label,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        command=command,
        cwd=str(cwd),
    )


def _python_command(script_path: Path) -> list[str]:
    return [sys.executable, str(script_path)]


def initialize_bronze_zone() -> None:
    run_command(
        _python_command(HDFS_ROOT / "client_1" / "initialize_client1_bronze_zone.py"),
        cwd=HDFS_ROOT / "client_1",
        label="Initialize Client 1 HDFS bronze zone",
    )


def initialize_lakehouse_namespace() -> None:
    run_command(
        _python_command(TRINO_ROOT / "client_1" / "initialize_lakehouse_namespace.py"),
        cwd=TRINO_ROOT / "client_1",
        label="Initialize Client 1 Iceberg namespaces through Trino",
    )


def reset_kafka_topics() -> None:
    run_command(
        _python_command(CLIENT_KAFKA_DIR / "reset_client1_kafka.py"),
        cwd=CLIENT_KAFKA_DIR,
        label="Reset Client 1 Kafka topics and local Kafka artifacts",
    )


def reset_hdfs_bronze_zone() -> None:
    run_command(
        _python_command(HDFS_ROOT / "client_1" / "reset_client1_bronze.py"),
        cwd=HDFS_ROOT / "client_1",
        label="Reset Client 1 HDFS bronze area",
    )


def reset_lakehouse_namespaces() -> None:
    run_command(
        _python_command(TRINO_ROOT / "client_1" / "reset_lakehouse_namespaces.py"),
        cwd=TRINO_ROOT / "client_1",
        label="Reset Client 1 Iceberg lakehouse schemas through Trino",
    )


def run_kafka_hdfs_spark_raw_pipeline(**context) -> None:
    command = _python_command(CLIENT_KAFKA_DIR / "run_client1_kafka_raw_pipeline.py")
    dag_run = context.get("dag_run")
    dag_run_conf = getattr(dag_run, "conf", {}) or {}
    resume_from_dataset = str(dag_run_conf.get("resume_from_dataset", "")).strip()

    if resume_from_dataset:
        print(f"[INFO] Resume mode requested through DAG run config: {resume_from_dataset}")
        command += ["--resume-from-dataset", resume_from_dataset]

    run_command(
        command,
        cwd=CLIENT_KAFKA_DIR,
        label="Run Client 1 Kafka -> HDFS bronze -> Spark -> Iceberg raw pipeline",
    )


def bootstrap_raw_gx() -> None:
    run_command(
        _python_command(GX_DIR / "bootstrap_gx.py") + ["--layers", "raw"],
        cwd=GX_DIR,
        label="Bootstrap Client 1 raw lakehouse quality assets",
    )


def validate_raw_data() -> None:
    run_command(
        _python_command(GX_DIR / "run_gx_validations.py") + ["--checkpoint", "raw", "--skip-bootstrap"],
        cwd=GX_DIR,
        label="Validate Client 1 Iceberg raw layer quality",
    )


def run_dbt_spark_transformations() -> None:
    run_command(
        ["dbt", "run"],
        cwd=DBT_SPARK_ROOT,
        label="Run Client 1 dbt-spark lakehouse transformations",
    )


def test_dbt_spark_transformations() -> None:
    run_command(
        ["dbt", "test"],
        cwd=DBT_SPARK_ROOT,
        label="Validate Client 1 dbt-spark transformation tests",
    )


def _build_http_url(endpoint: str) -> str:
    normalized = endpoint.strip()
    if not normalized.startswith(("http://", "https://")):
        normalized = f"http://{normalized}"
    return normalized


def validate_hdfs_bronze_service() -> None:
    def _callback() -> None:
        env = build_runtime_env()
        endpoint = _build_http_url(env["CUSTOMERDNA_HDFS_WEB_ENDPOINT"])
        response = requests.get(endpoint, timeout=15)
        response.raise_for_status()
        print(f"[SUCCESS] HDFS NameNode web interface responded with HTTP {response.status_code}")

    run_monitored_callable(
        label="Validate Client 1 HDFS bronze service",
        cwd=HDFS_ROOT,
        callback=_callback,
        command=[sys.executable, str(HDFS_ROOT / "client_1" / "initialize_client1_bronze_zone.py"), "--health-check"],
    )


def validate_hive_metastore_service() -> None:
    def _callback() -> None:
        env = build_runtime_env()
        host = env["CUSTOMERDNA_HIVE_METASTORE_HOST"]
        port = int(env["CUSTOMERDNA_HIVE_METASTORE_PORT"])
        with socket.create_connection((host, port), timeout=15):
            print(f"[SUCCESS] Hive metastore socket is reachable at {host}:{port}")

    run_monitored_callable(
        label="Validate Hive metastore service",
        cwd=HIVE_ROOT,
        callback=_callback,
        command=["python", "hive-metastore", "--health-check"],
    )


def validate_spark_cluster_service() -> None:
    def _callback() -> None:
        env = build_runtime_env()
        response = requests.get(env["CUSTOMERDNA_SPARK_MASTER_UI_URL"], timeout=15)
        response.raise_for_status()
        print(f"[SUCCESS] Spark master UI responded with HTTP {response.status_code}")

    run_monitored_callable(
        label="Validate Spark cluster service",
        cwd=SPARK_ROOT,
        callback=_callback,
        command=["python", "spark-master", "--health-check"],
    )


def validate_spark_thrift_service() -> None:
    def _callback() -> None:
        env = build_runtime_env()
        host = env["CUSTOMERDNA_DBT_SPARK_HOST"]
        port = int(env["CUSTOMERDNA_DBT_SPARK_PORT"])
        timeout_seconds = int(env.get("CUSTOMERDNA_SPARK_THRIFT_READY_TIMEOUT", "120"))
        retry_interval_seconds = int(env.get("CUSTOMERDNA_SPARK_THRIFT_READY_RETRY_INTERVAL", "5"))
        deadline = time.time() + timeout_seconds
        last_error: Exception | None = None

        while time.time() < deadline:
            try:
                with socket.create_connection((host, port), timeout=15):
                    print(f"[SUCCESS] Spark Thrift Server is reachable at {host}:{port}")
                    return
            except OSError as exc:
                last_error = exc
                remaining_seconds = max(0, int(deadline - time.time()))
                print(
                    f"[INFO] Spark Thrift Server not ready yet at {host}:{port}. "
                    f"Retrying in {retry_interval_seconds}s ({remaining_seconds}s remaining)."
                )
                time.sleep(retry_interval_seconds)

        if last_error is not None:
            raise last_error
        raise TimeoutError(f"Spark Thrift Server did not become reachable at {host}:{port}.")

    run_monitored_callable(
        label="Validate Spark Thrift service",
        cwd=SPARK_ROOT,
        callback=_callback,
        command=["python", "spark-thrift-server", "--health-check"],
    )


def validate_trino_query_service() -> None:
    def _callback() -> None:
        env = build_runtime_env()
        response = requests.get(f"{env['CUSTOMERDNA_TRINO_URL'].rstrip('/')}/v1/info", timeout=15)
        response.raise_for_status()
        print(f"[SUCCESS] Trino query service responded with HTTP {response.status_code}")

    run_monitored_callable(
        label="Validate Trino query service",
        cwd=TRINO_ROOT,
        callback=_callback,
        command=["python", "trino", "--health-check"],
    )
