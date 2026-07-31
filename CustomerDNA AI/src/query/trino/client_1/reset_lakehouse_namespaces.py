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


def _schema_exists(schema_name: str) -> bool:
    schemas_result = execute_trino_statement(f"SHOW SCHEMAS FROM {TRINO_CATALOG}")
    available_schemas = {row[0] for row in schemas_result["rows"]}
    return schema_name in available_schemas


def _list_tables(schema_name: str) -> list[str]:
    if not _schema_exists(schema_name):
        return []

    tables_result = execute_trino_statement(f"SHOW TABLES FROM {TRINO_CATALOG}.{schema_name}")
    return [row[0] for row in tables_result["rows"]]


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
                qualified_table = f'{TRINO_CATALOG}.{schema_name}."{table_name}"'
                execute_trino_statement(f"DROP TABLE IF EXISTS {qualified_table}")
                print(f"[SUCCESS] Dropped table: {qualified_table}")
        else:
            print(f"[INFO] No managed tables found in schema: {TRINO_CATALOG}.{schema_name}")

        execute_trino_statement(f"DROP SCHEMA IF EXISTS {TRINO_CATALOG}.{schema_name}")
        print(f"[SUCCESS] Dropped schema: {TRINO_CATALOG}.{schema_name}")

    remaining_schemas = execute_trino_statement(f"SHOW SCHEMAS FROM {TRINO_CATALOG}")
    visible_schema_names = {row[0] for row in remaining_schemas["rows"]}
    still_present = [schema_name for schema_name in RESET_SCHEMAS if schema_name in visible_schema_names]
    if still_present:
        raise RuntimeError(
            "The following schemas are still visible after reset: "
            + ", ".join(f"{TRINO_CATALOG}.{schema_name}" for schema_name in still_present)
        )

    print("[SUCCESS] Client 1 lakehouse schemas were removed successfully.")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
