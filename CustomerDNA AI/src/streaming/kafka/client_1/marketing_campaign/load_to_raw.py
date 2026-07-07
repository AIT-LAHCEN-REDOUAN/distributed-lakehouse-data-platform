"""Load Client 1 marketing campaign Kafka messages into PostgreSQL raw_data."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

import psycopg2
from kafka import KafkaConsumer
from psycopg2.extras import execute_values
from psycopg2 import sql

COMMON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "common"))
if COMMON_DIR not in sys.path:
    sys.path.append(COMMON_DIR)

ELT_CONFIG_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "ELT", "client_1", "config")
)
if ELT_CONFIG_DIR not in sys.path:
    sys.path.append(ELT_CONFIG_DIR)

from config import CLIENT_DW_CONFIG, DATA_WAREHOUSE_NAME, get_connection_params, validate_config  # noqa: E402
from kafka_config import KAFKA_BOOTSTRAP_SERVERS, TOPICS  # noqa: E402


DATASET_KEY = "marketing_campaign"
TOPIC_NAME = TOPICS[DATASET_KEY]
TARGET_TABLE = "marketing_campaign"
TARGET_SCHEMA = CLIENT_DW_CONFIG["raw_schema"]
METADATA_SCHEMA = CLIENT_DW_CONFIG["metadata_schema"]


def clean_identifier(name: str) -> str:
    """Convert source field names into raw table column style."""
    normalized = name.strip().lower()
    cleaned: list[str] = []
    previous_was_underscore = False

    for char in normalized:
        if char.isalnum():
            cleaned.append(char)
            previous_was_underscore = False
        else:
            if not previous_was_underscore:
                cleaned.append("_")
                previous_was_underscore = True

    result = "".join(cleaned).strip("_")
    if not result:
        return "unnamed"
    if result[0].isdigit():
        return f"col_{result}"
    return result


class KafkaRawLoader:
    """Consume Kafka messages and load them into a raw PostgreSQL table."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.connection = None

    def log(self, message: str, level: str = "INFO") -> None:
        if not self.verbose:
            return
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
            self.log("Closed database connection")

    def ensure_metadata_table(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(METADATA_SCHEMA))
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
        self.connection.commit()

    def register_kafka_load(
        self,
        rows_loaded: int,
        load_mode: str,
        started_at: datetime,
        ended_at: datetime,
        consumer_group: str,
    ) -> None:
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
                TOPIC_NAME,
                TARGET_SCHEMA,
                TARGET_TABLE,
                consumer_group,
                rows_loaded,
                load_mode,
                started_at.replace(tzinfo=None),
                ended_at.replace(tzinfo=None),
            ),
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
            (TARGET_SCHEMA, TARGET_TABLE),
        )
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return columns

    def truncate_target_table(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            sql.SQL("TRUNCATE TABLE {}.{}").format(
                sql.Identifier(TARGET_SCHEMA),
                sql.Identifier(TARGET_TABLE),
            )
        )
        cursor.close()
        self.log(f"Truncated target table: {TARGET_SCHEMA}.{TARGET_TABLE}")

    def build_consumer(self, consumer_group: str) -> KafkaConsumer:
        return KafkaConsumer(
            TOPIC_NAME,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            group_id=consumer_group,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
            key_deserializer=lambda value: value.decode("utf-8") if value else None,
            consumer_timeout_ms=15000,
            max_poll_records=1000,
        )

    def transform_payload_to_row(self, payload: dict[str, object], target_columns: list[str]) -> tuple[object, ...]:
        normalized_payload = {
            clean_identifier(str(key)): value for key, value in payload.items()
        }
        return tuple(normalized_payload.get(column) for column in target_columns)

    def create_temp_table(self, temp_table_name: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            sql.SQL("CREATE TEMP TABLE {} (LIKE {}.{} INCLUDING DEFAULTS)").format(
                sql.Identifier(temp_table_name),
                sql.Identifier(TARGET_SCHEMA),
                sql.Identifier(TARGET_TABLE),
            )
        )
        cursor.close()

    def insert_rows(self, table_name: str, rows: list[tuple[object, ...]], target_columns: list[str]) -> None:
        if not rows:
            return

        cursor = self.connection.cursor()
        insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(sql.Identifier(column) for column in target_columns),
        )
        execute_values(cursor, insert_sql.as_string(self.connection), rows, page_size=1000)
        cursor.close()

    def replace_target_from_temp(self, temp_table_name: str, target_columns: list[str]) -> None:
        cursor = self.connection.cursor()
        self.truncate_target_table()
        cursor.execute(
            sql.SQL("INSERT INTO {}.{} ({}) SELECT {} FROM {}").format(
                sql.Identifier(TARGET_SCHEMA),
                sql.Identifier(TARGET_TABLE),
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
                sql.Identifier(TARGET_SCHEMA),
                sql.Identifier(TARGET_TABLE),
            )
        )
        row_count = cursor.fetchone()[0]
        cursor.close()
        return row_count

    def load_topic_to_raw(self) -> int:
        started_at = datetime.now(timezone.utc)
        consumer_group = (
            "customerdna-client1-marketing-campaign-dw-loader-"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
        )
        target_columns = self.get_target_columns()
        if not target_columns:
            raise RuntimeError(
                f"Target table columns not found for {TARGET_SCHEMA}.{TARGET_TABLE}. "
                "Create raw tables first."
            )

        self.ensure_metadata_table()
        consumer = self.build_consumer(consumer_group)
        total_loaded = 0
        batch: list[tuple[object, ...]] = []
        batch_size = 1000
        temp_table_name = f"tmp_{TARGET_TABLE}_{uuid.uuid4().hex[:8]}"

        try:
            self.create_temp_table(temp_table_name)

            for message in consumer:
                message_value = message.value or {}
                payload = message_value.get("payload", {})
                batch.append(self.transform_payload_to_row(payload, target_columns))

                if len(batch) >= batch_size:
                    self.insert_rows(temp_table_name, batch, target_columns)
                    total_loaded += len(batch)
                    self.log(f"Buffered {total_loaded:,} rows for {TARGET_SCHEMA}.{TARGET_TABLE}")
                    batch = []

            if batch:
                self.insert_rows(temp_table_name, batch, target_columns)
                total_loaded += len(batch)

            if total_loaded == 0:
                raise RuntimeError(
                    "No Kafka messages were consumed. Existing raw table was left untouched."
                )

            self.replace_target_from_temp(temp_table_name, target_columns)
            target_row_count = self.count_target_rows()

            if target_row_count != total_loaded:
                raise RuntimeError(
                    "Post-load verification failed: "
                    f"consumed {total_loaded:,} rows but target table contains "
                    f"{target_row_count:,} rows."
                )

            self.log(
                f"Verified target row count: {target_row_count:,} rows in "
                f"{TARGET_SCHEMA}.{TARGET_TABLE}",
                "SUCCESS",
            )
            ended_at = datetime.now(timezone.utc)
            self.register_kafka_load(
                total_loaded,
                "full_refresh_from_kafka",
                started_at,
                ended_at,
                consumer_group,
            )
            self.connection.commit()
            return total_loaded
        except Exception:
            self.connection.rollback()
            raise
        finally:
            consumer.close()


def main() -> int:
    print("=" * 80)
    print("CUSTOMERDNA AI - KAFKA TO RAW LOAD")
    print("=" * 80)
    print(f"Dataset: {DATASET_KEY}")
    print(f"Topic: {TOPIC_NAME}")
    print(f"Target table: {TARGET_SCHEMA}.{TARGET_TABLE}")

    if not validate_config():
        return 1

    loader = KafkaRawLoader(verbose=True)
    if not loader.connect_to_dw():
        return 1

    start_counter = time.perf_counter()

    try:
        rows_loaded = loader.load_topic_to_raw()
        duration_seconds = round(time.perf_counter() - start_counter, 3)
        print(f"Rows loaded: {rows_loaded:,}")
        print(f"Duration (seconds): {duration_seconds}")
        print("Kafka-to-raw load completed successfully.")
        print("=" * 80)
        return 0
    except Exception as exc:
        print(f"[ERROR] Kafka-to-raw load failed: {exc}")
        return 1
    finally:
        loader.close_connection()


if __name__ == "__main__":
    raise SystemExit(main())
