"""Spark job that reads one Client 1 HDFS bronze slice and writes it into an Iceberg raw table."""

from __future__ import annotations

import argparse
import os
import re
import time
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


IDENTIFIER_CLEAN_PATTERN = re.compile(r"[^a-z0-9_]+")
TARGET_WRITE_PARTITIONS = max(1, int(os.getenv("CUSTOMERDNA_SPARK_WRITE_PARTITIONS", "2")))
SHUFFLE_PARTITIONS = max(TARGET_WRITE_PARTITIONS * 2, 4)


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
        .enableHiveSupport()
        .getOrCreate()
    )


def build_bronze_path(args: argparse.Namespace) -> str:
    bronze_prefix = "/" + args.bronze_prefix.strip().strip("/")
    return f"{args.hdfs_namenode_uri.rstrip('/')}{bronze_prefix}"


def load_bronze_dataframe(spark: SparkSession, bronze_path: str):
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
        raw_df = load_bronze_dataframe(spark, bronze_path)
        bronze_files_read = len(raw_df.inputFiles())

        if bronze_files_read == 0:
            raise RuntimeError(f"No bronze files were found under {bronze_path}.")
        if args.expected_file_count > 0 and bronze_files_read != args.expected_file_count:
            raise RuntimeError(
                f"Bronze file-count mismatch: expected {args.expected_file_count:,}, found {bronze_files_read:,}."
            )

        prepared_df = flatten_payload(raw_df)
        prepared_df, spark_partitions_used = repartition_for_cluster(prepared_df)
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
        return 1
    finally:
        spark.stop()


if __name__ == "__main__":
    raise SystemExit(main())
