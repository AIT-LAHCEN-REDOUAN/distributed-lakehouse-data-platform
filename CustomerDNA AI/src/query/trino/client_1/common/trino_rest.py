"""Minimal Trino REST helpers for the Client 1 lakehouse workflows."""

from __future__ import annotations

import os
import time
from typing import Any

import requests


TRINO_URL = os.getenv("CUSTOMERDNA_TRINO_URL", "http://localhost:8088").rstrip("/")
TRINO_USER = os.getenv("CUSTOMERDNA_TRINO_USER", "customerdna")
TRINO_CATALOG = os.getenv("CUSTOMERDNA_TRINO_CATALOG", "lakehouse")
TRINO_SCHEMA = os.getenv("CUSTOMERDNA_TRINO_SCHEMA", "raw_data")
TRINO_STATEMENT_MAX_ATTEMPTS = int(os.getenv("CUSTOMERDNA_TRINO_STATEMENT_MAX_ATTEMPTS", "3"))
TRINO_STATEMENT_RETRY_DELAY_SECONDS = float(
    os.getenv("CUSTOMERDNA_TRINO_STATEMENT_RETRY_DELAY_SECONDS", "5")
)


def _is_retryable_trino_error(message: str) -> bool:
    normalized = message.lower()
    retryable_markers = (
        "sockettimeoutexception",
        "read timed out",
        "timed out",
        "connection refused",
        "connection reset",
        "metastore",
    )
    return any(marker in normalized for marker in retryable_markers)


def execute_trino_statement(
    sql_text: str,
    *,
    trino_url: str | None = None,
    user: str | None = None,
    catalog: str | None = None,
    schema: str | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    base_url = (trino_url or TRINO_URL).rstrip("/")
    statement_url = f"{base_url}/v1/statement"
    headers = {
        "X-Trino-User": user or TRINO_USER,
        "X-Trino-Catalog": catalog or TRINO_CATALOG,
        "X-Trino-Schema": schema or TRINO_SCHEMA,
    }

    last_error: Exception | None = None
    for attempt in range(1, TRINO_STATEMENT_MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                statement_url,
                data=sql_text.encode("utf-8"),
                headers=headers,
                timeout=timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            rows = list(payload.get("data", []))
            columns = list(payload.get("columns", []))
            next_uri = payload.get("nextUri")
            final_payload = payload

            while next_uri:
                poll_response = requests.get(next_uri, timeout=timeout_seconds)
                poll_response.raise_for_status()
                final_payload = poll_response.json()
                rows.extend(final_payload.get("data", []))
                if final_payload.get("columns"):
                    columns = list(final_payload["columns"])
                next_uri = final_payload.get("nextUri")
                if next_uri:
                    time.sleep(0.2)

            if final_payload.get("error"):
                message = final_payload["error"].get("message", "Unknown Trino execution error.")
                if attempt < TRINO_STATEMENT_MAX_ATTEMPTS and _is_retryable_trino_error(message):
                    print(
                        f"[WARN] Trino statement attempt {attempt}/{TRINO_STATEMENT_MAX_ATTEMPTS} "
                        f"failed with a retryable error: {message}"
                    )
                    time.sleep(TRINO_STATEMENT_RETRY_DELAY_SECONDS)
                    continue
                raise RuntimeError(message)

            return {
                "rows": rows,
                "columns": columns,
                "final_payload": final_payload,
            }
        except (requests.RequestException, RuntimeError) as exc:
            last_error = exc
            message = str(exc)
            if attempt < TRINO_STATEMENT_MAX_ATTEMPTS and _is_retryable_trino_error(message):
                print(
                    f"[WARN] Trino statement attempt {attempt}/{TRINO_STATEMENT_MAX_ATTEMPTS} "
                    f"failed with a retryable error: {message}"
                )
                time.sleep(TRINO_STATEMENT_RETRY_DELAY_SECONDS)
                continue
            raise

    if last_error is not None:
        raise last_error
    raise RuntimeError("Trino statement failed without returning an explicit error.")
