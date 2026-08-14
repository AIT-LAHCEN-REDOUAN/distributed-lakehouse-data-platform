"""Minimal Spark smoke test for executor-side Kerberos access to HDFS."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import socket
import subprocess
import time
import traceback
from datetime import datetime
from urllib.parse import quote, urlparse

from pyspark.sql import SparkSession


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Spark executor Kerberos access to an HDFS path."
    )
    parser.add_argument("--hdfs-path", required=True)
    parser.add_argument("--expected-min-records", default=1, type=int)
    return parser.parse_args()


HDFS_TOKEN_RENEWAL_EXCLUDE = (
    os.getenv(
        "CUSTOMERDNA_HDFS_TOKEN_RENEWAL_EXCLUDE",
        "namenode.customerdna.local,namenode,10.10.252.12",
    ).strip()
    or "namenode.customerdna.local,namenode,10.10.252.12"
)
SPARK_DRIVER_HOST = (
    os.getenv("CUSTOMERDNA_SPARK_DRIVER_HOST", "").strip()
    or os.getenv("VM2_HOST_IP", "").strip()
    or "10.10.252.12"
)
SPARK_DRIVER_BIND_ADDRESS = (
    os.getenv("CUSTOMERDNA_SPARK_DRIVER_BIND_ADDRESS", "").strip() or "0.0.0.0"
)
SPARK_DRIVER_PORT = os.getenv("CUSTOMERDNA_SPARK_DRIVER_PORT", "").strip() or "35001"
SPARK_BLOCKMANAGER_PORT = (
    os.getenv("CUSTOMERDNA_SPARK_BLOCKMANAGER_PORT", "").strip() or "35002"
)
SPARK_KERBEROS_PRINCIPAL = (
    os.getenv("CUSTOMERDNA_SPARK_KERBEROS_PRINCIPAL", "").strip()
    or "spark@CUSTOMERDNA.LOCAL"
)
SPARK_KERBEROS_KEYTAB = (
    os.getenv("KRB5_CLIENT_KTNAME", "").strip()
    or "/etc/security/keytabs/spark.service.keytab"
)
HDFS_SAFEMODE_WAIT_TIMEOUT_SECONDS = max(
    30,
    int(os.getenv("CUSTOMERDNA_HDFS_SAFEMODE_WAIT_TIMEOUT_SECONDS", "180")),
)
HDFS_SAFEMODE_POLL_INTERVAL_SECONDS = max(
    1,
    int(os.getenv("CUSTOMERDNA_HDFS_SAFEMODE_POLL_INTERVAL_SECONDS", "5")),
)


def build_fs_shell_snippet(fs_args: str) -> str:
    # Some images expose HDFS shell commands as `hdfs dfs`, others as `hadoop fs`.
    return (
        "export HADOOP_CONF_DIR=/etc/hadoop/conf; "
        "run_fs() { "
        "if command -v hdfs >/dev/null 2>&1; then hdfs dfs \"$@\"; "
        "elif command -v hadoop >/dev/null 2>&1; then hadoop fs \"$@\"; "
        "else echo '__CUSTOMERDNA_FS_CLI_MISSING__' >&2; return 127; "
        "fi; "
        "}; "
        f"run_fs {fs_args}"
    )


def build_spark_session(hdfs_path: str) -> SparkSession:
    app_suffix = hdfs_path.strip("/").replace("/", "_").replace("*", "wildcard")[-60:]
    parsed = urlparse(hdfs_path)
    hdfs_fs_uri = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""
    return (
        SparkSession.builder.appName(f"customerdna-client1-hdfs-kerberos-smoke-{app_suffix}")
        .config("spark.eventLog.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.driver.host", SPARK_DRIVER_HOST)
        .config("spark.driver.bindAddress", SPARK_DRIVER_BIND_ADDRESS)
        .config("spark.driver.port", SPARK_DRIVER_PORT)
        .config("spark.blockManager.port", SPARK_BLOCKMANAGER_PORT)
        .config("spark.driverEnv.CUSTOMERDNA_SPARK_KERBEROS_PRINCIPAL", SPARK_KERBEROS_PRINCIPAL)
        .config("spark.driverEnv.KRB5_CLIENT_KTNAME", SPARK_KERBEROS_KEYTAB)
        .config("spark.executorEnv.CUSTOMERDNA_SPARK_KERBEROS_PRINCIPAL", SPARK_KERBEROS_PRINCIPAL)
        .config("spark.executorEnv.KRB5_CLIENT_KTNAME", SPARK_KERBEROS_KEYTAB)
        .config("spark.kerberos.principal", SPARK_KERBEROS_PRINCIPAL)
        .config("spark.kerberos.keytab", SPARK_KERBEROS_KEYTAB)
        .config("spark.security.credentials.hadoopfs.enabled", "false")
        .config("spark.hadoop.hadoop.security.token.service.use_ip", "false")
        .config("spark.hadoop.fs.defaultFS", hdfs_fs_uri)
        .config("spark.hadoop.hadoop.security.authentication", "kerberos")
        .config("spark.hadoop.hadoop.security.authorization", "true")
        .config(
            "spark.hadoop.mapreduce.job.hdfs-servers.token-renewal.exclude",
            HDFS_TOKEN_RENEWAL_EXCLUDE,
        )
        .enableHiveSupport()
        .getOrCreate()
    )


def resolve_kerberos_identity(spark: SparkSession) -> tuple[str, str]:
    principal = (
        spark.conf.get("spark.kerberos.principal", "").strip()
        or os.getenv("CUSTOMERDNA_SPARK_KERBEROS_PRINCIPAL", "").strip()
    )
    keytab = (
        spark.conf.get("spark.kerberos.keytab", "").strip()
        or os.getenv("KRB5_CLIENT_KTNAME", "").strip()
    )
    return principal, keytab


def force_hadoop_kerberos_login(spark: SparkSession) -> None:
    sc = spark.sparkContext
    hadoop_conf = sc._jsc.hadoopConfiguration()
    hadoop_conf.set(
        "mapreduce.job.hdfs-servers.token-renewal.exclude",
        HDFS_TOKEN_RENEWAL_EXCLUDE,
    )
    hadoop_conf.set("hadoop.security.token.service.use_ip", "false")
    ugi = sc._jvm.org.apache.hadoop.security.UserGroupInformation
    ugi.setConfiguration(hadoop_conf)

    principal, keytab = resolve_kerberos_identity(spark)
    print("[KERBEROS] Preparing explicit Hadoop login from keytab")
    print(f"[KERBEROS] Principal: {principal or '<unset>'}")
    print(f"[KERBEROS] Keytab: {keytab or '<unset>'}")
    print(f"[KERBEROS] Security enabled: {ugi.isSecurityEnabled()}")

    if not principal:
        raise RuntimeError("Spark Kerberos principal is not configured.")
    if not keytab:
        raise RuntimeError("Spark Kerberos keytab is not configured.")
    if not os.path.exists(keytab):
        raise RuntimeError(f"Spark Kerberos keytab does not exist on the driver: {keytab}")

    ugi.loginUserFromKeytab(principal, keytab)

    login_user = ugi.getLoginUser()
    current_user = ugi.getCurrentUser()
    print(f"[KERBEROS] Login user after refresh: {login_user.getUserName()}")
    print(f"[KERBEROS] Login auth method after refresh: {login_user.getAuthenticationMethod()}")
    print(f"[KERBEROS] Current user after refresh: {current_user.getUserName()}")
    print(f"[KERBEROS] Current auth method after refresh: {current_user.getAuthenticationMethod()}")
    print(
        "[KERBEROS] Current user has Kerberos credentials after refresh: "
        f"{current_user.hasKerberosCredentials()}"
    )


def log_driver_context(spark: SparkSession, hdfs_path: str) -> None:
    sc = spark.sparkContext
    hadoop_conf = sc._jsc.hadoopConfiguration()

    print("[DRIVER] Spark context")
    print(f"[DRIVER] Spark version: {spark.version}")
    print(f"[DRIVER] App name: {sc.appName}")
    print(f"[DRIVER] App id: {sc.applicationId}")
    print(f"[DRIVER] Master: {sc.master}")
    print(f"[DRIVER] HDFS path under test: {hdfs_path}")

    for conf_key in [
        "spark.kerberos.principal",
        "spark.kerberos.keytab",
        "spark.kerberos.renewal.credentials",
        "spark.kerberos.access.hadoopFileSystems",
        "spark.security.credentials.hadoopfs.enabled",
        "spark.hadoop.hadoop.security.token.service.use_ip",
        "spark.hadoop.mapreduce.job.hdfs-servers.token-renewal.exclude",
        "spark.executor.instances",
        "spark.executor.memory",
        "spark.executor.cores",
        "spark.cores.max",
        "spark.driver.host",
        "spark.driver.bindAddress",
        "spark.driver.port",
        "spark.blockManager.port",
    ]:
        print(f"[DRIVER] {conf_key}={spark.conf.get(conf_key, '<unset>')}")

    for conf_key in [
        "fs.defaultFS",
        "hadoop.security.token.service.use_ip",
        "hadoop.security.authentication",
        "hadoop.rpc.protection",
        "dfs.namenode.kerberos.principal",
        "dfs.data.transfer.protection",
        "dfs.encrypt.data.transfer",
        "dfs.client.use.datanode.hostname",
        "mapreduce.job.hdfs-servers.token-renewal.exclude",
    ]:
        print(f"[DRIVER] {conf_key}={hadoop_conf.get(conf_key) or '<unset>'}")

    for env_key in [
        "KRB5_CONFIG",
        "KRB5CCNAME",
        "KRB5_CLIENT_KTNAME",
        "CUSTOMERDNA_SPARK_KERBEROS_PRINCIPAL",
        "HADOOP_CONF_DIR",
        "HOSTNAME",
    ]:
        print(f"[DRIVER] {env_key}={os.getenv(env_key, '<unset>')}")

    try:
        parsed = urlparse(hdfs_path)
        print(
            "[DRIVER] Driver-side HDFS JVM preflight skipped to avoid the known "
            "submit-container hostname resolution issue."
        )
        print(
            f"[DRIVER] Parsed HDFS endpoint: scheme={parsed.scheme or '<unset>'}, "
            f"authority={parsed.netloc or '<unset>'}, path={parsed.path or '<unset>'}"
        )
    except Exception as exc:
        print(f"[DRIVER][WARN] Driver-side HDFS path parsing failed: {exc}")
        print(traceback.format_exc().rstrip())


def discover_hdfs_files_via_cli(hdfs_path: str) -> list[str]:
    command = [
        "sh",
        "-lc",
        build_fs_shell_snippet(f"-ls {shlex.quote(hdfs_path)}"),
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    print(f"[DRIVER][HDFS_CLI] exit_code={completed.returncode}")
    if completed.stdout.strip():
        print(f"[DRIVER][HDFS_CLI][stdout]\n{completed.stdout.rstrip()}")
    if completed.stderr.strip():
        print(f"[DRIVER][HDFS_CLI][stderr]\n{completed.stderr.rstrip()}")

    if completed.returncode != 0:
        raise RuntimeError(
            "Driver-side HDFS CLI discovery failed. "
            f"Exit code={completed.returncode}"
        )

    discovered_files: list[str] = []
    for raw_line in completed.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("Found "):
            continue
        if line.startswith("WARNING:"):
            continue
        parts = line.split()
        if len(parts) < 8:
            continue
        candidate = parts[-1]
        if candidate.endswith(".jsonl"):
            discovered_files.append(candidate)

    if not discovered_files:
        raise RuntimeError(
            f"No JSONL files were discovered under the HDFS path: {hdfs_path}"
        )

    print(f"[DRIVER] HDFS CLI discovered {len(discovered_files)} file(s).")
    for index, path in enumerate(discovered_files[:10], start=1):
        print(f"[DRIVER] File {index}: {path}")
    return discovered_files


def discover_hdfs_files_via_webhdfs(hdfs_path: str) -> list[str]:
    parsed = urlparse(hdfs_path)
    if parsed.scheme != "hdfs":
        raise RuntimeError(f"Unsupported HDFS scheme for smoke test: {parsed.scheme or '<unset>'}")

    canonical_http_host = os.getenv(
        "CUSTOMERDNA_HDFS_CANONICAL_HOST",
        parsed.hostname or "namenode.customerdna.local",
    ).strip() or "namenode.customerdna.local"
    https_port = os.getenv("CUSTOMERDNA_HDFS_WEBHTTPS_PORT", "9871").strip() or "9871"
    webhdfs_url = (
        f"https://{canonical_http_host}:{https_port}/webhdfs/v1"
        f"{quote(parsed.path or '/', safe='/')}"
        "?op=LISTSTATUS"
    )

    command = [
        "curl",
        "--negotiate",
        "-u",
        ":",
        "-sk",
        webhdfs_url,
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    print(f"[DRIVER][WEBHDFS] url={webhdfs_url}")
    print(f"[DRIVER][WEBHDFS] exit_code={completed.returncode}")
    if completed.stderr.strip():
        print(f"[DRIVER][WEBHDFS][stderr]\n{completed.stderr.rstrip()}")

    if completed.returncode != 0:
        raise RuntimeError(
            "Driver-side WebHDFS discovery failed. "
            f"Exit code={completed.returncode}"
        )

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Driver-side WebHDFS discovery returned non-JSON output. "
            f"Payload preview={(completed.stdout or '<empty>').strip()[:240]}"
        ) from exc

    statuses = (
        payload.get("FileStatuses", {}).get("FileStatus", [])
        if isinstance(payload, dict)
        else []
    )
    discovered_files: list[str] = []
    for entry in statuses:
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "FILE":
            continue
        suffix = str(entry.get("pathSuffix", "")).strip()
        if not suffix.endswith(".jsonl"):
            continue
        discovered_files.append(
            f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}/{suffix}"
        )

    if not discovered_files:
        raise RuntimeError(
            f"No JSONL files were discovered under the HDFS path via WebHDFS: {hdfs_path}"
        )

    print(f"[DRIVER] WebHDFS discovered {len(discovered_files)} file(s).")
    for index, path in enumerate(discovered_files[:10], start=1):
        print(f"[DRIVER] File {index}: {path}")
    return discovered_files


def wait_for_namenode_safemode_exit(hdfs_path: str) -> None:
    parsed = urlparse(hdfs_path)
    if parsed.scheme != "hdfs":
        raise RuntimeError(
            f"Unsupported HDFS scheme for safe-mode wait: {parsed.scheme or '<unset>'}"
        )

    canonical_http_host = os.getenv(
        "CUSTOMERDNA_HDFS_CANONICAL_HOST",
        parsed.hostname or "namenode.customerdna.local",
    ).strip() or "namenode.customerdna.local"
    https_port = os.getenv("CUSTOMERDNA_HDFS_WEBHTTPS_PORT", "9871").strip() or "9871"
    jmx_url = (
        f"https://{canonical_http_host}:{https_port}/jmx"
        "?qry=Hadoop:service=NameNode,name=NameNodeInfo"
    )

    print(
        "[HDFS] Waiting for NameNode safe mode to clear "
        f"(timeout={HDFS_SAFEMODE_WAIT_TIMEOUT_SECONDS}s, interval={HDFS_SAFEMODE_POLL_INTERVAL_SECONDS}s)"
    )

    deadline = time.time() + HDFS_SAFEMODE_WAIT_TIMEOUT_SECONDS
    last_status = "<unavailable>"

    while time.time() < deadline:
        completed = subprocess.run(
            ["curl", "--negotiate", "-u", ":", "-sk", jmx_url],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if completed.returncode != 0:
            last_status = (
                f"curl failed with exit code {completed.returncode}: "
                f"{(completed.stderr or '<empty>').strip()}"
            )
        else:
            try:
                payload = json.loads(completed.stdout)
                beans = payload.get("beans", []) if isinstance(payload, dict) else []
                safemode = ""
                if beans and isinstance(beans[0], dict):
                    safemode = str(beans[0].get("Safemode", "") or "").strip()
                last_status = safemode or "<off>"
                print(f"[HDFS] SafeMode status: {last_status}")
                if not safemode:
                    print("[HDFS] NameNode safe mode is OFF. Continuing.")
                    return
            except json.JSONDecodeError:
                last_status = (
                    "non-JSON JMX response: "
                    f"{(completed.stdout or '<empty>').strip()[:240]}"
                )

        remaining = max(0, int(deadline - time.time()))
        print(f"[HDFS] Safe mode still active/unconfirmed. Retrying in {HDFS_SAFEMODE_POLL_INTERVAL_SECONDS}s ({remaining}s remaining).")
        time.sleep(HDFS_SAFEMODE_POLL_INTERVAL_SECONDS)

    raise RuntimeError(
        "NameNode safe mode did not clear before timeout. "
        f"Last observed status: {last_status}"
    )


def log_executor_command_probe(spark: SparkSession, hdfs_path: str) -> None:
    canonical_http_host = os.getenv("CUSTOMERDNA_HDFS_CANONICAL_HOST", "namenode.customerdna.local")
    jmx_url = (
        f"https://{canonical_http_host}:9871/jmx?"
        "qry=Hadoop:service=NameNode,name=NameNodeInfo"
    )
    hdfs_quoted = shlex.quote(hdfs_path)

    def _probe(partition_iter):
        list(partition_iter)
        hostname = socket.gethostname()
        cache_name = os.getenv("KRB5CCNAME", "<unset>")
        cache_path = cache_name.removeprefix("FILE:") if cache_name and cache_name != "<unset>" else ""
        keytab = os.getenv("KRB5_CLIENT_KTNAME", "<unset>")
        principal = os.getenv("CUSTOMERDNA_SPARK_KERBEROS_PRINCIPAL", "<unset>")

        commands = [
            ("id", ["id"]),
            ("hostname", ["hostname", "-f"]),
            (
                "ls_cache",
                ["sh", "-lc", f"ls -l {shlex.quote(cache_path)}"] if cache_path else ["sh", "-lc", "echo no-cache-path"],
            ),
            (
                "ls_keytab",
                ["sh", "-lc", f"ls -l {shlex.quote(keytab)}"]
                if keytab and keytab != "<unset>"
                else ["sh", "-lc", "echo no-keytab-path"],
            ),
            (
                "klist",
                ["sh", "-lc", f"klist -c {shlex.quote(cache_path)}"] if cache_path else ["sh", "-lc", "klist"],
            ),
            (
                "kvno_nn",
                ["kvno", f"nn/{canonical_http_host}@CUSTOMERDNA.LOCAL"],
            ),
            (
                "kvno_http",
                ["kvno", f"HTTP/{canonical_http_host}@CUSTOMERDNA.LOCAL"],
            ),
            (
                "curl_jmx_negotiate",
                [
                    "curl",
                    "--negotiate",
                    "-u",
                    ":",
                    "-sk",
                    "-I",
                    jmx_url,
                ],
            ),
            (
                "hdfs_ls",
                [
                    "sh",
                    "-lc",
                    build_fs_shell_snippet(f"-ls {hdfs_quoted}")
                    + " || echo hdfs-cli-unavailable",
                ],
            ),
        ]

        output = [
            f"executor_hostname={hostname}",
            f"KRB5CCNAME={cache_name}",
            f"KRB5_CLIENT_KTNAME={keytab}",
            f"CUSTOMERDNA_SPARK_KERBEROS_PRINCIPAL={principal}",
        ]

        for label, command in commands:
            try:
                completed = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=25,
                )
                output.append(f"{label}.exit_code={completed.returncode}")
                output.append(f"{label}.stdout={(completed.stdout.strip() or '<empty>')}")
                output.append(f"{label}.stderr={(completed.stderr.strip() or '<empty>')}")
            except Exception as exc:
                output.append(f"{label}.error={exc}")

        yield " | ".join(output)

    results = spark.sparkContext.parallelize([1, 2, 3], 3).mapPartitions(_probe).collect()
    for line in results:
        print(f"[EXECUTOR_COMMAND_PROBE] {line}")


def run_executor_spark_read_probe(spark: SparkSession, hdfs_path: str) -> int:
    wait_for_namenode_safemode_exit(hdfs_path)
    discovered_files = discover_hdfs_files_via_webhdfs(hdfs_path)
    print("[SPARK_READ] Starting distributed Spark text read against discovered HDFS files.")
    for path in discovered_files:
        print(f"[SPARK_READ] Input file: {path}")

    text_rdd = spark.sparkContext.textFile(",".join(discovered_files))
    count = text_rdd.count()
    print(f"[SPARK_READ] Counted records through Spark/HDFS path: {count}")
    return count


def main() -> int:
    args = parse_args()
    start_counter = time.perf_counter()

    print("=" * 80)
    print("CUSTOMERDNA AI - SPARK EXECUTOR KERBEROS HDFS SMOKE TEST")
    print("=" * 80)
    print(f"HDFS path: {args.hdfs_path}")
    print(f"Expected minimum records: {args.expected_min_records}")

    spark = build_spark_session(args.hdfs_path)

    try:
        force_hadoop_kerberos_login(spark)
        log_driver_context(spark, args.hdfs_path)
        log_executor_command_probe(spark, args.hdfs_path)
        records = run_executor_spark_read_probe(spark, args.hdfs_path)

        if records < args.expected_min_records:
            raise RuntimeError(
                f"Smoke test record-count check failed: expected at least "
                f"{args.expected_min_records:,}, observed {records:,}."
            )

        duration_seconds = round(time.perf_counter() - start_counter, 3)
        print(f"Smoke test records observed: {records:,}")
        print(f"Completed at (UTC): {datetime.utcnow().isoformat()}Z")
        print(f"Duration (seconds): {duration_seconds}")
        print("Spark executor Kerberos HDFS smoke test completed successfully.")
        print("=" * 80)
        return 0
    except Exception as exc:
        print(f"[ERROR] Spark executor Kerberos HDFS smoke test failed: {exc}")
        print("[ERROR] Python traceback follows:")
        print(traceback.format_exc().rstrip())
        return 1
    finally:
        spark.stop()


if __name__ == "__main__":
    raise SystemExit(main())
