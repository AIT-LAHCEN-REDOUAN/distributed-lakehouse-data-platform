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
MINIO_ENV_PATH = CUSTOMERDNA_ROOT / "src" / "lake" / "minio" / ".env"


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}

    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()

    return values


LOCAL_MINIO_ENV = load_env_file(MINIO_ENV_PATH)


def get_setting(name: str, default: str = "") -> str:
    return os.getenv(name, LOCAL_MINIO_ENV.get(name, default)).strip()

MINIO_ENDPOINT = get_setting("CUSTOMERDNA_MINIO_ENDPOINT", default_minio_endpoint())
MINIO_ACCESS_KEY = get_setting("CUSTOMERDNA_MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = get_setting("CUSTOMERDNA_MINIO_SECRET_KEY")
MINIO_BUCKET_NAME = get_setting("CUSTOMERDNA_MINIO_BUCKET", "customerdna-bronze")
MINIO_OBJECT_PREFIX = get_setting("CUSTOMERDNA_MINIO_OBJECT_PREFIX", "bronze").strip("/")

if not MINIO_ACCESS_KEY or not MINIO_SECRET_KEY:
    raise RuntimeError(
        "Missing MinIO credentials. Set CUSTOMERDNA_MINIO_ACCESS_KEY and "
        "CUSTOMERDNA_MINIO_SECRET_KEY in the environment or in "
        f"{MINIO_ENV_PATH}."
    )
