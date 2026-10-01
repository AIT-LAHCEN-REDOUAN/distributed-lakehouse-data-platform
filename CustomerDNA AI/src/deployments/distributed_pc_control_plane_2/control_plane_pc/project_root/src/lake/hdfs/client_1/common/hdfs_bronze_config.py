"""Shared configuration for the Client 1 HDFS bronze layer."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def customerdna_root() -> Path:
    current_path = Path(__file__).resolve()

    for candidate in current_path.parents:
        if (candidate / "src").is_dir() and (candidate / "datasets").is_dir():
            return candidate

    return current_path.parents[5]


CUSTOMERDNA_ROOT = customerdna_root()
HDFS_ENV_PATH = CUSTOMERDNA_ROOT / "src" / "lake" / "hdfs" / ".env"

if load_dotenv:
    if HDFS_ENV_PATH.exists():
        load_dotenv(HDFS_ENV_PATH, override=False)


def _default_hdfs_web_endpoint() -> str:
    return "localhost:9870"


def _default_hdfs_namenode_uri() -> str:
    return "hdfs://localhost:9000"


def _normalize_bronze_root(path_value: str) -> str:
    cleaned = "/" + path_value.strip().strip("/")
    return cleaned.rstrip("/") or "/bronze/client_1"


HDFS_WEB_ENDPOINT = os.getenv("CUSTOMERDNA_HDFS_WEB_ENDPOINT", _default_hdfs_web_endpoint()).strip()
HDFS_NAMENODE_URI = os.getenv("CUSTOMERDNA_HDFS_NAMENODE_URI", _default_hdfs_namenode_uri()).strip()
HDFS_BRONZE_ROOT = _normalize_bronze_root(
    os.getenv("CUSTOMERDNA_HDFS_BRONZE_ROOT", "/bronze/client_1")
)
HDFS_WEBHDFS_USER = os.getenv("CUSTOMERDNA_HDFS_WEBHDFS_USER", "hdfs").strip() or "hdfs"
