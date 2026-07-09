"""Shared MinIO bronze-to-raw PostgreSQL loader for Client 1 datasets."""

from __future__ import annotations

import csv
import io
import json
import time
import re
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2 import sql


CURRENT_DIR = Path(__file__).resolve().parent
CLIENT_ELT_ROOT = CURRENT_DIR.parents[1]
SRC_ROOT = CLIENT_ELT_ROOT.parents[1]
STREAMING_COMMON_DIR = SRC_ROOT / "streaming" / "kafka" / "client_1" / "common"
MINIO_COMMON_DIR = SRC_ROOT / "lake" / "minio" / "client_1" / "common"
CONFIG_DIR = CLIENT_ELT_ROOT / "config"

for dependency_dir in (CONFIG_DIR, STREAMING_COMMON_DIR, MINIO_COMMON_DIR):
    dependency_dir_str = str(dependency_dir)
    if dependency_dir_str not in sys.path:
        sys.path.insert(0, dependency_dir_str)

from config import CLIENT_DW_CONFIG, DATA_WAREHOUSE_NAME, get_connection_params  # noqa: E402
from kafka_config import TOPICS, get_dataset_config  # noqa: E402
from minio_bronze_config import MINIO_BUCKET_NAME  # noqa: E402
from minio_bronze_utils import build_minio_client, list_bronze_objects, list_bronze_objects_by_prefix  # noqa: E402


IDENTIFIER_CLEAN_PATTERN = re.compile(r"[^a-z0-9_]+")


@dataclass(frozen=True)
class BronzeLoadResult:
    """Return a compact bronze-to-raw loading summary."""

    rows_loaded: int
    object_count: int
    duration_seconds: float


class BronzeToRawLoader:
    """Stream bronze JSONL objects from MinIO into raw PostgreSQL tables."""

    def __init__(self, dataset_key: str, verbose: bool = True):
        self.dataset_key = dataset_key
        self.dataset_config = get_dataset_config(dataset_key)
        self.target_table = str(self.dataset_config["target_table"])
        self.topic_name = TOPICS[dataset_key]
        self.verbose = verbose
        self.connection = None
        self.raw_schema = CLIENT_DW_CONFIG["raw_schema"]
        self.metadata_schema = CLIENT_DW_CONFIG["metadata_schema"]

    def log(self, message: str, level: str = "INFO") -> None:
        if self.verbose:
            print(f"[{level}] {message}")

    def connect_to_dw(self) -> bool:
        try:
            self.connection = psycopg2.connect(**get_connection_params(DATA_WAREHOUSE_NAME))
            self.connection.autocommit = False
            self.log(f"Connected to Data Warehouse: {DATA_WAREHOUSE_NAME}", "SUCCESS")
            return True
        except Exception as exc:
            self.log(f"Failed to connect to Data Warehouse: {exc}", "ERROR")
            return False

    def close_connection(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None
            self.log("Closed database connection")

    def ensure_metadata_table(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(self.metadata_schema))
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata.kafka_loaded_topics (
                id SERIAL PRIMARY KEY,
                topic_name TEXT NOT NULL,
                target_schema TEXT NOT NULL,
                target_table TEXT NOT NULL,
                consumer_group TEXT NOT NULL,
                rows_loaded BIGINT NOT NULL DEFAULT 0,
                load_mode TEXT NOT NULL,
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.close()

    def get_target_columns(self) -> list[str]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
            ORDER BY ordinal_position
            """,
            (self.raw_schema, self.target_table),
        )
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()

        if not columns:
            raise RuntimeError(
                f"Target table columns not found for {self.raw_schema}.{self.target_table}. "
                "Run the DW setup and raw base-table creation first."
            )

        return columns

    def create_temp_table(self, temp_table_name: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            sql.SQL("CREATE TEMP TABLE {} (LIKE {}.{} INCLUDING DEFAULTS)").format(
                sql.Identifier(temp_table_name),
                sql.Identifier(self.raw_schema),
                sql.Identifier(self.target_table),
            )
        )
        cursor.close()

    def truncate_target_table(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            sql.SQL("TRUNCATE TABLE {}.{}").format(
                sql.Identifier(self.raw_schema),
                sql.Identifier(self.target_table),
            )
        )
        cursor.close()
        self.log(f"Truncated target table: {self.raw_schema}.{self.target_table}")

    def copy_rows(self, table_name: str, rows: list[tuple[object, ...]], target_columns: list[str]) -> None:
        if not rows:
            return

        buffer = io.StringIO()
        writer = csv.writer(
            buffer,
            delimiter="\t",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n",
        )

        for row in rows:
            writer.writerow(["\\N" if value is None else str(value) for value in row])

        buffer.seek(0)
        cursor = self.connection.cursor()
        copy_sql = sql.SQL(
            "COPY {} ({}) FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N')"
        ).format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(sql.Identifier(column_name) for column_name in target_columns),
        )
        cursor.copy_expert(copy_sql.as_string(self.connection), buffer)
        cursor.close()

    def replace_target_from_temp(self, temp_table_name: str, target_columns: list[str]) -> None:
        cursor = self.connection.cursor()
        self.truncate_target_table()
        cursor.execute(
            sql.SQL("INSERT INTO {}.{} ({}) SELECT {} FROM {}").format(
                sql.Identifier(self.raw_schema),
                sql.Identifier(self.target_table),
                sql.SQL(", ").join(sql.Identifier(column) for column in target_columns),
                sql.SQL(", ").join(sql.Identifier(column) for column in target_columns),
                sql.Identifier(temp_table_name),
            )
        )
        cursor.close()

    def count_target_rows(self) -> int:
        cursor = self.connection.cursor()
        cursor.execute(
            sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                sql.Identifier(self.raw_schema),
                sql.Identifier(self.target_table),
            )
        )
        row_count = int(cursor.fetchone()[0])
        cursor.close()
        return row_count

    def register_load(self, rows_loaded: int, started_at: datetime, ended_at: datetime, load_mode: str) -> None:
        loader_run_id = (
            f"customerdna-client1-{self.dataset_key}-bronze-loader-"
            f"{ended_at.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        )
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO metadata.kafka_loaded_topics (
                topic_name,
                target_schema,
                target_table,
                consumer_group,
                rows_loaded,
                load_mode,
                started_at,
                ended_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                self.topic_name,
                self.raw_schema,
                self.target_table,
                loader_run_id,
                rows_loaded,
                load_mode,
                started_at.replace(tzinfo=None),
                ended_at.replace(tzinfo=None),
            ),
        )
        cursor.close()

    @staticmethod
    def clean_identifier(name: str) -> str:
        normalized = name.strip().lower()
        cleaned = IDENTIFIER_CLEAN_PATTERN.sub("_", normalized)
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
        if not cleaned:
            cleaned = "unnamed"
        if cleaned[0].isdigit():
            cleaned = f"col_{cleaned}"
        return cleaned

    def transform_payload_to_row(
        self,
        payload: dict[str, object],
        target_columns: list[str],
    ) -> tuple[object, ...]:
        normalized_payload = {
            self.clean_identifier(str(column_name)): column_value
            for column_name, column_value in payload.items()
        }
        return tuple(normalized_payload.get(column_name) for column_name in target_columns)

    def _load_bronze_objects(
        self,
        *,
        minio_client,
        bronze_objects: list,
        target_columns: list[str],
        started_at: datetime,
        start_counter: float,
        load_mode: str,
        expected_rows: int | None = None,
        expected_object_count: int | None = None,
    ) -> BronzeLoadResult:
        if expected_object_count is not None and len(bronze_objects) != expected_object_count:
            raise RuntimeError(
                f"Bronze object-count mismatch for dataset '{self.dataset_key}': "
                f"expected {expected_object_count:,}, found {len(bronze_objects):,}."
            )

        self.ensure_metadata_table()
        temp_table_name = f"tmp_{self.target_table}_{uuid.uuid4().hex[:8]}"
        self.create_temp_table(temp_table_name)

        total_loaded = 0
        row_batch: list[tuple[object, ...]] = []
        copy_batch_size = int(self.dataset_config["load_copy_batch_size"])
        progress_interval = int(self.dataset_config["load_progress_interval"])
        next_progress_checkpoint = progress_interval

        def flush_row_batch() -> None:
            nonlocal total_loaded, row_batch, next_progress_checkpoint

            if not row_batch:
                return

            batch_size = len(row_batch)
            self.copy_rows(temp_table_name, row_batch, target_columns)
            total_loaded += batch_size
            if total_loaded >= next_progress_checkpoint:
                self.log(
                    f"Buffered {total_loaded:,} rows for "
                    f"{self.raw_schema}.{self.target_table}"
                )
                while total_loaded >= next_progress_checkpoint:
                    next_progress_checkpoint += progress_interval
            row_batch = []

        try:
            for object_index, object_info in enumerate(bronze_objects, start=1):
                self.log(
                    f"Loading bronze object {object_index:,}/{len(bronze_objects):,}: "
                    f"{object_info.object_name}"
                )
                response = minio_client.get_object(MINIO_BUCKET_NAME, object_info.object_name)

                try:
                    text_buffer = ""
                    for chunk in response.stream(amt=1024 * 1024):
                        if not chunk:
                            continue

                        text_buffer += chunk.decode("utf-8")
                        lines = text_buffer.splitlines(keepends=True)

                        if lines and not lines[-1].endswith(("\n", "\r")):
                            text_buffer = lines.pop()
                        else:
                            text_buffer = ""

                        for raw_line in lines:
                            line = raw_line.strip()
                            if not line:
                                continue

                            message_value = json.loads(line)
                            payload = message_value.get("payload", {})
                            row_batch.append(self.transform_payload_to_row(payload, target_columns))

                            if len(row_batch) >= copy_batch_size:
                                flush_row_batch()

                    if text_buffer.strip():
                        message_value = json.loads(text_buffer.strip())
                        payload = message_value.get("payload", {})
                        row_batch.append(self.transform_payload_to_row(payload, target_columns))
                        if len(row_batch) >= copy_batch_size:
                            flush_row_batch()
                finally:
                    response.close()
                    response.release_conn()

            flush_row_batch()

            if total_loaded == 0:
                raise RuntimeError(
                    f"No rows were read from bronze objects for dataset '{self.dataset_key}'."
                )

            if expected_rows is not None and total_loaded != expected_rows:
                raise RuntimeError(
                    f"Bronze row-count mismatch for dataset '{self.dataset_key}': "
                    f"expected {expected_rows:,}, loaded {total_loaded:,}."
                )

            self.replace_target_from_temp(temp_table_name, target_columns)
            target_row_count = self.count_target_rows()
            if target_row_count != total_loaded:
                raise RuntimeError(
                    f"Post-load verification failed for {self.raw_schema}.{self.target_table}: "
                    f"bronze rows={total_loaded:,}, target rows={target_row_count:,}."
                )

            ended_at = datetime.now(timezone.utc)
            self.register_load(total_loaded, started_at, ended_at, load_mode)
            self.connection.commit()
            self.log(
                f"Verified target row count: {target_row_count:,} rows in "
                f"{self.raw_schema}.{self.target_table}",
                "SUCCESS",
            )

            duration_seconds = round(time.perf_counter() - start_counter, 3)
            return BronzeLoadResult(
                rows_loaded=total_loaded,
                object_count=len(bronze_objects),
                duration_seconds=duration_seconds,
            )
        except Exception:
            self.connection.rollback()
            raise

    def load_from_bronze_event(self, event_payload: dict[str, object]) -> BronzeLoadResult:
        started_at = datetime.now(timezone.utc)
        start_counter = time.perf_counter()
        target_columns = self.get_target_columns()
        minio_client = build_minio_client()

        event_bucket_name = str(event_payload.get("bucket_name", "")).strip()
        if event_bucket_name and event_bucket_name != MINIO_BUCKET_NAME:
            raise RuntimeError(
                f"MinIO bucket mismatch: event bucket '{event_bucket_name}' "
                f"does not match configured bucket '{MINIO_BUCKET_NAME}'."
            )

        bronze_run_prefix = str(event_payload.get("bronze_run_prefix", "")).strip().strip("/")
        if not bronze_run_prefix:
            raise RuntimeError("Bronze-ready event did not include a valid bronze_run_prefix.")

        bronze_objects = sorted(
            list_bronze_objects_by_prefix(minio_client, bronze_run_prefix),
            key=lambda object_info: object_info.object_name,
        )

        if not bronze_objects:
            raise RuntimeError(
                f"No bronze objects found for dataset '{self.dataset_key}' under prefix "
                f"'{bronze_run_prefix}'."
            )

        return self._load_bronze_objects(
            minio_client=minio_client,
            bronze_objects=bronze_objects,
            target_columns=target_columns,
            started_at=started_at,
            start_counter=start_counter,
            load_mode=str(event_payload.get("load_mode", "kafka_bronze_ready_event")),
            expected_rows=int(event_payload.get("row_count", 0)) or None,
            expected_object_count=int(event_payload.get("object_count", 0)) or None,
        )

    def load_from_bronze(self) -> BronzeLoadResult:
        started_at = datetime.now(timezone.utc)
        start_counter = time.perf_counter()
        target_columns = self.get_target_columns()
        minio_client = build_minio_client()
        bronze_objects = sorted(
            list_bronze_objects(minio_client, self.dataset_key),
            key=lambda object_info: object_info.object_name,
        )

        if not bronze_objects:
            raise RuntimeError(
                f"No bronze objects found for dataset '{self.dataset_key}'. "
                "Run the Kafka producer and bronze consumer first."
            )

        return self._load_bronze_objects(
            minio_client=minio_client,
            bronze_objects=bronze_objects,
            target_columns=target_columns,
            started_at=started_at,
            start_counter=start_counter,
            load_mode="full_refresh_from_minio_bronze",
        )
