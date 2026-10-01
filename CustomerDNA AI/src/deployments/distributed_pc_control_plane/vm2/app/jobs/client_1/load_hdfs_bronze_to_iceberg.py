"""Spark job that reads one Client 1 HDFS bronze slice and writes it into an Iceberg raw table."""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import time
import traceback
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


IDENTIFIER_CLEAN_PATTERN = re.compile(r"[^a-z0-9_]+")
TARGET_WRITE_PARTITIONS = max(1, int(os.getenv("CUSTOMERDNA_SPARK_WRITE_PARTITIONS", "2")))
SHUFFLE_PARTITIONS = max(TARGET_WRITE_PARTITIONS * 2, 4)
HDFS_TOKEN_RENEWAL_EXCLUDE = (
    os.getenv(
        "CUSTOMERDNA_HDFS_TOKEN_RENEWAL_EXCLUDE",
        "namenode.customerdna.local,namenode,10.10.252.12",
    ).strip()
    or "namenode.customerdna.local,namenode,10.10.252.12"
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


def clean_identifier(name: str) -> str:
    normalized = str(name).strip().lower()
    cleaned = IDENTIFIER_CLEAN_PATTERN.sub("_", normalized)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = "unnamed"
    if cleaned[0].isdigit():
        cleaned = f"col_{cleaned}"
    return cleaned


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load a Client 1 HDFS bronze dataset into an Iceberg raw table using Spark."
    )
    parser.add_argument("--dataset-key", required=True)
    parser.add_argument("--target-table", required=True)
    parser.add_argument("--iceberg-catalog", default="customerdna")
    parser.add_argument("--iceberg-namespace", default="raw_data")
    parser.add_argument("--bronze-prefix", required=True)
    parser.add_argument("--hdfs-namenode-uri", required=True)
    parser.add_argument("--expected-rows", default=0, type=int)
    parser.add_argument("--expected-file-count", default=0, type=int)
    return parser.parse_args()


def build_spark_session(dataset_key: str) -> SparkSession:
    return (
        SparkSession.builder.appName(f"customerdna-client1-{dataset_key}-bronze-to-iceberg")
        .config("spark.eventLog.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.default.parallelism", str(TARGET_WRITE_PARTITIONS))
        .config("spark.sql.shuffle.partitions", str(SHUFFLE_PARTITIONS))
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config("spark.driverEnv.CUSTOMERDNA_SPARK_KERBEROS_PRINCIPAL", SPARK_KERBEROS_PRINCIPAL)
        .config("spark.driverEnv.KRB5_CLIENT_KTNAME", SPARK_KERBEROS_KEYTAB)
        .config("spark.executorEnv.CUSTOMERDNA_SPARK_KERBEROS_PRINCIPAL", SPARK_KERBEROS_PRINCIPAL)
        .config("spark.executorEnv.KRB5_CLIENT_KTNAME", SPARK_KERBEROS_KEYTAB)
        .config("spark.kerberos.principal", SPARK_KERBEROS_PRINCIPAL)
        .config("spark.kerberos.keytab", SPARK_KERBEROS_KEYTAB)
        .config("spark.security.credentials.hadoopfs.enabled", "false")
        .config("spark.hadoop.hadoop.security.token.service.use_ip", "false")
        .config(
            "spark.hadoop.mapreduce.job.hdfs-servers.token-renewal.exclude",
            HDFS_TOKEN_RENEWAL_EXCLUDE,
        )
        .enableHiveSupport()
        .getOrCreate()
    )


def build_bronze_path(args: argparse.Namespace) -> str:
    bronze_prefix = "/" + args.bronze_prefix.strip().strip("/")
    return f"{args.hdfs_namenode_uri.rstrip('/')}{bronze_prefix}"


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
        raise RuntimeError("Spark Kerberos principal is not configured for explicit Hadoop login.")
    if not keytab:
        raise RuntimeError("Spark Kerberos keytab is not configured for explicit Hadoop login.")
    if not os.path.exists(keytab):
        raise RuntimeError(f"Spark Kerberos keytab does not exist on the driver: {keytab}")

    try:
        login_user_before = ugi.getLoginUser()
        print(f"[KERBEROS] Login user before refresh: {login_user_before.getUserName()}")
        print(
            "[KERBEROS] Login auth method before refresh: "
            f"{login_user_before.getAuthenticationMethod()}"
        )
    except Exception as exc:
        print(f"[KERBEROS][WARN] Unable to inspect login user before refresh: {exc}")

    ugi.loginUserFromKeytab(principal, keytab)

    login_user_after = ugi.getLoginUser()
    current_user_after = ugi.getCurrentUser()
    print(f"[KERBEROS] Login user after refresh: {login_user_after.getUserName()}")
    print(
        "[KERBEROS] Login auth method after refresh: "
        f"{login_user_after.getAuthenticationMethod()}"
    )
    print(f"[KERBEROS] Current user after refresh: {current_user_after.getUserName()}")
    print(
        "[KERBEROS] Current auth method after refresh: "
        f"{current_user_after.getAuthenticationMethod()}"
    )
    print(
        "[KERBEROS] Current user has Kerberos credentials after refresh: "
        f"{current_user_after.hasKerberosCredentials()}"
    )


def wait_for_namenode_safemode_exit(bronze_path: str) -> None:
    if not bronze_path.startswith("hdfs://"):
        raise RuntimeError(f"Unsupported bronze path for safe-mode wait: {bronze_path}")

    authority = bronze_path.split("://", 1)[1].split("/", 1)[0]
    hostname = authority.split(":", 1)[0]
    canonical_http_host = (
        os.getenv("CUSTOMERDNA_HDFS_CANONICAL_HOST", "").strip() or hostname
    )
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


def load_bronze_dataframe(spark: SparkSession, bronze_path: str):
    wait_for_namenode_safemode_exit(bronze_path)
    return spark.read.option("recursiveFileLookup", "true").json(bronze_path)


def flatten_payload(raw_df):
    payload_df = raw_df.select("payload.*")
    actual_columns = {column_name: column_name for column_name in payload_df.columns}
    normalized_to_actual = {
        clean_identifier(actual_column): actual_column
        for actual_column in payload_df.columns
    }

    renamed_columns = []
    for actual_column in payload_df.columns:
        clean_name = clean_identifier(actual_column)
        source_column = actual_columns.get(actual_column) or normalized_to_actual.get(clean_name)
        renamed_columns.append(
            F.col(f"`{source_column}`").cast("string").alias(clean_name)
        )

    return payload_df.select(*renamed_columns)


def repartition_for_cluster(prepared_df):
    current_partitions = prepared_df.rdd.getNumPartitions()
    if TARGET_WRITE_PARTITIONS <= 1 or current_partitions >= TARGET_WRITE_PARTITIONS:
        return prepared_df, current_partitions
    return prepared_df.repartition(TARGET_WRITE_PARTITIONS), TARGET_WRITE_PARTITIONS


def ensure_namespace(spark: SparkSession, *, catalog: str, namespace: str) -> None:
    spark.sql(f"CREATE NAMESPACE IF NOT EXISTS {catalog}.{namespace}")


def write_to_iceberg(prepared_df, *, table_identifier: str) -> None:
    (
        prepared_df.writeTo(table_identifier)
        .tableProperty("format-version", "2")
        .using("iceberg")
        .createOrReplace()
    )


def verify_target_row_count(spark: SparkSession, *, table_identifier: str) -> int:
    return int(spark.table(table_identifier).count())


def log_runtime_diagnostics(spark: SparkSession, args: argparse.Namespace, bronze_path: str) -> None:
    sc = spark.sparkContext
    print("[DIAGNOSTICS] Spark runtime context")
    print(f"[DIAGNOSTICS] Spark version: {spark.version}")
    print(f"[DIAGNOSTICS] Spark app name: {sc.appName}")
    print(f"[DIAGNOSTICS] Spark master: {sc.master}")
    print(f"[DIAGNOSTICS] Spark application id: {sc.applicationId}")
    print(f"[DIAGNOSTICS] Spark default parallelism: {sc.defaultParallelism}")
    print(f"[DIAGNOSTICS] Target write partitions: {TARGET_WRITE_PARTITIONS}")
    print(f"[DIAGNOSTICS] Shuffle partitions: {spark.conf.get('spark.sql.shuffle.partitions')}")

    print("[DIAGNOSTICS] Job arguments")
    print(f"[DIAGNOSTICS] Dataset key: {args.dataset_key}")
    print(f"[DIAGNOSTICS] Target table: {args.target_table}")
    print(f"[DIAGNOSTICS] Iceberg catalog: {args.iceberg_catalog}")
    print(f"[DIAGNOSTICS] Iceberg namespace: {args.iceberg_namespace}")
    print(f"[DIAGNOSTICS] Bronze prefix: {args.bronze_prefix}")
    print(f"[DIAGNOSTICS] Bronze path: {bronze_path}")
    print(f"[DIAGNOSTICS] Expected rows: {args.expected_rows}")
    print(f"[DIAGNOSTICS] Expected file count: {args.expected_file_count}")

    print("[DIAGNOSTICS] Selected Spark configuration")
    for conf_key in [
        "spark.kerberos.principal",
        "spark.kerberos.keytab",
        "spark.kerberos.access.hadoopFileSystems",
        "spark.security.credentials.hadoopfs.enabled",
        "spark.hadoop.hadoop.security.token.service.use_ip",
        "spark.hadoop.mapreduce.job.hdfs-servers.token-renewal.exclude",
        "spark.driver.host",
        "spark.driver.bindAddress",
        "spark.driver.port",
        "spark.blockManager.port",
        "spark.executor.memory",
        "spark.executor.cores",
        "spark.cores.max",
    ]:
        print(f"[DIAGNOSTICS] {conf_key}={spark.conf.get(conf_key, '<unset>')}")

    print("[DIAGNOSTICS] Selected Hadoop configuration")
    hadoop_conf = sc._jsc.hadoopConfiguration()
    for conf_key in [
        "fs.defaultFS",
        "hadoop.security.token.service.use_ip",
        "hadoop.security.authentication",
        "hadoop.security.authorization",
        "hadoop.rpc.protection",
        "dfs.namenode.kerberos.principal",
        "dfs.datanode.kerberos.principal",
        "dfs.block.access.token.enable",
        "dfs.data.transfer.protection",
        "dfs.encrypt.data.transfer",
        "dfs.client.use.datanode.hostname",
        "mapreduce.job.hdfs-servers.token-renewal.exclude",
    ]:
        print(f"[DIAGNOSTICS] {conf_key}={hadoop_conf.get(conf_key) or '<unset>'}")

    print("[DIAGNOSTICS] Selected environment variables")
    for env_key in [
        "KRB5_CONFIG",
        "KRB5CCNAME",
        "HADOOP_CONF_DIR",
        "SPARK_CONF_DIR",
        "JAVA_HOME",
        "HOSTNAME",
    ]:
        print(f"[DIAGNOSTICS] {env_key}={os.getenv(env_key, '<unset>')}")

    try:
        ugi = sc._jvm.org.apache.hadoop.security.UserGroupInformation
        current_user = ugi.getCurrentUser()
        print("[DIAGNOSTICS] Hadoop security context")
        print(f"[DIAGNOSTICS] Current user: {current_user.getUserName()}")
        print(f"[DIAGNOSTICS] Authentication method: {current_user.getAuthenticationMethod()}")
        print(f"[DIAGNOSTICS] Has Kerberos credentials: {current_user.hasKerberosCredentials()}")
        print(f"[DIAGNOSTICS] Security enabled: {ugi.isSecurityEnabled()}")
    except Exception as exc:
        print(f"[DIAGNOSTICS][WARN] Unable to inspect Hadoop security context: {exc}")

    try:
        print("[DIAGNOSTICS] HDFS preflight")
        path_cls = sc._jvm.org.apache.hadoop.fs.Path
        fs = path_cls(bronze_path).getFileSystem(hadoop_conf)
        bronze_path_obj = path_cls(bronze_path)
        print(f"[DIAGNOSTICS] Filesystem URI: {fs.getUri()}")
        print(f"[DIAGNOSTICS] Working directory: {fs.getWorkingDirectory()}")
        print(f"[DIAGNOSTICS] Bronze path exists: {fs.exists(bronze_path_obj)}")

        if fs.exists(bronze_path_obj):
            statuses = fs.listStatus(bronze_path_obj)
            preview_limit = min(5, len(statuses))
            print(f"[DIAGNOSTICS] Bronze path entries discovered: {len(statuses)}")
            for index in range(preview_limit):
                status = statuses[index]
                print(
                    "[DIAGNOSTICS] Bronze entry "
                    f"{index + 1}: path={status.getPath()}, isFile={status.isFile()}, length={status.getLen()}"
                )
    except Exception as exc:
        print(f"[DIAGNOSTICS][ERROR] HDFS preflight failed: {exc}")
        print("[DIAGNOSTICS][ERROR] HDFS preflight traceback follows:")
        print(traceback.format_exc().rstrip())


def log_executor_security_probe(spark: SparkSession) -> None:
    def _probe(_):
        hostname = socket.gethostname()
        krb5_config = os.getenv("KRB5_CONFIG", "<unset>")
        krb5_ccname = os.getenv("KRB5CCNAME", "<unset>")
        krb5_client_ktname = os.getenv("KRB5_CLIENT_KTNAME", "<unset>")
        cache_path = krb5_ccname.removeprefix("FILE:") if krb5_ccname and krb5_ccname != "<unset>" else None
        output_lines = [
            f"hostname={hostname}",
            f"KRB5_CONFIG={krb5_config}",
            f"KRB5CCNAME={krb5_ccname}",
            f"KRB5_CLIENT_KTNAME={krb5_client_ktname}",
        ]

        commands = [
            ("id", ["id"]),
            ("ls_cache", ["ls", "-l", cache_path] if cache_path else ["sh", "-lc", "echo no-cache-path"]),
            ("ls_keytab", ["ls", "-l", krb5_client_ktname] if krb5_client_ktname and krb5_client_ktname != "<unset>" else ["sh", "-lc", "echo no-keytab-path"]),
            ("klist", ["klist", *(["-c", cache_path] if cache_path else [])]),
            (
                "kvno",
                [
                    "kvno",
                    "nn/namenode.customerdna.local@CUSTOMERDNA.LOCAL",
                ],
            ),
        ]

        for label, command in commands:
            try:
                completed = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                stdout = completed.stdout.strip() or "<empty>"
                stderr = completed.stderr.strip() or "<empty>"
                output_lines.append(f"{label}.exit_code={completed.returncode}")
                output_lines.append(f"{label}.stdout={stdout}")
                output_lines.append(f"{label}.stderr={stderr}")
            except Exception as exc:
                output_lines.append(f"{label}.error={exc}")

        yield " | ".join(output_lines)

    try:
        probe_output = spark.sparkContext.parallelize([1], 1).mapPartitions(_probe).collect()
        for line in probe_output:
            print(f"[EXECUTOR_DIAGNOSTICS] {line}")
    except Exception as exc:
        print(f"[EXECUTOR_DIAGNOSTICS][WARN] Executor security probe failed before data read: {exc}")
        print(traceback.format_exc().rstrip())


def main() -> int:
    args = parse_args()
    start_counter = time.perf_counter()

    print("=" * 80)
    print("CUSTOMERDNA AI - SPARK HDFS TO ICEBERG RAW LOAD")
    print("=" * 80)
    print(f"Dataset: {args.dataset_key}")
    print(f"Bronze prefix: {args.bronze_prefix}")

    spark = build_spark_session(args.dataset_key)

    try:
        bronze_path = build_bronze_path(args)
        force_hadoop_kerberos_login(spark)
        log_runtime_diagnostics(spark, args, bronze_path)
        log_executor_security_probe(spark)
        raw_df = load_bronze_dataframe(spark, bronze_path)
        bronze_files_read = len(raw_df.inputFiles())
        print(f"[DIAGNOSTICS] Spark input files discovered: {bronze_files_read}")
        for index, input_file in enumerate(raw_df.inputFiles()[:5], start=1):
            print(f"[DIAGNOSTICS] Input file {index}: {input_file}")

        if bronze_files_read == 0:
            raise RuntimeError(f"No bronze files were found under {bronze_path}.")
        if args.expected_file_count > 0 and bronze_files_read != args.expected_file_count:
            raise RuntimeError(
                f"Bronze file-count mismatch: expected {args.expected_file_count:,}, found {bronze_files_read:,}."
            )

        prepared_df = flatten_payload(raw_df)
        print(f"[DIAGNOSTICS] Prepared dataframe schema: {prepared_df.schema.simpleString()}")
        prepared_df, spark_partitions_used = repartition_for_cluster(prepared_df)
        print(f"[DIAGNOSTICS] Partitions after repartition step: {spark_partitions_used}")
        rows_loaded = int(prepared_df.count())

        if rows_loaded == 0:
            raise RuntimeError("Spark read zero rows from the bronze slice.")
        if args.expected_rows > 0 and rows_loaded != args.expected_rows:
            raise RuntimeError(
                f"Bronze row-count mismatch: expected {args.expected_rows:,}, loaded {rows_loaded:,}."
            )

        ensure_namespace(
            spark,
            catalog=args.iceberg_catalog,
            namespace=args.iceberg_namespace,
        )

        table_identifier = f"{args.iceberg_catalog}.{args.iceberg_namespace}.{args.target_table}"
        write_to_iceberg(prepared_df, table_identifier=table_identifier)

        target_row_count = verify_target_row_count(spark, table_identifier=table_identifier)
        if target_row_count != rows_loaded:
            raise RuntimeError(
                f"Iceberg row verification failed: Spark loaded {rows_loaded:,}, table contains {target_row_count:,}."
            )

        duration_seconds = round(time.perf_counter() - start_counter, 3)
        print(f"Iceberg target: {table_identifier}")
        print(f"Bronze files read: {bronze_files_read:,}")
        print(f"Spark partitions used: {spark_partitions_used:,}")
        print(f"Rows loaded: {rows_loaded:,}")
        print(f"Verified target rows: {target_row_count:,}")
        print(f"Completed at (UTC): {datetime.utcnow().isoformat()}Z")
        print(f"Duration (seconds): {duration_seconds}")
        print("Spark HDFS-to-Iceberg raw load completed successfully.")
        print("=" * 80)
        return 0
    except Exception as exc:
        print(f"[ERROR] Spark HDFS-to-Iceberg raw load failed: {exc}")
        print("[ERROR] Python traceback follows:")
        print(traceback.format_exc().rstrip())
        return 1
    finally:
        spark.stop()


if __name__ == "__main__":
    raise SystemExit(main())
