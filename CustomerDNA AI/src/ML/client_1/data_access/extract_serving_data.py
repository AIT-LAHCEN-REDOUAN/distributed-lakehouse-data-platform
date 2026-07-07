from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

try:
    import psycopg2
except ImportError as exc:  # pragma: no cover - depends on local environment
    raise SystemExit(
        "psycopg2 is required to extract serving data. Install it in your local environment first."
    ) from exc

from schema_manifest import (
    build_connection_config,
    build_snapshot_manifest,
    ensure_dataset_directories,
    load_common_config,
    load_env_file,
    load_use_case_config,
    resolve_client_env_path,
    snapshot_artifact_paths,
    write_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a reproducible training snapshot from a Client 1 serving table.",
    )
    parser.add_argument(
        "--use-case",
        default="segmentation",
        help="Use-case config name stored under src/ML/client_1/configs without the .json suffix.",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Optional override for the number of sample rows to store in datasets/samples.",
    )
    return parser.parse_args()


def quoted_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def qualified_relation(schema_name: str, table_name: str) -> str:
    return f"{quoted_identifier(schema_name)}.{quoted_identifier(table_name)}"


def fetch_columns(cursor, schema_name: str, table_name: str) -> list[str]:
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
        ORDER BY ordinal_position
        """,
        (schema_name, table_name),
    )
    return [row[0] for row in cursor.fetchall()]


def fetch_row_count(cursor, relation_sql: str) -> int:
    cursor.execute(f"SELECT COUNT(*) FROM {relation_sql}")
    return int(cursor.fetchone()[0])


def export_csv(cursor, query_sql: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        cursor.copy_expert(
            f"COPY ({query_sql}) TO STDOUT WITH CSV HEADER",
            handle,
        )


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        row_count = -1
        for row_count, _ in enumerate(reader):
            pass

    if row_count < 0:
        return 0

    return row_count


def main() -> None:
    args = parse_args()

    common_config = load_common_config()
    use_case_config = load_use_case_config(args.use_case)
    env_vars = load_env_file(resolve_client_env_path(common_config))
    connection_config = build_connection_config(common_config, env_vars)
    schema_name = common_config["serving_schema"]
    table_name = use_case_config["source_table"]
    relation_sql = qualified_relation(schema_name, table_name)
    sample_size = args.sample_size or int(common_config["default_sample_size"])
    extracted_at = datetime.now(timezone.utc)

    ensure_dataset_directories()
    artifact_paths = snapshot_artifact_paths(
        use_case_config=use_case_config,
        common_config=common_config,
        current_time=extracted_at,
    )

    order_by_columns = use_case_config.get("order_by", [])
    order_by_sql = ", ".join(quoted_identifier(column_name) for column_name in order_by_columns)
    ordered_select_sql = f"SELECT * FROM {relation_sql}"
    if order_by_sql:
        ordered_select_sql += f" ORDER BY {order_by_sql}"

    sample_select_sql = ordered_select_sql + f" LIMIT {sample_size}"

    print("=" * 80)
    print("CUSTOMERDNA AI - SERVING DATA EXTRACTION")
    print("=" * 80)
    print(f"Use case: {use_case_config['use_case']}")
    print(f"Source relation: {schema_name}.{table_name}")
    print(f"Target snapshot: {artifact_paths['snapshot_path']}")
    print(f"Target sample: {artifact_paths['sample_path']}")
    print(f"Target manifest: {artifact_paths['manifest_path']}")

    with psycopg2.connect(**connection_config) as connection:
        with connection.cursor() as cursor:
            columns = fetch_columns(cursor, schema_name, table_name)
            row_count = fetch_row_count(cursor, relation_sql)

            export_csv(cursor, ordered_select_sql, artifact_paths["snapshot_path"])
            export_csv(cursor, sample_select_sql, artifact_paths["sample_path"])

    sample_row_count = count_csv_rows(artifact_paths["sample_path"])

    manifest = build_snapshot_manifest(
        common_config=common_config,
        use_case_config=use_case_config,
        row_count=row_count,
        sample_row_count=sample_row_count,
        columns=columns,
        artifact_paths=artifact_paths,
        extracted_at=extracted_at,
    )
    write_manifest(artifact_paths["manifest_path"], manifest)

    print(f"Extracted rows: {row_count}")
    print(f"Column count: {len(columns)}")
    print(f"Sample rows: {sample_row_count}")
    print("Extraction completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
