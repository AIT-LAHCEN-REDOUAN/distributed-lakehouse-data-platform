"""Dataset-specific source readers for Client 1 Kafka ingestion."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

import pandas as pd

from kafka_config import SOURCE_DATASET_CONFIGS


def get_source_label(dataset_key: str) -> str:
    """Return a human-readable source label for the dataset."""
    return str(SOURCE_DATASET_CONFIGS[dataset_key]["source_label"])


def get_source_paths(dataset_key: str) -> list[Path]:
    """Return all source paths required for the dataset."""
    return list(SOURCE_DATASET_CONFIGS[dataset_key]["source_paths"])


def ensure_source_paths_exist(dataset_key: str) -> list[Path]:
    """Validate source files exist before ingestion starts."""
    source_paths = get_source_paths(dataset_key)
    missing_paths = [path for path in source_paths if not path.exists()]

    if missing_paths:
        missing_display = ", ".join(str(path) for path in missing_paths)
        raise FileNotFoundError(f"Source dataset not found for {dataset_key}: {missing_display}")

    return source_paths


def get_source_columns(dataset_key: str) -> list[str]:
    """Read the source header contract without scanning the full dataset."""
    source_paths = ensure_source_paths_exist(dataset_key)

    if dataset_key == "bank_marketing":
        return _get_csv_columns(source_paths[0], delimiter=";")
    if dataset_key == "online_shoppers_intention":
        return _get_csv_columns(source_paths[0], delimiter=",")
    if dataset_key == "online_retail_2":
        combined_columns: list[str] = []
        for sheet_name in SOURCE_DATASET_CONFIGS["online_retail_2"]["sheet_names"]:
            dataframe = pd.read_excel(
                source_paths[0],
                sheet_name=sheet_name,
                engine="openpyxl",
                nrows=0,
            )
            for column_name in dataframe.columns:
                column_as_text = str(column_name)
                if column_as_text not in combined_columns:
                    combined_columns.append(column_as_text)
        return combined_columns

    raise KeyError(f"Unsupported dataset key: {dataset_key}")


def iter_source_rows(dataset_key: str) -> Iterator[dict[str, str | None]]:
    """Stream normalized rows from the configured raw source dataset."""
    source_paths = ensure_source_paths_exist(dataset_key)

    if dataset_key == "bank_marketing":
        yield from _iter_csv_rows(source_paths[0], delimiter=";")
    elif dataset_key == "online_shoppers_intention":
        yield from _iter_csv_rows(source_paths[0], delimiter=",")
    elif dataset_key == "online_retail_2":
        yield from _iter_online_retail_rows(source_paths[0])
    else:
        raise KeyError(f"Unsupported dataset key: {dataset_key}")


def _normalize_value(
    value: object,
    *,
    date_format: str | None = None,
) -> str | None:
    """Normalize values to Kafka-friendly strings while preserving NULLs."""
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, pd.Timestamp):
        return value.strftime(date_format or "%Y-%m-%d %H:%M:%S")

    if isinstance(value, str):
        cleaned = value.strip().encode("utf-8", "ignore").decode("utf-8")
        if cleaned == "" or cleaned.lower() in {"nan", "nat"}:
            return None
        return cleaned

    return str(value)


def _iter_csv_rows(source_path: Path, *, delimiter: str) -> Iterator[dict[str, str | None]]:
    with source_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        for row in reader:
            yield {
                key: _normalize_value(value)
                for key, value in row.items()
            }


def _get_csv_columns(source_path: Path, *, delimiter: str) -> list[str]:
    with source_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        return list(reader.fieldnames or [])


def _iter_online_retail_rows(source_path: Path) -> Iterator[dict[str, str | None]]:
    sheet_names = SOURCE_DATASET_CONFIGS["online_retail_2"]["sheet_names"]

    for sheet_name in sheet_names:
        dataframe = pd.read_excel(
            source_path,
            sheet_name=sheet_name,
            engine="openpyxl",
        )

        if "Customer ID" in dataframe.columns:
            dataframe["Customer ID"] = dataframe["Customer ID"].fillna(-1)

        if "Description" in dataframe.columns:
            dataframe["Description"] = dataframe["Description"].fillna("Unknown")

        if "InvoiceDate" in dataframe.columns:
            dataframe["InvoiceDate"] = pd.to_datetime(dataframe["InvoiceDate"], errors="coerce")

        columns = list(dataframe.columns)

        for row_values in dataframe.itertuples(index=False, name=None):
            row_payload: dict[str, str | None] = {}

            for column_name, row_value in zip(columns, row_values):
                if column_name == "Customer ID" and row_value is not None and not pd.isna(row_value):
                    try:
                        row_value = int(row_value)
                    except (TypeError, ValueError):
                        pass

                if column_name == "InvoiceDate":
                    row_payload[column_name] = _normalize_value(
                        row_value,
                        date_format="%Y-%m-%d %H:%M:%S",
                    )
                else:
                    row_payload[column_name] = _normalize_value(row_value)

            yield row_payload
