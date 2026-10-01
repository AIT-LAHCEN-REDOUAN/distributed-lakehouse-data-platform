"""Drop the Client 1 Iceberg lakehouse schemas and managed objects through Trino."""

from __future__ import annotations

import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
COMMON_DIR = CURRENT_DIR / "common"

if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from trino_rest import TRINO_CATALOG, TRINO_SCHEMA, TRINO_URL, execute_trino_statement  # noqa: E402


RESET_SCHEMAS = [
    "analytics",
    "intermediate",
    "staging",
    TRINO_SCHEMA,
]

TRINO_SCHEMA_DROP_WARNING_MARKERS = (
    "java.lang.nullpointerexception",
)

TRINO_TABLE_DROP_WARNING_MARKERS = (
    "table '",
    "not found",
)


def _schema_exists(schema_name: str) -> bool:
    schemas_result = execute_trino_statement(f"SHOW SCHEMAS FROM {TRINO_CATALOG}")
    available_schemas = {row[0] for row in schemas_result["rows"]}
    return schema_name in available_schemas


def _list_tables(schema_name: str) -> list[str]:
    if not _schema_exists(schema_name):
        return []

    tables_result = execute_trino_statement(f"SHOW TABLES FROM {TRINO_CATALOG}.{schema_name}")
    return [row[0] for row in tables_result["rows"]]


def _drop_schema_if_possible(schema_name: str) -> None:
    qualified_schema = f"{TRINO_CATALOG}.{schema_name}"
    try:
        execute_trino_statement(f"DROP SCHEMA IF EXISTS {qualified_schema}")
        print(f"[SUCCESS] Dropped schema: {qualified_schema}")
    except RuntimeError as exc:
        message = str(exc).strip()
        normalized = message.lower()
        if any(marker in normalized for marker in TRINO_SCHEMA_DROP_WARNING_MARKERS):
            print(
                f"[WARN] Trino could not drop empty schema {qualified_schema} due to a connector-side "
                f"error ({message}). Continuing because the schema contents were already cleared."
            )
            return
        raise


def _drop_table_if_possible(schema_name: str, table_name: str) -> None:
    qualified_table = f'{TRINO_CATALOG}.{schema_name}."{table_name}"'
    try:
        execute_trino_statement(f"DROP TABLE IF EXISTS {qualified_table}")
        print(f"[SUCCESS] Dropped table: {qualified_table}")
    except RuntimeError as exc:
        message = str(exc).strip()
        normalized = message.lower()
        if all(marker in normalized for marker in TRINO_TABLE_DROP_WARNING_MARKERS):
            print(
                f"[WARN] Trino reported table already absent while dropping {qualified_table} "
                f"({message}). Continuing because the table was already removed."
            )
            return
        raise


def main() -> int:
    print("=" * 80)
    print("CUSTOMERDNA AI - TRINO LAKEHOUSE RESET")
    print("=" * 80)
    print(f"Trino URL: {TRINO_URL}")
    print(f"Catalog: {TRINO_CATALOG}")
    print("Schemas scheduled for cleanup:")
    for schema_name in RESET_SCHEMAS:
        print(f"  - {TRINO_CATALOG}.{schema_name}")

    for schema_name in RESET_SCHEMAS:
        if not _schema_exists(schema_name):
            print(f"[INFO] Schema does not exist, skipping: {TRINO_CATALOG}.{schema_name}")
            continue

        tables = _list_tables(schema_name)
        if tables:
            for table_name in tables:
                _drop_table_if_possible(schema_name, table_name)
        else:
            print(f"[INFO] No managed tables found in schema: {TRINO_CATALOG}.{schema_name}")

        _drop_schema_if_possible(schema_name)

    non_empty_schemas: list[str] = []
    for schema_name in RESET_SCHEMAS:
        if _list_tables(schema_name):
            non_empty_schemas.append(schema_name)

    if non_empty_schemas:
        raise RuntimeError(
            "The following schemas still contain tables after reset: "
            + ", ".join(f"{TRINO_CATALOG}.{schema_name}" for schema_name in non_empty_schemas)
        )

    print("[SUCCESS] Client 1 lakehouse schemas were cleared successfully.")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
