from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


MONITORING_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MONITORING_ROOT.parent
APP_ROOT = SRC_ROOT.parent

AIRFLOW_LOG_ROOT = SRC_ROOT / "airflow" / "logs" / "system"
KAFKA_LOG_ROOT = SRC_ROOT / "streaming" / "kafka" / "logs"
MONITORING_LOG_ROOT = MONITORING_ROOT / "logs"
GRAFANA_LOG_ROOT = MONITORING_LOG_ROOT / "grafana"
PROMETHEUS_LOG_ROOT = MONITORING_LOG_ROOT / "prometheus"


@dataclass(frozen=True)
class ContainerLogSpec:
    group: str
    container_name: str
    output_path: Path
    description: str


LOG_SPECS: tuple[ContainerLogSpec, ...] = (
    ContainerLogSpec(
        group="airflow",
        container_name="customerdna_airflow_api_server",
        output_path=AIRFLOW_LOG_ROOT / "airflow_api_server.log",
        description="Airflow API server runtime log",
    ),
    ContainerLogSpec(
        group="airflow",
        container_name="customerdna_airflow_scheduler",
        output_path=AIRFLOW_LOG_ROOT / "airflow_scheduler.log",
        description="Airflow scheduler runtime log",
    ),
    ContainerLogSpec(
        group="airflow",
        container_name="customerdna_airflow_dag_processor",
        output_path=AIRFLOW_LOG_ROOT / "airflow_dag_processor.log",
        description="Airflow DAG processor runtime log",
    ),
    ContainerLogSpec(
        group="airflow",
        container_name="customerdna_airflow_triggerer",
        output_path=AIRFLOW_LOG_ROOT / "airflow_triggerer.log",
        description="Airflow triggerer runtime log",
    ),
    ContainerLogSpec(
        group="airflow",
        container_name="customerdna_airflow_postgres",
        output_path=AIRFLOW_LOG_ROOT / "airflow_postgres.log",
        description="Airflow metadata PostgreSQL log",
    ),
    ContainerLogSpec(
        group="kafka",
        container_name="broker",
        output_path=KAFKA_LOG_ROOT / "broker.log",
        description="Kafka broker runtime log",
    ),
    ContainerLogSpec(
        group="kafka",
        container_name="kafka-ui",
        output_path=KAFKA_LOG_ROOT / "kafka_ui.log",
        description="Kafka UI runtime log",
    ),
    ContainerLogSpec(
        group="monitoring",
        container_name="customerdna_grafana",
        output_path=GRAFANA_LOG_ROOT / "grafana.log",
        description="Grafana runtime log",
    ),
    ContainerLogSpec(
        group="monitoring",
        container_name="customerdna_prometheus",
        output_path=PROMETHEUS_LOG_ROOT / "prometheus.log",
        description="Prometheus runtime log",
    ),
    ContainerLogSpec(
        group="monitoring",
        container_name="customerdna_postgres_exporter",
        output_path=PROMETHEUS_LOG_ROOT / "postgres_exporter.log",
        description="PostgreSQL exporter runtime log",
    ),
    ContainerLogSpec(
        group="monitoring",
        container_name="customerdna_cadvisor",
        output_path=PROMETHEUS_LOG_ROOT / "cadvisor.log",
        description="cAdvisor runtime log",
    ),
    ContainerLogSpec(
        group="monitoring",
        container_name="customerdna_pipeline_metrics_exporter",
        output_path=PROMETHEUS_LOG_ROOT / "pipeline_metrics_exporter.log",
        description="Pipeline metrics exporter runtime log",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Docker container logs into organized project log files.",
    )
    parser.add_argument(
        "--group",
        choices=["all", "airflow", "kafka", "monitoring"],
        default="all",
        help="Limit export to one service group.",
    )
    parser.add_argument(
        "--tail",
        type=int,
        default=5000,
        help="How many recent log lines to capture per container.",
    )
    parser.add_argument(
        "--since",
        default="24h",
        help="Docker log time window, for example '2h', '30m', or an RFC3339 timestamp.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to the existing log files instead of replacing them.",
    )
    return parser.parse_args()


def selected_specs(group: str) -> Iterable[ContainerLogSpec]:
    if group == "all":
        return LOG_SPECS
    return [spec for spec in LOG_SPECS if spec.group == group]


def ensure_output_dirs() -> None:
    AIRFLOW_LOG_ROOT.mkdir(parents=True, exist_ok=True)
    KAFKA_LOG_ROOT.mkdir(parents=True, exist_ok=True)
    GRAFANA_LOG_ROOT.mkdir(parents=True, exist_ok=True)
    PROMETHEUS_LOG_ROOT.mkdir(parents=True, exist_ok=True)


def render_header(spec: ContainerLogSpec, tail: int, since: str) -> str:
    generated_at = datetime.now().isoformat(timespec="seconds")
    return (
        "=" * 80
        + "\n"
        + "CUSTOMERDNA AI - RUNTIME LOG EXPORT\n"
        + "=" * 80
        + "\n"
        + f"Generated at: {generated_at}\n"
        + f"Container: {spec.container_name}\n"
        + f"Group: {spec.group}\n"
        + f"Description: {spec.description}\n"
        + f"Tail lines: {tail}\n"
        + f"Since: {since}\n"
        + "=" * 80
        + "\n"
    )


def export_one(spec: ContainerLogSpec, tail: int, since: str, append: bool) -> tuple[bool, str]:
    command = [
        "docker",
        "logs",
        "--timestamps",
        "--tail",
        str(tail),
        "--since",
        since,
        spec.container_name,
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    body = completed.stdout
    if completed.stderr:
        if body and not body.endswith("\n"):
            body += "\n"
        body += completed.stderr

    if completed.returncode != 0:
        body = (
            f"[ERROR] Failed to export logs for container '{spec.container_name}'.\n"
            f"[COMMAND] {' '.join(command)}\n"
            f"[RETURN CODE] {completed.returncode}\n\n"
            f"{body}"
        )

    write_mode = "a" if append else "w"
    with spec.output_path.open(write_mode, encoding="utf-8") as handle:
        if append:
            handle.write("\n")
        handle.write(render_header(spec, tail, since))
        handle.write(body)
        if body and not body.endswith("\n"):
            handle.write("\n")

    return completed.returncode == 0, str(spec.output_path)


def main() -> int:
    args = parse_args()
    ensure_output_dirs()

    exported = 0
    failed = 0

    print("=" * 80)
    print("CUSTOMERDNA AI - CONTAINER LOG EXPORT")
    print("=" * 80)
    print(f"Group: {args.group}")
    print(f"Tail lines per container: {args.tail}")
    print(f"Since: {args.since}")
    print(f"Append mode: {args.append}")
    print("=" * 80)

    for spec in selected_specs(args.group):
        success, output_path = export_one(spec, args.tail, args.since, args.append)
        exported += 1
        status_label = "SUCCESS" if success else "FAILED"
        print(f"[{status_label}] {spec.container_name} -> {output_path}")
        if not success:
            failed += 1

    print("=" * 80)
    print(f"Containers processed: {exported}")
    print(f"Containers failed: {failed}")
    print("=" * 80)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
