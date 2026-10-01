from __future__ import annotations

import shutil
import subprocess
from pathlib import Path, PurePosixPath


PLAIN_BASELINE_COMMIT = "b2906757"

OLD_DEPLOY_PREFIX = PurePosixPath(
    "CustomerDNA AI/src/deployments/distributed_pc_control_plane"
)

OLD_SOURCE_MAPPINGS: list[tuple[PurePosixPath, PurePosixPath]] = [
    (
        PurePosixPath("CustomerDNA AI/src/airflow"),
        PurePosixPath("control_plane_pc/airflow"),
    ),
    (
        PurePosixPath("CustomerDNA AI/src/monitoring"),
        PurePosixPath("control_plane_pc/monitoring"),
    ),
    (
        PurePosixPath("CustomerDNA AI/src/catalog"),
        PurePosixPath("control_plane_pc/project_root/src/catalog"),
    ),
    (
        PurePosixPath("CustomerDNA AI/src/lake"),
        PurePosixPath("control_plane_pc/project_root/src/lake"),
    ),
    (
        PurePosixPath("CustomerDNA AI/src/monitoring"),
        PurePosixPath("control_plane_pc/project_root/src/monitoring"),
    ),
    (
        PurePosixPath("CustomerDNA AI/src/processing"),
        PurePosixPath("control_plane_pc/project_root/src/processing"),
    ),
    (
        PurePosixPath("CustomerDNA AI/src/quality"),
        PurePosixPath("control_plane_pc/project_root/src/quality"),
    ),
    (
        PurePosixPath("CustomerDNA AI/src/query"),
        PurePosixPath("control_plane_pc/project_root/src/query"),
    ),
    (
        PurePosixPath("CustomerDNA AI/src/streaming"),
        PurePosixPath("control_plane_pc/project_root/src/streaming"),
    ),
    (
        PurePosixPath("CustomerDNA AI/src/transformation"),
        PurePosixPath("control_plane_pc/project_root/src/transformation"),
    ),
]

EXTRA_FILE_MAPPINGS: list[tuple[PurePosixPath, PurePosixPath]] = [
    (
        PurePosixPath(
            "CustomerDNA AI/src/processing/spark/jobs/client_1/load_hdfs_bronze_to_iceberg.py"
        ),
        PurePosixPath("vm2/app/jobs/client_1/load_hdfs_bronze_to_iceberg.py"),
    ),
]

UNWANTED_PATHS = [
    "windows_kerberos_client",
    "control_plane_pc/certs",
    "control_plane_pc/tls_gateway",
    "control_plane_pc/vm2-dag-debug.txt",
    "control_plane_pc/vm3-dag-debug.txt",
    "control_plane_pc/vm3_executor_logs.txt",
    "vm1/kerberos",
    "vm2/kerberos",
    "vm3/kerberos",
    "vm1/hdfs/tls",
    "vm2/hdfs/tls",
    "vm3/hdfs/tls",
    "vm2/trino/caddy",
    "vm2/trino/nginx",
    "vm2/app/jobs/client_1/smoke_test_hdfs_executor_kerberos.py",
    "control_plane_pc/project_root/src/processing/spark/jobs/client_1/smoke_test_hdfs_executor_kerberos.py",
    "vm1/spark/config/jaas.conf",
    "vm2/spark/config/jaas.conf",
    "vm3/spark/config/jaas.conf",
    "control_plane_pc/project_root/src/processing/spark/config/jaas.conf",
    "control_plane_pc/spark_submit_config/spark-defaults.conf.bak",
]


def run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def repo_root_for(base_dir: Path) -> Path:
    return Path(
        subprocess.run(
            ["git", "-C", str(base_dir), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )


def tracked_files(repo_root: Path, prefix: PurePosixPath) -> list[PurePosixPath]:
    output = run_git(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        PLAIN_BASELINE_COMMIT,
        "--",
        prefix.as_posix(),
    )
    return [PurePosixPath(line) for line in output.splitlines() if line.strip()]


def file_bytes(repo_root: Path, repo_path: PurePosixPath) -> bytes:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "show",
            f"{PLAIN_BASELINE_COMMIT}:{repo_path.as_posix()}",
        ],
        check=True,
        capture_output=True,
    )
    return result.stdout


def restore_prefix(
    repo_root: Path,
    old_prefix: PurePosixPath,
    target_root: Path,
) -> int:
    count = 0
    for repo_path in tracked_files(repo_root, old_prefix):
        relative = repo_path.relative_to(old_prefix)
        target_path = target_root / Path(*relative.parts)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(file_bytes(repo_root, repo_path))
        count += 1
    return count


def restore_file(repo_root: Path, old_file: PurePosixPath, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(file_bytes(repo_root, old_file))


def patch_control_plane(compose_path: Path, env_example_path: Path) -> None:
    compose_text = compose_path.read_text(encoding="utf-8")
    replacements = {
        "../../../airflow/dags": "./airflow/dags",
        "../../../airflow/plugins": "./airflow/plugins",
        "../../../airflow/config": "./airflow/config",
        "../../../airflow/requirements.txt": "./airflow/requirements.txt",
        "${CUSTOMERDNA_PROJECT_ROOT_MOUNT:-../../../..}": "${CUSTOMERDNA_PROJECT_ROOT_MOUNT:-./project_root}",
        "../../../monitoring:${CUSTOMERDNA_MONITORING_ROOT_IN_CONTAINER:-/monitoring}:ro": "./monitoring:${CUSTOMERDNA_MONITORING_ROOT_IN_CONTAINER:-/monitoring}:ro",
        "./prometheus.yml:/etc/prometheus/prometheus.yml:ro": "./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro",
        "./grafana/provisioning:/etc/grafana/provisioning:ro": "./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro",
        "../../../monitoring/grafana/dashboards:/var/lib/grafana/dashboards/customerdna:ro": "./monitoring/grafana/dashboards:/var/lib/grafana/dashboards/customerdna:ro",
    }
    for old, new in replacements.items():
        compose_text = compose_text.replace(old, new)
    compose_path.write_text(compose_text, encoding="utf-8")

    env_text = env_example_path.read_text(encoding="utf-8")
    env_text = env_text.replace(
        "CUSTOMERDNA_PROJECT_ROOT_MOUNT=../../../..",
        "CUSTOMERDNA_PROJECT_ROOT_MOUNT=./project_root",
    )
    if "CUSTOMERDNA_HDFS_ACCESS_MODE=" not in env_text:
        env_text += "\nCUSTOMERDNA_HDFS_ACCESS_MODE=webhdfs\n"
    env_example_path.write_text(env_text, encoding="utf-8")


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink()


def copy_if_exists(source: Path, target: Path) -> None:
    if source.exists():
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    repo_root = repo_root_for(base_dir)

    restored = restore_prefix(repo_root, OLD_DEPLOY_PREFIX, base_dir)

    for old_prefix, new_prefix in OLD_SOURCE_MAPPINGS:
        restore_prefix(repo_root, old_prefix, base_dir / Path(*new_prefix.parts))

    for old_file, new_file in EXTRA_FILE_MAPPINGS:
        restore_file(repo_root, old_file, base_dir / Path(*new_file.parts))

    control_plane_dir = base_dir / "control_plane_pc"
    (control_plane_dir / "airflow" / "plugins").mkdir(parents=True, exist_ok=True)
    (control_plane_dir / "airflow" / "config").mkdir(parents=True, exist_ok=True)
    (control_plane_dir / "runtime" / "airflow" / "logs").mkdir(parents=True, exist_ok=True)
    (control_plane_dir / "runtime" / "monitoring").mkdir(parents=True, exist_ok=True)

    patch_control_plane(
        control_plane_dir / "docker-compose.yml",
        control_plane_dir / ".env.example",
    )

    copy_if_exists(control_plane_dir / ".env.example", control_plane_dir / ".env")
    copy_if_exists(base_dir / "vm1" / ".env.example", base_dir / "vm1" / ".env")
    copy_if_exists(base_dir / "vm2" / ".env.example", base_dir / "vm2" / ".env")
    copy_if_exists(base_dir / "vm3" / ".env.example", base_dir / "vm3" / ".env")

    for unwanted in UNWANTED_PATHS:
        remove_path(base_dir / unwanted)

    print(
        f"Rebuilt distributed_pc_control_plane_2 from plain baseline {PLAIN_BASELINE_COMMIT}. "
        f"Restored {restored} deployment files and refreshed local source copies."
    )


if __name__ == "__main__":
    main()
