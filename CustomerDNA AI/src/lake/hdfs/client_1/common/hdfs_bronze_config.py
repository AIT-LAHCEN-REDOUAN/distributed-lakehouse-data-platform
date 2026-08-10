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
HDFS_WEB_VERIFY_TLS = os.getenv("CUSTOMERDNA_HDFS_WEB_VERIFY_TLS", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
HDFS_WEB_CA_CERT_PATH = os.getenv("CUSTOMERDNA_HDFS_WEB_CA_CERT_PATH", "").strip()
HDFS_NAMENODE_URI = os.getenv("CUSTOMERDNA_HDFS_NAMENODE_URI", _default_hdfs_namenode_uri()).strip()
HDFS_BRONZE_ROOT = _normalize_bronze_root(
    os.getenv("CUSTOMERDNA_HDFS_BRONZE_ROOT", "/bronze/client_1")
)
HDFS_WEBHDFS_USER = os.getenv("CUSTOMERDNA_HDFS_WEBHDFS_USER", "hdfs").strip() or "hdfs"
HDFS_ACCESS_MODE = os.getenv("CUSTOMERDNA_HDFS_ACCESS_MODE", "webhdfs").strip().lower() or "webhdfs"
HDFS_REMOTE_SSH_HOST = os.getenv("CUSTOMERDNA_HDFS_REMOTE_SSH_HOST", "").strip()
HDFS_REMOTE_SSH_PORT = int(os.getenv("CUSTOMERDNA_HDFS_REMOTE_SSH_PORT", "22").strip() or "22")
HDFS_REMOTE_SSH_USER = os.getenv("CUSTOMERDNA_HDFS_REMOTE_SSH_USER", "").strip()
HDFS_REMOTE_SSH_KEY_PATH = os.getenv("CUSTOMERDNA_HDFS_REMOTE_SSH_KEY_PATH", "").strip()
HDFS_REMOTE_CONTAINER_NAME = os.getenv("CUSTOMERDNA_HDFS_REMOTE_CONTAINER_NAME", "hdfs-admin-client").strip() or "hdfs-admin-client"
HDFS_REMOTE_KRB5_CONFIG_PATH = os.getenv("CUSTOMERDNA_HDFS_REMOTE_KRB5_CONFIG_PATH", "/etc/krb5.conf").strip() or "/etc/krb5.conf"
HDFS_REMOTE_KINIT_PRINCIPAL = os.getenv("CUSTOMERDNA_HDFS_REMOTE_KINIT_PRINCIPAL", "").strip()
HDFS_REMOTE_KINIT_KEYTAB_PATH = os.getenv("CUSTOMERDNA_HDFS_REMOTE_KINIT_KEYTAB_PATH", "").strip()
HDFS_REMOTE_STAGING_HOST_DIR = os.getenv(
    "CUSTOMERDNA_HDFS_REMOTE_STAGING_HOST_DIR",
    "/tmp/customerdna_hdfs_admin_staging",
).strip() or "/tmp/customerdna_hdfs_admin_staging"
HDFS_REMOTE_STAGING_CONTAINER_DIR = os.getenv(
    "CUSTOMERDNA_HDFS_REMOTE_STAGING_CONTAINER_DIR",
    HDFS_REMOTE_STAGING_HOST_DIR,
).strip() or HDFS_REMOTE_STAGING_HOST_DIR


def describe_hdfs_access() -> str:
    if HDFS_ACCESS_MODE == "ssh_cli":
        return (
            f"SSH CLI via {HDFS_REMOTE_SSH_USER}@{HDFS_REMOTE_SSH_HOST}:{HDFS_REMOTE_SSH_PORT} "
            f"-> container {HDFS_REMOTE_CONTAINER_NAME}"
        )

    return f"WebHDFS via {HDFS_WEB_ENDPOINT} as {HDFS_WEBHDFS_USER}"
