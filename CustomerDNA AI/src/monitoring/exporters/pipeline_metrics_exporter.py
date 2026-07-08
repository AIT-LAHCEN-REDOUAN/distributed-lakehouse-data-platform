from __future__ import annotations

import json
import math
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


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


def build_metrics_payload() -> str:
    lines: list[str] = []

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

    pipelines = airflow_state.get("pipelines", {})
    for pipeline in pipelines.values():
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
