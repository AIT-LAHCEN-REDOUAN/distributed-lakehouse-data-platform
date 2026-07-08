from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path("/opt/airflow/CustomerDNA_AI")
CLIENT_ELT_DIR = PROJECT_ROOT / "src" / "ELT" / "client_1"
CLIENT_KAFKA_DIR = PROJECT_ROOT / "src" / "streaming" / "kafka" / "client_1"
SETUP_DW_DIR = CLIENT_ELT_DIR / "setup_dw"
DBT_DIR = CLIENT_ELT_DIR / "dbt"
GX_DIR = CLIENT_ELT_DIR / "great_expectations"
CLIENT_ENV_PATH = CLIENT_ELT_DIR / ".env"
MONITORING_SRC_DIR = PROJECT_ROOT / "src" / "monitoring"

if str(MONITORING_SRC_DIR) not in sys.path:
    sys.path.append(str(MONITORING_SRC_DIR))

try:
    from shared.pipeline_metrics import record_task_run
except Exception:
    record_task_run = None

DEFAULT_ARGS = {
    "owner": "customerdna",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


def read_env_file(env_path: Path) -> dict[str, str]:
    env_vars: dict[str, str] = {}

    if not env_path.exists():
        return env_vars

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        env_vars[key.strip()] = value.strip()

    return env_vars


def build_task_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(read_env_file(CLIENT_ENV_PATH))

    # Inside the Airflow container, localhost points to the container itself.
    container_safe_host = env.get("CUSTOMERDNA_AIRFLOW_DW_HOST", "host.docker.internal")
    if env.get("CUSTOMERDNA_POSTGRES_HOST", "localhost") in {"localhost", "127.0.0.1"}:
        env["CUSTOMERDNA_POSTGRES_HOST"] = container_safe_host

    if not env.get("CUSTOMERDNA_KAFKA_BOOTSTRAP_SERVERS"):
        env["CUSTOMERDNA_KAFKA_BOOTSTRAP_SERVERS"] = env.get(
            "CUSTOMERDNA_AIRFLOW_KAFKA_BOOTSTRAP_SERVERS",
            "broker:29092",
        )

    env["DBT_PROFILES_DIR"] = str(DBT_DIR)
    env["PYTHONUNBUFFERED"] = "1"
    return env


def run_command(command: list[str], cwd: Path, task_label: str) -> None:
    env = build_task_env()
    started_at = datetime.now(timezone.utc)
    start_counter = time.perf_counter()
    status = "success"

    print(f"[TASK] {task_label}")
    print(f"[CWD] {cwd}")
    print(f"[CMD] {' '.join(command)}")
    print(f"[DB HOST] {env.get('CUSTOMERDNA_POSTGRES_HOST')}")
    print(f"[KAFKA BOOTSTRAP] {env.get('CUSTOMERDNA_KAFKA_BOOTSTRAP_SERVERS')}")

    try:
        subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            check=True,
        )
    except subprocess.CalledProcessError:
        status = "failed"
        raise
    finally:
        ended_at = datetime.now(timezone.utc)
        duration = time.perf_counter() - start_counter
        print(f"[STATUS] {status.upper()}")
        print(f"[DURATION] {duration:.3f}s")

        if record_task_run:
            record_task_run(
                dag_id=env.get("AIRFLOW_CTX_DAG_ID", "manual_execution"),
                task_id=env.get("AIRFLOW_CTX_TASK_ID", task_label.lower().replace(" ", "_")),
                run_id=env.get("AIRFLOW_CTX_DAG_RUN_ID", env.get("AIRFLOW_CTX_RUN_ID", "manual_run")),
                task_label=task_label,
                status=status,
                started_at=started_at,
                ended_at=ended_at,
                command=command,
                cwd=str(cwd),
            )


def run_setup_dw() -> None:
    run_command(
        [sys.executable, str(SETUP_DW_DIR / "setup_dw.py")],
        SETUP_DW_DIR,
        "Initialize Client 1 data warehouse database and schemas",
    )


def run_create_base_tables() -> None:
    run_command(
        [sys.executable, str(SETUP_DW_DIR / "create_base_tables.py")],
        SETUP_DW_DIR,
        "Create Client 1 raw base tables",
    )


def load_raw_data() -> None:
    run_command(
        [sys.executable, str(CLIENT_KAFKA_DIR / "run_client1_kafka_raw_pipeline.py")],
        CLIENT_KAFKA_DIR,
        "Run Client 1 Kafka raw pipeline into client1_DW.raw_data",
    )


def bootstrap_raw_gx() -> None:
    run_command(
        [sys.executable, str(GX_DIR / "bootstrap_gx.py"), "--layers", "raw"],
        GX_DIR,
        "Bootstrap Great Expectations context and raw assets",
    )


def bootstrap_analytics_gx() -> None:
    run_command(
        [sys.executable, str(GX_DIR / "bootstrap_gx.py"), "--layers", "analytics"],
        GX_DIR,
        "Bootstrap Great Expectations context and analytics assets",
    )


def bootstrap_transformation_gx() -> None:
    run_command(
        [sys.executable, str(GX_DIR / "bootstrap_gx.py"), "--layers", "all"],
        GX_DIR,
        "Bootstrap Great Expectations context and transformation-serving assets",
    )


def validate_raw_data() -> None:
    run_command(
        [
            sys.executable,
            str(GX_DIR / "run_gx_validations.py"),
            "--checkpoint",
            "raw",
            "--skip-bootstrap",
        ],
        GX_DIR,
        "Run Great Expectations raw data checkpoint",
    )


def dbt_run_all() -> None:
    run_command(
        [
            "dbt",
            "run",
            "--project-dir",
            str(DBT_DIR),
            "--profiles-dir",
            str(DBT_DIR),
        ],
        DBT_DIR,
        "Run dbt models for Client 1",
    )


def dbt_test_all() -> None:
    run_command(
        [
            "dbt",
            "test",
            "--project-dir",
            str(DBT_DIR),
            "--profiles-dir",
            str(DBT_DIR),
        ],
        DBT_DIR,
        "Run dbt tests for Client 1",
    )


def validate_analytics_data() -> None:
    run_command(
        [
            sys.executable,
            str(GX_DIR / "run_gx_validations.py"),
            "--checkpoint",
            "analytics",
            "--skip-bootstrap",
        ],
        GX_DIR,
        "Run Great Expectations analytics checkpoint",
    )


def validate_serving_data() -> None:
    run_command(
        [
            sys.executable,
            str(GX_DIR / "run_gx_validations.py"),
            "--checkpoint",
            "serving",
            "--skip-bootstrap",
        ],
        GX_DIR,
        "Run Great Expectations serving checkpoint",
    )


def validate_ml_readiness() -> None:
    run_command(
        [
            sys.executable,
            str(GX_DIR / "run_gx_validations.py"),
            "--checkpoint",
            "ml",
            "--skip-bootstrap",
        ],
        GX_DIR,
        "Run Great Expectations ML-readiness checkpoint",
    )
