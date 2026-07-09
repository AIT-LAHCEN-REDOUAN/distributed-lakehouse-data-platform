"""Utility helpers for Client 1 bronze objects stored in MinIO."""

from __future__ import annotations

from pathlib import Path

from minio.deleteobjects import DeleteObject
from minio.error import S3Error

from minio_bronze_config import (
    MINIO_ACCESS_KEY,
    MINIO_BUCKET_NAME,
    MINIO_ENDPOINT,
    MINIO_OBJECT_PREFIX,
    MINIO_SECRET_KEY,
)


def build_minio_client():
    from minio import Minio

    secure = MINIO_ENDPOINT.startswith("https://")
    normalized_endpoint = (
        MINIO_ENDPOINT.replace("https://", "", 1).replace("http://", "", 1)
    )

    return Minio(
        normalized_endpoint,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=secure,
    )


def ensure_bucket_exists(client) -> None:
    if not client.bucket_exists(MINIO_BUCKET_NAME):
        client.make_bucket(MINIO_BUCKET_NAME)
        print(f"[INFO] Created MinIO bucket: {MINIO_BUCKET_NAME}")
    else:
        print(f"[INFO] MinIO bucket already exists: {MINIO_BUCKET_NAME}")


def client_bronze_root_prefix() -> str:
    """Return the root prefix used for Client 1 bronze data."""
    return f"{MINIO_OBJECT_PREFIX}/client_1/kafka_topics"


def bronze_dataset_prefix(dataset_key: str) -> str:
    """Return the bronze prefix for one dataset."""
    return f"{client_bronze_root_prefix()}/{dataset_key}"


def bronze_run_prefix(dataset_key: str, run_id: str) -> str:
    """Return the bronze prefix for one specific dataset run."""
    return f"{bronze_dataset_prefix(dataset_key)}/run_id={run_id}"


def bronze_batch_object_key(dataset_key: str, run_id: str, batch_index: int) -> str:
    """Return the object key for one uploaded JSONL bronze batch."""
    return f"{bronze_run_prefix(dataset_key, run_id)}/part_{batch_index:05d}.jsonl"


def upload_bronze_batch_file(*, client, dataset_key: str, run_id: str, batch_index: int, local_path: Path) -> str:
    """Upload one local JSONL batch file into MinIO bronze."""
    object_key = bronze_batch_object_key(dataset_key, run_id, batch_index)
    client.fput_object(MINIO_BUCKET_NAME, object_key, str(local_path))
    return object_key


def list_bronze_objects(client, dataset_key: str | None = None) -> list:
    """Return all bronze objects for Client 1 or for one dataset."""
    prefix = bronze_dataset_prefix(dataset_key) if dataset_key else client_bronze_root_prefix()
    return list_bronze_objects_by_prefix(client, prefix)


def list_bronze_objects_by_prefix(client, prefix: str) -> list:
    """Return bronze objects under an explicit MinIO prefix."""
    try:
        return list(client.list_objects(MINIO_BUCKET_NAME, prefix=prefix, recursive=True))
    except S3Error as exc:
        if exc.code == "NoSuchBucket":
            return []
        raise


def remove_bronze_objects(client, dataset_key: str | None = None) -> int:
    """Delete bronze objects for Client 1 or for one dataset and return the deleted count."""
    objects = list_bronze_objects(client, dataset_key)
    if not objects:
        return 0

    delete_errors = list(
        client.remove_objects(
            MINIO_BUCKET_NAME,
            (DeleteObject(obj.object_name) for obj in objects),
        )
    )
    if delete_errors:
        failing_objects = ", ".join(error.object_name for error in delete_errors)
        raise RuntimeError(f"Failed to delete one or more bronze objects: {failing_objects}")

    return len(objects)
