"""Submit Client 1 Spark Iceberg-load jobs through a local or remote submit container."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse


try:
    import docker  # type: ignore
except Exception:  # pragma: no cover - optional local dependency
    docker = None

try:
    import paramiko  # type: ignore
except Exception:  # pragma: no cover - optional local dependency
    paramiko = None


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
SPARK_DRIVER_HOST = os.getenv("CUSTOMERDNA_SPARK_DRIVER_HOST", "").strip()
SPARK_DRIVER_BIND_ADDRESS = os.getenv("CUSTOMERDNA_SPARK_DRIVER_BIND_ADDRESS", "").strip()
SPARK_DRIVER_PORT = os.getenv("CUSTOMERDNA_SPARK_DRIVER_PORT", "").strip()
SPARK_BLOCKMANAGER_PORT = os.getenv("CUSTOMERDNA_SPARK_BLOCKMANAGER_PORT", "").strip()
SPARK_EXECUTOR_MEMORY = os.getenv("CUSTOMERDNA_SPARK_EXECUTOR_MEMORY", "").strip()
SPARK_EXECUTOR_CORES = os.getenv("CUSTOMERDNA_SPARK_EXECUTOR_CORES", "").strip()
SPARK_CORES_MAX = os.getenv("CUSTOMERDNA_SPARK_CORES_MAX", "").strip()
SPARK_KERBEROS_PRINCIPAL = os.getenv(
    "CUSTOMERDNA_SPARK_KERBEROS_PRINCIPAL",
    "spark@CUSTOMERDNA.LOCAL",
).strip() or "spark@CUSTOMERDNA.LOCAL"
SPARK_KERBEROS_KEYTAB = os.getenv(
    "CUSTOMERDNA_SPARK_KERBEROS_KEYTAB",
    "/etc/security/keytabs/spark.service.keytab",
).strip() or "/etc/security/keytabs/spark.service.keytab"
HDFS_CANONICAL_HOST = (
    os.getenv("CUSTOMERDNA_HDFS_CANONICAL_HOST", "namenode.customerdna.local").strip()
    or "namenode.customerdna.local"
)
HDFS_NAMENODE_KERBEROS_PRINCIPAL = os.getenv(
    "CUSTOMERDNA_HDFS_NAMENODE_KERBEROS_PRINCIPAL",
    f"nn/{HDFS_CANONICAL_HOST}@CUSTOMERDNA.LOCAL",
).strip() or f"nn/{HDFS_CANONICAL_HOST}@CUSTOMERDNA.LOCAL"
HDFS_RPC_PROTECTION = os.getenv("CUSTOMERDNA_HDFS_RPC_PROTECTION", "privacy").strip() or "privacy"
HDFS_DATA_TRANSFER_PROTECTION = os.getenv(
    "CUSTOMERDNA_HDFS_DATA_TRANSFER_PROTECTION",
    "privacy",
).strip() or "privacy"
SPARK_REMOTE_SSH_HOST = os.getenv("CUSTOMERDNA_SPARK_REMOTE_SSH_HOST", "").strip()
SPARK_REMOTE_SSH_PORT = int(os.getenv("CUSTOMERDNA_SPARK_REMOTE_SSH_PORT", "22").strip() or "22")
SPARK_REMOTE_SSH_USER = os.getenv("CUSTOMERDNA_SPARK_REMOTE_SSH_USER", "").strip()
SPARK_REMOTE_SSH_KEY_PATH = os.getenv("CUSTOMERDNA_SPARK_REMOTE_SSH_KEY_PATH", "").strip()
SPARK_REMOTE_SSH_KNOWN_HOSTS_PATH = os.getenv(
    "CUSTOMERDNA_SPARK_REMOTE_SSH_KNOWN_HOSTS_PATH",
    "/opt/customerdna/.ssh/known_hosts",
).strip()
SPARK_REMOTE_SSH_CONNECT_TIMEOUT_SECONDS = int(
    os.getenv("CUSTOMERDNA_SPARK_REMOTE_SSH_CONNECT_TIMEOUT_SECONDS", "20").strip() or "20"
)
KRB5_CONFIG_PATH = os.getenv("CUSTOMERDNA_KRB5_CONFIG_PATH", "/etc/krb5.conf").strip() or "/etc/krb5.conf"
KRB5_CCACHE_PATH = os.getenv("CUSTOMERDNA_KRB5_CCACHE_PATH", "FILE:/tmp/krb5cc_spark").strip() or "FILE:/tmp/krb5cc_spark"
SPARK_JAAS_CONFIG_PATH = (
    os.getenv("CUSTOMERDNA_SPARK_JAAS_CONFIG_PATH", "/opt/spark/custom-conf/jaas.conf").strip()
    or "/opt/spark/custom-conf/jaas.conf"
)


def _unique_csv(values: list[str]) -> str:
    unique_values: list[str] = []
    for value in values:
        value = value.strip()
        if value and value not in unique_values:
            unique_values.append(value)
    return ",".join(unique_values)


@dataclass(frozen=True)
class SparkRawLoadResult:
    rows_loaded: int
    bronze_files_read: int
    duration_seconds: float
    stdout: str


def _should_use_remote_ssh() -> bool:
    return any(
        (
            SPARK_REMOTE_SSH_HOST,
            SPARK_REMOTE_SSH_USER,
            SPARK_REMOTE_SSH_KEY_PATH,
        )
    )


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
    if parsed_hdfs_uri.scheme == "hdfs" and parsed_hdfs_uri.hostname in {
        "localhost",
        "127.0.0.1",
        "namenode",
        "10.10.252.12",
    }:
        container_safe_hdfs_uri = urlunparse(
            (
                parsed_hdfs_uri.scheme,
                f"{HDFS_CANONICAL_HOST}:{parsed_hdfs_uri.port or 9000}",
                parsed_hdfs_uri.path,
                parsed_hdfs_uri.params,
                parsed_hdfs_uri.query,
                parsed_hdfs_uri.fragment,
            )
        )

    command = [
        SPARK_BIN,
        "--master",
        SPARK_MASTER_URL,
        "--principal",
        SPARK_KERBEROS_PRINCIPAL,
        "--keytab",
        SPARK_KERBEROS_KEYTAB,
        "--conf",
        "spark.eventLog.enabled=false",
        "--conf",
        f"spark.kerberos.access.hadoopFileSystems={container_safe_hdfs_uri}",
        "--conf",
        f"spark.hadoop.fs.defaultFS={container_safe_hdfs_uri}",
        "--conf",
        "spark.hadoop.hadoop.security.authentication=kerberos",
        "--conf",
        "spark.hadoop.hadoop.security.authorization=true",
        "--conf",
        f"spark.hadoop.hadoop.rpc.protection={HDFS_RPC_PROTECTION}",
        "--conf",
        f"spark.hadoop.dfs.namenode.kerberos.principal={HDFS_NAMENODE_KERBEROS_PRINCIPAL}",
        "--conf",
        f"spark.hadoop.dfs.data.transfer.protection={HDFS_DATA_TRANSFER_PROTECTION}",
        "--conf",
        "spark.hadoop.dfs.encrypt.data.transfer=true",
        "--conf",
        "spark.hadoop.dfs.client.use.datanode.hostname=true",
        "--conf",
        "spark.hadoop.dfs.client.use.legacy.blockreader.local=false",
        "--conf",
        "spark.hadoop.dfs.block.access.token.enable=true",
        "--conf",
        "spark.hadoop.dfs.client.https.need-auth=false",
        "--conf",
        "spark.hadoop.ipc.client.fallback-to-simple-auth-allowed=false",
        "--conf",
        f"spark.driverEnv.KRB5_CONFIG={KRB5_CONFIG_PATH}",
        "--conf",
        f"spark.driverEnv.KRB5CCNAME={KRB5_CCACHE_PATH}",
        "--conf",
        "spark.driverEnv.HADOOP_CONF_DIR=/etc/hadoop/conf",
        "--conf",
        f"spark.executorEnv.KRB5_CONFIG={KRB5_CONFIG_PATH}",
        "--conf",
        f"spark.executorEnv.KRB5CCNAME={KRB5_CCACHE_PATH}",
        "--conf",
        "spark.executorEnv.HADOOP_CONF_DIR=/etc/hadoop/conf",
        "--conf",
        f"spark.kerberos.principal={SPARK_KERBEROS_PRINCIPAL}",
        "--conf",
        f"spark.kerberos.keytab={SPARK_KERBEROS_KEYTAB}",
        "--conf",
        (
            "spark.driver.extraJavaOptions="
            f"-Djava.security.krb5.conf={KRB5_CONFIG_PATH} "
            f"-Djava.security.auth.login.config={SPARK_JAAS_CONFIG_PATH} "
            "-Djavax.security.auth.useSubjectCredsOnly=false"
        ),
        "--conf",
        (
            "spark.executor.extraJavaOptions="
            f"-Djava.security.krb5.conf={KRB5_CONFIG_PATH} "
            f"-Djava.security.auth.login.config={SPARK_JAAS_CONFIG_PATH} "
            "-Djavax.security.auth.useSubjectCredsOnly=false"
        ),
    ]

    if SPARK_DRIVER_HOST:
        command.extend(["--conf", f"spark.driver.host={SPARK_DRIVER_HOST}"])
    if SPARK_DRIVER_BIND_ADDRESS:
        command.extend(["--conf", f"spark.driver.bindAddress={SPARK_DRIVER_BIND_ADDRESS}"])
    if SPARK_DRIVER_PORT:
        command.extend(["--conf", f"spark.driver.port={SPARK_DRIVER_PORT}"])
    if SPARK_BLOCKMANAGER_PORT:
        command.extend(["--conf", f"spark.blockManager.port={SPARK_BLOCKMANAGER_PORT}"])
    if SPARK_EXECUTOR_MEMORY:
        command.extend(["--conf", f"spark.executor.memory={SPARK_EXECUTOR_MEMORY}"])
    if SPARK_EXECUTOR_CORES:
        command.extend(["--conf", f"spark.executor.cores={SPARK_EXECUTOR_CORES}"])
    if SPARK_CORES_MAX:
        command.extend(["--conf", f"spark.cores.max={SPARK_CORES_MAX}"])
    command.extend(
        [
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
    )

    return command


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


def _has_success_summary(output: str) -> bool:
    """Return True when the Spark loader printed its completion summary."""
    return bool(
        ROWS_LOADED_PATTERN.search(output)
        and FILES_READ_PATTERN.search(output)
        and DURATION_PATTERN.search(output)
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


def _validate_remote_ssh_configuration() -> None:
    missing = []
    if not SPARK_REMOTE_SSH_HOST:
        missing.append("CUSTOMERDNA_SPARK_REMOTE_SSH_HOST")
    if not SPARK_REMOTE_SSH_USER:
        missing.append("CUSTOMERDNA_SPARK_REMOTE_SSH_USER")
    if not SPARK_REMOTE_SSH_KEY_PATH:
        missing.append("CUSTOMERDNA_SPARK_REMOTE_SSH_KEY_PATH")
    if not SPARK_REMOTE_SSH_KNOWN_HOSTS_PATH:
        missing.append("CUSTOMERDNA_SPARK_REMOTE_SSH_KNOWN_HOSTS_PATH")

    if missing:
        raise RuntimeError(
            "Remote Spark execution is enabled, but required SSH settings are missing: "
            + ", ".join(missing)
        )

    if paramiko is None:
        raise RuntimeError(
            "Remote Spark execution requires the 'paramiko' package inside the Airflow runtime."
        )

    if not os.path.exists(SPARK_REMOTE_SSH_KEY_PATH):
        raise RuntimeError(
            "Remote Spark SSH key file does not exist inside the Airflow container: "
            f"{SPARK_REMOTE_SSH_KEY_PATH}"
        )
    if not os.path.exists(SPARK_REMOTE_SSH_KNOWN_HOSTS_PATH):
        raise RuntimeError(
            "Remote Spark known_hosts file does not exist inside the Airflow container: "
            f"{SPARK_REMOTE_SSH_KNOWN_HOSTS_PATH}"
        )


def _build_verified_ssh_client():
    assert paramiko is not None  # pragma: no cover - guarded by validation
    client = paramiko.SSHClient()
    client.load_host_keys(SPARK_REMOTE_SSH_KNOWN_HOSTS_PATH)
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    return client


def _run_with_remote_ssh(command: list[str]) -> str:
    _validate_remote_ssh_configuration()

    client = _build_verified_ssh_client()

    remote_command = shlex.join(
        ["docker", "exec", SPARK_SUBMIT_CONTAINER, *command]
    )

    try:
        client.connect(
            hostname=SPARK_REMOTE_SSH_HOST,
            port=SPARK_REMOTE_SSH_PORT,
            username=SPARK_REMOTE_SSH_USER,
            key_filename=SPARK_REMOTE_SSH_KEY_PATH,
            look_for_keys=False,
            allow_agent=False,
            timeout=SPARK_REMOTE_SSH_CONNECT_TIMEOUT_SECONDS,
            banner_timeout=SPARK_REMOTE_SSH_CONNECT_TIMEOUT_SECONDS,
            auth_timeout=SPARK_REMOTE_SSH_CONNECT_TIMEOUT_SECONDS,
        )

        _, stdout, stderr = client.exec_command(remote_command)
        channel = stdout.channel
        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []

        while True:
            while channel.recv_ready():
                chunk = channel.recv(4096).decode("utf-8", errors="replace")
                print(chunk, end="" if chunk.endswith("\n") else "\n")
                stdout_chunks.append(chunk)

            while channel.recv_stderr_ready():
                chunk = channel.recv_stderr(4096).decode("utf-8", errors="replace")
                print(chunk, end="" if chunk.endswith("\n") else "\n", file=sys.stderr)
                stderr_chunks.append(chunk)

            if channel.exit_status_ready():
                if not channel.recv_ready() and not channel.recv_stderr_ready():
                    break

            time.sleep(0.2)

        exit_code = channel.recv_exit_status()
        stdout_text = "".join(stdout_chunks)
        stderr_text = "".join(stderr_chunks)

        if exit_code == -1 and _has_success_summary(stdout_text):
            print(
                "[WARN] Remote SSH channel reported exit code -1 after the Spark loader "
                "printed a complete success summary. Treating the remote submit as successful."
            )
            return stdout_text

        if exit_code != 0:
            raise RuntimeError(
                "Remote Spark submit failed on "
                f"{SPARK_REMOTE_SSH_USER}@{SPARK_REMOTE_SSH_HOST}:{SPARK_REMOTE_SSH_PORT} "
                f"inside container '{SPARK_SUBMIT_CONTAINER}' with exit code {exit_code}.\n"
                f"stderr:\n{stderr_text}"
            )

        return stdout_text
    finally:
        client.close()


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
    print(f"[SPARK] Master URL: {SPARK_MASTER_URL}")
    print(f"[SPARK] Dataset key: {dataset_key}")
    print(f"[SPARK] Target table: raw_data.{target_table}")
    print(f"[SPARK] Bronze prefix: {bronze_prefix}")
    print(f"[SPARK] Original HDFS URI: {hdfs_namenode_uri}")
    print(f"[SPARK] Kerberos principal: {SPARK_KERBEROS_PRINCIPAL}")
    print(f"[SPARK] Kerberos keytab: {SPARK_KERBEROS_KEYTAB}")
    print(f"[SPARK] KRB5 config path: {KRB5_CONFIG_PATH}")
    print(f"[SPARK] Credential cache path: {KRB5_CCACHE_PATH}")
    print(f"[SPARK] JAAS config path: {SPARK_JAAS_CONFIG_PATH}")
    print(f"[SPARK] Expected rows: {expected_rows if expected_rows is not None else 0}")
    print(f"[SPARK] Expected bronze files: {expected_file_count if expected_file_count is not None else 0}")

    try:
        if _should_use_remote_ssh():
            print(
                "[SPARK] Remote execution: "
                f"{SPARK_REMOTE_SSH_USER}@{SPARK_REMOTE_SSH_HOST}:{SPARK_REMOTE_SSH_PORT}"
            )
            stdout = _run_with_remote_ssh(command)
        elif docker is not None:
            stdout = _run_with_docker_sdk(command)
        else:
            stdout = _run_with_docker_cli(command)
    except Exception as exc:
        print(f"[SPARK][ERROR] Submission failed before summary parsing: {exc}")
        print("[SPARK][ERROR] Python traceback follows:")
        print(traceback.format_exc().rstrip())
        raise

    return _parse_result(stdout)
