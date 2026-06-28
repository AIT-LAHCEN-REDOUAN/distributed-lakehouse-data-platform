from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator


PROJECT_ROOT = Path("/opt/airflow/CustomerDNA_AI")
INGESTION_SCRIPTS_DIR = PROJECT_ROOT / "src" / "Data_Ingestion" / "client_1" / "scripts"
CLIENT_ELT_DIR = PROJECT_ROOT / "src" / "ELT" / "client_1"
DBT_DIR = CLIENT_ELT_DIR / "dbt"
GX_DIR = CLIENT_ELT_DIR / "great_expectations"
CLIENT_ENV_PATH = CLIENT_ELT_DIR / ".env"


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
    # Default to the Docker host alias when the client env still uses localhost.
    container_safe_host = env.get("CUSTOMERDNA_AIRFLOW_DW_HOST", "host.docker.internal")
    if env.get("CUSTOMERDNA_POSTGRES_HOST", "localhost") in {"localhost", "127.0.0.1"}:
        env["CUSTOMERDNA_POSTGRES_HOST"] = container_safe_host

    env["DBT_PROFILES_DIR"] = str(DBT_DIR)
    env["PYTHONUNBUFFERED"] = "1"
    return env


def run_command(command: list[str], cwd: Path, task_label: str) -> None:
    env = build_task_env()
    print(f"[TASK] {task_label}")
    print(f"[CWD] {cwd}")
    print(f"[CMD] {' '.join(command)}")
    print(f"[DB HOST] {env.get('CUSTOMERDNA_POSTGRES_HOST')}")

    subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        check=True,
    )


def run_ingestion() -> None:
    run_command(
        [sys.executable, str(INGESTION_SCRIPTS_DIR / "run_all_ingestions.py")],
        INGESTION_SCRIPTS_DIR,
        "Client 1 data ingestion",
    )


def load_raw_data() -> None:
    run_command(
        [sys.executable, str(CLIENT_ELT_DIR / "load_data_to_dw.py")],
        CLIENT_ELT_DIR,
        "Load processed ingestion outputs into client1_DW.raw_data",
    )


def bootstrap_gx() -> None:
    run_command(
        [sys.executable, str(GX_DIR / "bootstrap_gx.py")],
        GX_DIR,
        "Bootstrap Great Expectations context and assets",
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


default_args = {
    "owner": "customerdna",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="customerdna_client1_elt_pipeline",
    description="Client 1 ELT pipeline: ingestion -> raw load -> dbt -> dbt test -> Great Expectations validation",
    default_args=default_args,
    start_date=datetime(2026, 6, 28),
    schedule=None,
    catchup=False,
    tags=["customerdna", "client1", "elt", "dbt", "gx"],
) as dag:
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    ingest = PythonOperator(
        task_id="ingest_client1_datasets",
        python_callable=run_ingestion,
    )

    load_raw = PythonOperator(
        task_id="load_raw_data_to_dw",
        python_callable=load_raw_data,
    )

    gx_bootstrap = PythonOperator(
        task_id="bootstrap_great_expectations",
        python_callable=bootstrap_gx,
    )

    gx_raw = PythonOperator(
        task_id="validate_raw_data_quality",
        python_callable=validate_raw_data,
    )

    dbt_run = PythonOperator(
        task_id="dbt_run_all_models",
        python_callable=dbt_run_all,
    )

    dbt_test = PythonOperator(
        task_id="dbt_test_all_models",
        python_callable=dbt_test_all,
    )

    gx_analytics = PythonOperator(
        task_id="validate_analytics_quality",
        python_callable=validate_analytics_data,
    )

    gx_ml = PythonOperator(
        task_id="validate_ml_feature_readiness",
        python_callable=validate_ml_readiness,
    )

    start >> ingest >> load_raw >> gx_bootstrap >> gx_raw >> dbt_run >> dbt_test >> gx_analytics >> gx_ml >> end