from __future__ import annotations

import json
import math
import os
import socket
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


MONITORING_ROOT = Path(__file__).resolve().parents[1]
if str(MONITORING_ROOT) not in sys.path:
    sys.path.insert(0, str(MONITORING_ROOT))

from shared.pipeline_metrics import (  # noqa: E402
    AIRFLOW_STATE_PATH,
    GX_STATE_PATH,
    RAW_LOAD_STATE_PATH,
    iso_to_unix_seconds,
)


EXPORTER_PORT = 9109
DEFAULT_HTTP_TIMEOUT_SECONDS = float(os.getenv("CUSTOMERDNA_MONITORING_HTTP_TIMEOUT_SECONDS", "5"))
DEFAULT_SOCKET_TIMEOUT_SECONDS = float(os.getenv("CUSTOMERDNA_MONITORING_SOCKET_TIMEOUT_SECONDS", "5"))
STALE_RUNNING_RECONCILIATION_SECONDS = float(
    os.getenv("CUSTOMERDNA_MONITORING_STALE_RUNNING_RECONCILIATION_SECONDS", "300")
)


def _normalized_http_url(value: str) -> str:
    normalized = value.strip()
    if not normalized.startswith(("http://", "https://")):
        normalized = f"http://{normalized}"
    return normalized


def _http_probe_status(value: str) -> int:
    try:
        request = Request(_normalized_http_url(value), headers={"User-Agent": "customerdna-monitoring-exporter"})
        with urlopen(request, timeout=DEFAULT_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
            return 1 if 200 <= response.status < 500 else 0
    except (URLError, TimeoutError, ValueError, OSError):
        return 0


def _socket_probe_status(host: str, port: int) -> int:
    try:
        with socket.create_connection((host, port), timeout=DEFAULT_SOCKET_TIMEOUT_SECONDS):
            return 1
    except OSError:
        return 0


def _escape_label_value(value: Any) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("\"", "\\\"")
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            return payload if isinstance(payload, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _append_metric(
    lines: list[str],
    name: str,
    value: float | int | None,
    labels: dict[str, Any] | None = None,
) -> None:
    if value is None:
        return

    numeric_value = float(value)
    if math.isnan(numeric_value) or math.isinf(numeric_value):
        return

    if labels:
        rendered_labels = ",".join(
            f'{key}="{_escape_label_value(label_value)}"'
            for key, label_value in sorted(labels.items())
        )
        lines.append(f"{name}{{{rendered_labels}}} {numeric_value}")
    else:
        lines.append(f"{name} {numeric_value}")


def _run_sort_timestamp(run_record: dict[str, Any]) -> float:
    return (
        iso_to_unix_seconds(run_record.get("ended_at"))
        or iso_to_unix_seconds(run_record.get("started_at"))
        or 0.0
    )


def _reconciled_run_status(run_record: dict[str, Any]) -> str:
    run_status = str(run_record.get("status", "")).lower()
    if run_status != "running":
        return run_status

    task_records = run_record.get("tasks", {})
    if not isinstance(task_records, dict) or not task_records:
        return run_status

    normalized_task_statuses = {
        str(task_record.get("status", "")).lower()
        for task_record in task_records.values()
        if isinstance(task_record, dict)
    }
    if "failed" in normalized_task_statuses:
        return "failed"

    if normalized_task_statuses and normalized_task_statuses == {"success"}:
        latest_task_end = max(
            (
                iso_to_unix_seconds(task_record.get("ended_at"))
                or iso_to_unix_seconds(task_record.get("started_at"))
                or 0.0
            )
            for task_record in task_records.values()
            if isinstance(task_record, dict)
        )
        if latest_task_end and (time.time() - latest_task_end) >= STALE_RUNNING_RECONCILIATION_SECONDS:
            return "success"

    return run_status


def _build_reconciled_pipeline_metrics(airflow_state: dict[str, Any]) -> list[dict[str, Any]]:
    pipelines = airflow_state.get("pipelines", {})
    dag_runs = airflow_state.get("dag_runs", {})

    latest_runs_by_dag: dict[str, dict[str, Any]] = {}
    for run_record in dag_runs.values():
        dag_id = run_record.get("dag_id")
        if not dag_id:
            continue

        existing_record = latest_runs_by_dag.get(dag_id)
        if existing_record is None or _run_sort_timestamp(run_record) >= _run_sort_timestamp(existing_record):
            latest_runs_by_dag[dag_id] = run_record

    all_dag_ids = set(pipelines.keys()) | set(latest_runs_by_dag.keys())
    reconciled_records: list[dict[str, Any]] = []

    for dag_id in sorted(all_dag_ids):
        pipeline_record = dict(pipelines.get(dag_id, {}))
        latest_run = latest_runs_by_dag.get(dag_id)

        if latest_run:
            latest_run_status = _reconciled_run_status(latest_run)
            latest_run_ended_at = latest_run.get("ended_at") or latest_run.get("started_at")

            pipeline_record.setdefault("dag_id", dag_id)

            # If the persisted pipeline snapshot is stale or missing, derive it from the
            # latest DAG run history so Grafana reflects the real latest pipeline outcome.
            pipeline_snapshot_ts = iso_to_unix_seconds(pipeline_record.get("last_run_at")) or 0.0
            latest_run_ts = iso_to_unix_seconds(latest_run_ended_at) or 0.0
            if latest_run_ts >= pipeline_snapshot_ts:
                pipeline_record["last_status"] = latest_run_status or pipeline_record.get("last_status", "unknown")
                pipeline_record["last_run_id"] = latest_run.get("run_id", pipeline_record.get("last_run_id", ""))
                pipeline_record["last_run_at"] = latest_run_ended_at

                started_at = latest_run.get("started_at")
                ended_at = latest_run.get("ended_at")
                started_at_seconds = iso_to_unix_seconds(started_at)
                ended_at_seconds = iso_to_unix_seconds(ended_at)
                if started_at_seconds is not None and ended_at_seconds is not None:
                    duration_value = ended_at_seconds - started_at_seconds
                    pipeline_record["last_duration_seconds"] = round(max(duration_value, 0.0), 3)

                if latest_run_status == "success" and latest_run_ended_at:
                    pipeline_record["last_success_at"] = latest_run_ended_at

        if pipeline_record:
            reconciled_records.append(pipeline_record)

    return reconciled_records


def build_metrics_payload() -> str:
    lines: list[str] = []

    service_targets = (
        {
            "service_name": "kafka_broker",
            "check_type": "tcp",
            "target": f"{os.getenv('CUSTOMERDNA_MONITORING_KAFKA_HOST', 'host.docker.internal')}:{os.getenv('CUSTOMERDNA_MONITORING_KAFKA_PORT', '9092')}",
            "value": _socket_probe_status(
                os.getenv("CUSTOMERDNA_MONITORING_KAFKA_HOST", "host.docker.internal"),
                int(os.getenv("CUSTOMERDNA_MONITORING_KAFKA_PORT", "9092")),
            ),
        },
        {
            "service_name": "hdfs_namenode_web",
            "check_type": "http",
            "target": _normalized_http_url(os.getenv("CUSTOMERDNA_MONITORING_HDFS_WEB_ENDPOINT", "host.docker.internal:9870")),
            "value": _http_probe_status(os.getenv("CUSTOMERDNA_MONITORING_HDFS_WEB_ENDPOINT", "host.docker.internal:9870")),
        },
        {
            "service_name": "hive_metastore",
            "check_type": "tcp",
            "target": f"{os.getenv('CUSTOMERDNA_MONITORING_HIVE_METASTORE_HOST', 'host.docker.internal')}:{os.getenv('CUSTOMERDNA_MONITORING_HIVE_METASTORE_PORT', '9083')}",
            "value": _socket_probe_status(
                os.getenv("CUSTOMERDNA_MONITORING_HIVE_METASTORE_HOST", "host.docker.internal"),
                int(os.getenv("CUSTOMERDNA_MONITORING_HIVE_METASTORE_PORT", "9083")),
            ),
        },
        {
            "service_name": "spark_master_ui",
            "check_type": "http",
            "target": _normalized_http_url(os.getenv("CUSTOMERDNA_MONITORING_SPARK_MASTER_UI_URL", "http://host.docker.internal:8086")),
            "value": _http_probe_status(os.getenv("CUSTOMERDNA_MONITORING_SPARK_MASTER_UI_URL", "http://host.docker.internal:8086")),
        },
        {
            "service_name": "spark_thrift_server",
            "check_type": "tcp",
            "target": f"{os.getenv('CUSTOMERDNA_MONITORING_SPARK_THRIFT_HOST', 'host.docker.internal')}:{os.getenv('CUSTOMERDNA_MONITORING_SPARK_THRIFT_PORT', '10000')}",
            "value": _socket_probe_status(
                os.getenv("CUSTOMERDNA_MONITORING_SPARK_THRIFT_HOST", "host.docker.internal"),
                int(os.getenv("CUSTOMERDNA_MONITORING_SPARK_THRIFT_PORT", "10000")),
            ),
        },
        {
            "service_name": "trino_query_service",
            "check_type": "http",
            "target": _normalized_http_url(os.getenv("CUSTOMERDNA_MONITORING_TRINO_URL", "http://host.docker.internal:8088")) + "/v1/info",
            "value": _http_probe_status(os.getenv("CUSTOMERDNA_MONITORING_TRINO_URL", "http://host.docker.internal:8088") + "/v1/info"),
        },
    )

    for service in service_targets:
        _append_metric(
            lines,
            "customerdna_service_health_status",
            service["value"],
            {
                "service_name": service["service_name"],
                "check_type": service["check_type"],
                "target": service["target"],
            },
        )

    airflow_state = _read_json(AIRFLOW_STATE_PATH)
    tasks = airflow_state.get("tasks", {})
    for task in tasks.values():
        labels = {
            "dag_id": task.get("dag_id", "unknown"),
            "task_id": task.get("task_id", "unknown"),
            "task_label": task.get("task_label", "unknown"),
        }
        _append_metric(
            lines,
            "customerdna_task_last_status",
            1 if task.get("status") == "success" else 0,
            labels,
        )
        _append_metric(
            lines,
            "customerdna_task_last_duration_seconds",
            task.get("duration_seconds"),
            labels,
        )
        _append_metric(
            lines,
            "customerdna_task_last_run_timestamp_seconds",
            iso_to_unix_seconds(task.get("ended_at")),
            labels,
        )

    for pipeline in _build_reconciled_pipeline_metrics(airflow_state):
        labels = {
            "dag_id": pipeline.get("dag_id", "unknown"),
        }
        _append_metric(
            lines,
            "customerdna_pipeline_last_status",
            1 if pipeline.get("last_status") == "success" else 0,
            labels,
        )
        _append_metric(
            lines,
            "customerdna_pipeline_last_duration_seconds",
            pipeline.get("last_duration_seconds"),
            labels,
        )
        _append_metric(
            lines,
            "customerdna_pipeline_last_run_timestamp_seconds",
            iso_to_unix_seconds(pipeline.get("last_run_at")),
            labels,
        )
        _append_metric(
            lines,
            "customerdna_pipeline_last_success_timestamp_seconds",
            iso_to_unix_seconds(pipeline.get("last_success_at")),
            labels,
        )

    raw_load_state = _read_json(RAW_LOAD_STATE_PATH)
    raw_last_run = raw_load_state.get("last_run") or {}
    if raw_last_run:
        _append_metric(
            lines,
            "customerdna_raw_last_run_status",
            1 if raw_last_run.get("status") == "success" else 0,
        )
        _append_metric(
            lines,
            "customerdna_raw_last_run_duration_seconds",
            raw_last_run.get("duration_seconds"),
        )
        _append_metric(
            lines,
            "customerdna_raw_last_run_rows_inserted_total",
            raw_last_run.get("total_rows_inserted"),
        )
        _append_metric(
            lines,
            "customerdna_raw_last_run_bronze_files_total",
            raw_last_run.get("total_bronze_files"),
        )
        _append_metric(
            lines,
            "customerdna_raw_last_run_successful_files",
            raw_last_run.get("successful_files"),
        )
        _append_metric(
            lines,
            "customerdna_raw_last_run_failed_files",
            raw_last_run.get("failed_files"),
        )
        _append_metric(
            lines,
            "customerdna_raw_last_run_skipped_files",
            raw_last_run.get("skipped_files"),
        )
        _append_metric(
            lines,
            "customerdna_raw_last_run_refreshed_files",
            raw_last_run.get("refreshed_files"),
        )
        _append_metric(
            lines,
            "customerdna_raw_last_run_incremental_files",
            raw_last_run.get("incremental_files"),
        )
        _append_metric(
            lines,
            "customerdna_raw_last_run_timestamp_seconds",
            iso_to_unix_seconds(raw_last_run.get("ended_at")),
        )

        for table in raw_last_run.get("tables", []):
            labels = {
                "table_name": table.get("table_name", "unknown"),
                "load_mode": table.get("load_mode", "unknown"),
            }
            _append_metric(
                lines,
                "customerdna_raw_table_last_status",
                1 if table.get("status") == "success" else 0,
                labels,
            )
            _append_metric(
                lines,
                "customerdna_raw_table_last_rows_inserted",
                table.get("rows_inserted"),
                labels,
            )
            _append_metric(
                lines,
                "customerdna_raw_table_last_source_rows",
                table.get("source_rows"),
                labels,
            )
            _append_metric(
                lines,
                "customerdna_raw_table_last_bronze_files_read",
                table.get("bronze_files_read"),
                labels,
            )
            _append_metric(
                lines,
                "customerdna_raw_table_last_duration_seconds",
                table.get("duration_seconds"),
                labels,
            )

    gx_state = _read_json(GX_STATE_PATH)
    checkpoints = gx_state.get("checkpoints", {})
    for checkpoint in checkpoints.values():
        labels = {
            "checkpoint_name": checkpoint.get("checkpoint_name", "unknown"),
        }
        _append_metric(
            lines,
            "customerdna_gx_checkpoint_last_status",
            1 if checkpoint.get("status") == "success" else 0,
            labels,
        )
        _append_metric(
            lines,
            "customerdna_gx_checkpoint_last_duration_seconds",
            checkpoint.get("duration_seconds"),
            labels,
        )
        _append_metric(
            lines,
            "customerdna_gx_checkpoint_validation_results",
            checkpoint.get("validation_results"),
            labels,
        )
        _append_metric(
            lines,
            "customerdna_gx_checkpoint_last_run_timestamp_seconds",
            iso_to_unix_seconds(checkpoint.get("ended_at")),
            labels,
        )

    return "\n".join(lines) + "\n"


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            body = b"ok\n"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path != "/metrics":
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
            return

        body = build_metrics_payload().encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", EXPORTER_PORT), MetricsHandler)
    print(f"CustomerDNA pipeline metrics exporter listening on port {EXPORTER_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
