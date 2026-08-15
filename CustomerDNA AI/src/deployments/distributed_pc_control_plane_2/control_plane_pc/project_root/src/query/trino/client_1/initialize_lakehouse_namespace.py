"""Create the Client 1 Iceberg namespaces in Trino if they do not already exist."""

from __future__ import annotations

import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
COMMON_DIR = CURRENT_DIR / "common"

if str(COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_DIR))

from trino_rest import TRINO_CATALOG, TRINO_SCHEMA, TRINO_URL, execute_trino_statement  # noqa: E402


REQUIRED_SCHEMAS = [
    TRINO_SCHEMA,
    "staging",
    "intermediate",
    "analytics",
]


def main() -> int:
    print("=" * 80)
    print("CUSTOMERDNA AI - TRINO LAKEHOUSE NAMESPACE INITIALIZATION")
    print("=" * 80)
    print(f"Trino URL: {TRINO_URL}")
    print(f"Catalog: {TRINO_CATALOG}")
    print(f"Base schema: {TRINO_SCHEMA}")

    for schema_name in REQUIRED_SCHEMAS:
        execute_trino_statement(f"CREATE SCHEMA IF NOT EXISTS {TRINO_CATALOG}.{schema_name}")
    schemas_result = execute_trino_statement(f"SHOW SCHEMAS FROM {TRINO_CATALOG}")
    available_schemas = [row[0] for row in schemas_result["rows"]]

    missing_schemas = [
        schema_name for schema_name in REQUIRED_SCHEMAS if schema_name not in available_schemas
    ]
    if missing_schemas:
        raise RuntimeError(
            "The following lakehouse schemas were not visible after initialization: "
            + ", ".join(f"{TRINO_CATALOG}.{schema_name}" for schema_name in missing_schemas)
        )

    print("[SUCCESS] Lakehouse schemas are ready:")
    for schema_name in REQUIRED_SCHEMAS:
        print(f"  - {TRINO_CATALOG}.{schema_name}")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
