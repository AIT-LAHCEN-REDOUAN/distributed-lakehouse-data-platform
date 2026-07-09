"""Shared configuration for the Client 1 MinIO bronze layer."""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[6]


def customerdna_root() -> Path:
    current_path = Path(__file__).resolve()

    for candidate in current_path.parents:
        if (candidate / "src").is_dir() and (candidate / "datasets").is_dir():
            return candidate

    return project_root() / "CustomerDNA AI"


def default_minio_endpoint() -> str:
    if Path("/.dockerenv").exists():
        return "minio:9000"
    return "localhost:9000"


CUSTOMERDNA_ROOT = customerdna_root()
MINIO_CLIENT_ROOT = Path(__file__).resolve().parents[1]

MINIO_ENDPOINT = os.getenv("CUSTOMERDNA_MINIO_ENDPOINT", default_minio_endpoint()).strip()
MINIO_ACCESS_KEY = os.getenv("CUSTOMERDNA_MINIO_ACCESS_KEY", "minioadmin").strip()
MINIO_SECRET_KEY = os.getenv("CUSTOMERDNA_MINIO_SECRET_KEY", "minioadmin").strip()
MINIO_BUCKET_NAME = os.getenv("CUSTOMERDNA_MINIO_BUCKET", "customerdna-bronze").strip()
MINIO_OBJECT_PREFIX = os.getenv("CUSTOMERDNA_MINIO_OBJECT_PREFIX", "bronze").strip().strip("/")
