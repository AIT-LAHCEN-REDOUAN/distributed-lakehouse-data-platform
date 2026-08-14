"""Minimal Spark smoke test for executor-side Kerberos access to HDFS."""

from __future__ import annotations

import argparse
import os
import shlex
import socket
import subprocess
import time
import traceback
from datetime import datetime

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


def build_spark_session(hdfs_path: str) -> SparkSession:
    app_suffix = hdfs_path.strip("/").replace("/", "_").replace("*", "wildcard")[-60:]
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
        .config("spark.kerberos.renewal.credentials", "keytab")
        .config("spark.security.credentials.hadoopfs.enabled", "true")
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
        path_cls = sc._jvm.org.apache.hadoop.fs.Path
        fs = path_cls(hdfs_path).getFileSystem(hadoop_conf)
        target = path_cls(hdfs_path)
        print(f"[DRIVER] Filesystem URI: {fs.getUri()}")
        print(f"[DRIVER] Path exists: {fs.exists(target)}")
        if fs.exists(target):
            statuses = fs.listStatus(target)
            print(f"[DRIVER] Path entries discovered: {len(statuses)}")
            for index, status in enumerate(statuses[:5], start=1):
                print(
                    "[DRIVER] Entry "
                    f"{index}: path={status.getPath()}, isFile={status.isFile()}, length={status.getLen()}"
                )
    except Exception as exc:
        print(f"[DRIVER][WARN] Driver-side HDFS preflight failed: {exc}")
        print(traceback.format_exc().rstrip())


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
                    "command -v hdfs >/dev/null 2>&1 && "
                    f"HADOOP_CONF_DIR=/etc/hadoop/conf hdfs dfs -ls {hdfs_quoted} || "
                    "echo hdfs-cli-unavailable",
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
    def _partition_probe(partition_index, rows):
        hostname = socket.gethostname()
        observed = 0
        samples = []
        for row in rows:
            observed += 1
            if len(samples) < 2:
                samples.append(row[:160])
            if observed >= 5:
                break
        yield (
            f"partition={partition_index} | executor_hostname={hostname} | "
            f"observed_rows={observed} | samples={samples or ['<none>']}"
        )

    rdd = spark.sparkContext.textFile(hdfs_path, minPartitions=3)
    count = int(rdd.count())
    print(f"[SPARK_READ] Counted records through Spark executor path: {count}")

    partition_logs = rdd.mapPartitionsWithIndex(_partition_probe).collect()
    for line in partition_logs:
        print(f"[SPARK_READ] {line}")

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
