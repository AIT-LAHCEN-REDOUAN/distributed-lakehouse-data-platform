from __future__ import annotations

import json
import math
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable


MONITORING_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = MONITORING_ROOT / "state"

AIRFLOW_STATE_PATH = STATE_DIR / "airflow_pipeline_state.json"
RAW_LOAD_STATE_PATH = STATE_DIR / "raw_load_state.json"
GX_STATE_PATH = STATE_DIR / "gx_state.json"
MONITORING_ERROR_LOG_PATH = STATE_DIR / "monitoring_errors.log"

FINAL_TASK_BY_DAG = {
    "customerdna_client1_dw_setup_pipeline": "create_client1_raw_base_tables",
    "customerdna_client1_raw_load_pipeline": "validate_raw_data_quality",
    "customerdna_client1_transformation_quality_pipeline": "validate_ml_feature_readiness",
}

_STATE_LOCK = threading.Lock()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime | None = None) -> str:
    current = value or utc_now()
    return current.astimezone(timezone.utc).isoformat()


def iso_to_unix_seconds(value: str | None) -> float | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return None


def duration_seconds(started_at: str | None, ended_at: str | None) -> float | None:
    start_value = iso_to_unix_seconds(started_at)
    end_value = iso_to_unix_seconds(ended_at)

    if start_value is None or end_value is None:
        return None

    return max(end_value - start_value, 0.0)


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default_factory: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    if not path.exists():
        return default_factory()

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
    except (json.JSONDecodeError, OSError):
        pass

    return default_factory()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_state_dir()

    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as temp_handle:
        json.dump(payload, temp_handle, indent=2, sort_keys=True)
        temp_handle.write("\n")
        temp_path = Path(temp_handle.name)

    os.replace(temp_path, path)


def _append_error_log(message: str) -> None:
    try:
        ensure_state_dir()
        with MONITORING_ERROR_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(f"{isoformat_utc()} | {message}\n")
    except Exception:
        pass


def _default_airflow_state() -> dict[str, Any]:
    return {
        "updated_at": isoformat_utc(),
        "tasks": {},
        "dag_runs": {},
        "pipelines": {},
    }


def _default_raw_load_state() -> dict[str, Any]:
    return {
        "updated_at": isoformat_utc(),
        "last_run": None,
    }


def _default_gx_state() -> dict[str, Any]:
    return {
        "updated_at": isoformat_utc(),
        "checkpoints": {},
    }


def _cleanup_old_runs(dag_runs: dict[str, Any], keep_latest: int = 25) -> dict[str, Any]:
    if len(dag_runs) <= keep_latest:
        return dag_runs

    sortable_runs: list[tuple[str, float]] = []
    for key, value in dag_runs.items():
        ended_at = iso_to_unix_seconds(value.get("ended_at"))
        started_at = iso_to_unix_seconds(value.get("started_at"))
        sortable_runs.append((key, ended_at or started_at or 0.0))

    retained_keys = {
        key
        for key, _ in sorted(sortable_runs, key=lambda item: item[1], reverse=True)[:keep_latest]
    }

    return {
        key: value
        for key, value in dag_runs.items()
        if key in retained_keys
    }


def _safe_write(
    path: Path,
    default_factory: Callable[[], dict[str, Any]],
    updater: Callable[[dict[str, Any]], None],
) -> bool:
    last_error: Exception | None = None

    for attempt in range(1, 4):
        try:
            with _STATE_LOCK:
                state = _read_json(path, default_factory)
                updater(state)
                state["updated_at"] = isoformat_utc()
                _write_json(path, state)
            return True
        except Exception as exc:
            last_error = exc
            _append_error_log(
                f"write_failed path={path.name} attempt={attempt} error={exc!r}"
            )
            time.sleep(0.1 * attempt)

    if last_error is not None:
        _append_error_log(
            f"write_aborted path={path.name} error={last_error!r}"
        )

    return False


def record_task_run(
    *,
    dag_id: str,
    task_id: str,
    run_id: str,
    task_label: str,
    status: str,
    started_at: datetime,
    ended_at: datetime,
    command: list[str] | None = None,
    cwd: str | None = None,
) -> bool:
    started_at_iso = isoformat_utc(started_at)
    ended_at_iso = isoformat_utc(ended_at)
    duration = max((ended_at - started_at).total_seconds(), 0.0)
    normalized_status = status.lower()

    def updater(state: dict[str, Any]) -> None:
        task_key = f"{dag_id}::{task_id}"
        run_key = f"{dag_id}::{run_id}"

        task_record = {
            "dag_id": dag_id,
            "task_id": task_id,
            "run_id": run_id,
            "task_label": task_label,
            "status": normalized_status,
            "started_at": started_at_iso,
            "ended_at": ended_at_iso,
            "duration_seconds": round(duration, 3),
            "command": command or [],
            "cwd": cwd or "",
        }

        state["tasks"][task_key] = task_record

        run_record = state["dag_runs"].setdefault(
            run_key,
            {
                "dag_id": dag_id,
                "run_id": run_id,
                "started_at": started_at_iso,
                "ended_at": ended_at_iso,
                "status": "running",
                "tasks": {},
            },
        )
        run_record["tasks"][task_id] = task_record

        current_run_start = iso_to_unix_seconds(run_record.get("started_at")) or math.inf
        task_start = iso_to_unix_seconds(started_at_iso) or math.inf
        if task_start < current_run_start:
            run_record["started_at"] = started_at_iso

        current_run_end = iso_to_unix_seconds(run_record.get("ended_at")) or 0.0
        task_end = iso_to_unix_seconds(ended_at_iso) or 0.0
        if task_end >= current_run_end:
            run_record["ended_at"] = ended_at_iso

        run_duration = duration_seconds(run_record.get("started_at"), run_record.get("ended_at")) or duration

        pipeline_record = state["pipelines"].setdefault(
            dag_id,
            {
                "dag_id": dag_id,
                "last_status": "unknown",
                "last_run_id": "",
                "last_run_at": None,
                "last_success_at": None,
                "last_duration_seconds": 0.0,
            },
        )

        if normalized_status == "failed":
            run_record["status"] = "failed"
            pipeline_record.update(
                {
                    "last_status": "failed",
                    "last_run_id": run_id,
                    "last_run_at": ended_at_iso,
                    "last_duration_seconds": round(run_duration, 3),
                }
            )
        elif task_id == FINAL_TASK_BY_DAG.get(dag_id):
            run_record["status"] = "success"
            pipeline_record.update(
                {
                    "last_status": "success",
                    "last_run_id": run_id,
                    "last_run_at": ended_at_iso,
                    "last_success_at": ended_at_iso,
                    "last_duration_seconds": round(run_duration, 3),
                }
            )

        state["dag_runs"] = _cleanup_old_runs(state["dag_runs"])

    return _safe_write(AIRFLOW_STATE_PATH, _default_airflow_state, updater)


def record_raw_load_run(summary: dict[str, Any]) -> bool:
    def updater(state: dict[str, Any]) -> None:
        state["last_run"] = summary

    return _safe_write(RAW_LOAD_STATE_PATH, _default_raw_load_state, updater)


def record_gx_checkpoint_run(summary: dict[str, Any]) -> bool:
    checkpoint_name = summary.get("checkpoint_name", "unknown_checkpoint")

    def updater(state: dict[str, Any]) -> None:
        state["checkpoints"][checkpoint_name] = summary

    return _safe_write(GX_STATE_PATH, _default_gx_state, updater)
