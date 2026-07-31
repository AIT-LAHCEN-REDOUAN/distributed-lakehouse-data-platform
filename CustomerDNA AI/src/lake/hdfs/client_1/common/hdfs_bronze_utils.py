"""Utility helpers for Client 1 bronze files stored in HDFS via WebHDFS."""

from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

import requests

from hdfs_bronze_config import (
    HDFS_BRONZE_ROOT,
    HDFS_NAMENODE_URI,
    HDFS_WEB_ENDPOINT,
    HDFS_WEBHDFS_USER,
)


REQUEST_TIMEOUT_SECONDS = 120
DATANODE_ALIAS_CACHE_TTL_SECONDS = 60


@dataclass(frozen=True)
class HdfsFileInfo:
    object_name: str
    path_suffix: str
    length: int


class HdfsBronzeClient:
    """Minimal WebHDFS client used by the bronze ingestion workflow."""

    def __init__(self, web_endpoint: str, namenode_uri: str, webhdfs_user: str):
        base = web_endpoint.strip().rstrip("/")
        if not base.startswith(("http://", "https://")):
            base = f"http://{base}"

        self.web_endpoint = base
        self.namenode_uri = namenode_uri
        self.webhdfs_user = webhdfs_user.strip() or "hdfs"
        self._datanode_alias_cache: dict[str, str] = {}
        self._datanode_alias_cache_expires_at = 0.0

    @staticmethod
    def normalize_path(hdfs_path: str) -> str:
        cleaned = "/" + str(hdfs_path).strip().strip("/")
        return cleaned.rstrip("/") or "/"

    def _build_url(self, hdfs_path: str) -> str:
        normalized = self.normalize_path(hdfs_path)
        return f"{self.web_endpoint}/webhdfs/v1{quote(normalized, safe='/')}"

    @staticmethod
    def _can_resolve_host(hostname: str) -> bool:
        try:
            socket.getaddrinfo(hostname, None)
            return True
        except socket.gaierror:
            return False

    @staticmethod
    def _extract_host(value: str | None) -> str:
        if not value:
            return ""
        return value.rsplit(":", 1)[0].strip().lower()

    @staticmethod
    def _extract_ip_like_host(*values: str | None) -> str:
        for value in values:
            host = HdfsBronzeClient._extract_host(value)
            if host and any(character.isdigit() for character in host):
                return host
        return ""

    def _load_datanode_alias_map(self) -> dict[str, str]:
        now = time.time()
        if self._datanode_alias_cache and now < self._datanode_alias_cache_expires_at:
            return self._datanode_alias_cache

        alias_map: dict[str, str] = {}
        response = requests.get(
            f"{self.web_endpoint}/jmx",
            params={"qry": "Hadoop:service=NameNode,name=NameNodeInfo"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        try:
            response.raise_for_status()
            payload = response.json()
            beans = payload.get("beans", [])
            if not beans:
                self._datanode_alias_cache = {}
                self._datanode_alias_cache_expires_at = now + DATANODE_ALIAS_CACHE_TTL_SECONDS
                return {}

            raw_live_nodes = beans[0].get("LiveNodes", "{}")
            live_nodes = json.loads(raw_live_nodes) if isinstance(raw_live_nodes, str) else {}

            for node_name, node_payload in live_nodes.items():
                if not isinstance(node_payload, dict):
                    continue

                node_host = self._extract_host(str(node_name))
                info_addr = str(node_payload.get("infoAddr", ""))
                xfer_addr = str(node_payload.get("xferaddr", ""))
                mapped_host = self._extract_ip_like_host(info_addr, xfer_addr)

                if not mapped_host:
                    continue

                if node_host and not self._can_resolve_host(node_host):
                    alias_map[node_host] = mapped_host

                info_host = self._extract_host(info_addr)
                if info_host and not self._can_resolve_host(info_host):
                    alias_map[info_host] = mapped_host

                xfer_host = self._extract_host(xfer_addr)
                if xfer_host and not self._can_resolve_host(xfer_host):
                    alias_map[xfer_host] = mapped_host
        finally:
            response.close()

        self._datanode_alias_cache = alias_map
        self._datanode_alias_cache_expires_at = now + DATANODE_ALIAS_CACHE_TTL_SECONDS
        return alias_map

    def _rewrite_redirect_location(self, location: str) -> str:
        parsed = urlparse(location)
        redirect_host = (parsed.hostname or "").strip().lower()
        if not redirect_host or self._can_resolve_host(redirect_host):
            return location

        alias_map = self._load_datanode_alias_map()
        resolved_host = alias_map.get(redirect_host)
        if not resolved_host:
            return location

        rewritten_netloc = resolved_host
        if parsed.port is not None:
            rewritten_netloc = f"{resolved_host}:{parsed.port}"

        return urlunparse(
            (
                parsed.scheme,
                rewritten_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )

    def _request(self, method: str, hdfs_path: str, *, params: dict[str, object], stream: bool = False):
        request_params = dict(params)
        request_params.setdefault("user.name", self.webhdfs_user)
        response = requests.request(
            method,
            self._build_url(hdfs_path),
            params=request_params,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=False,
            stream=stream,
        )
        return response

    def _request_with_redirect(
        self,
        method: str,
        hdfs_path: str,
        *,
        params: dict[str, object],
        data: bytes | None = None,
        stream: bool = False,
    ):
        response = self._request(method, hdfs_path, params=params, stream=stream)

        if response.status_code in {307, 308}:
            location = response.headers.get("Location")
            response.close()
            if not location:
                raise RuntimeError(f"Missing WebHDFS redirect location for path: {hdfs_path}")

            rewritten_location = self._rewrite_redirect_location(location)
            redirected = requests.request(
                method,
                rewritten_location,
                data=data,
                timeout=REQUEST_TIMEOUT_SECONDS,
                allow_redirects=False,
                stream=stream,
            )
            return redirected

        return response

    def path_exists(self, hdfs_path: str) -> bool:
        response = self._request("GET", hdfs_path, params={"op": "GETFILESTATUS"})
        try:
            if response.status_code == 200:
                return True
            if response.status_code == 404:
                return False
            response.raise_for_status()
            return True
        finally:
            response.close()

    def ensure_directory(self, hdfs_path: str) -> None:
        response = self._request("PUT", hdfs_path, params={"op": "MKDIRS"})
        try:
            response.raise_for_status()
        finally:
            response.close()

    def delete_path(self, hdfs_path: str, *, recursive: bool = True) -> bool:
        response = self._request(
            "DELETE",
            hdfs_path,
            params={"op": "DELETE", "recursive": str(recursive).lower()},
        )
        try:
            if response.status_code == 404:
                return False
            response.raise_for_status()
            payload = response.json()
            return bool(payload.get("boolean", False))
        finally:
            response.close()

    def upload_file(self, hdfs_path: str, local_path: Path, *, overwrite: bool = True) -> None:
        file_bytes = local_path.read_bytes()
        response = self._request_with_redirect(
            "PUT",
            hdfs_path,
            params={"op": "CREATE", "overwrite": str(overwrite).lower()},
            data=file_bytes,
        )
        try:
            response.raise_for_status()
        finally:
            response.close()

    def list_status(self, hdfs_path: str) -> list[dict[str, object]]:
        response = self._request("GET", hdfs_path, params={"op": "LISTSTATUS"})
        try:
            if response.status_code == 404:
                return []
            response.raise_for_status()
            payload = response.json()
            return list(payload.get("FileStatuses", {}).get("FileStatus", []))
        finally:
            response.close()

    def list_files(self, hdfs_path: str, *, recursive: bool = False) -> list[HdfsFileInfo]:
        normalized_path = self.normalize_path(hdfs_path)
        collected: list[HdfsFileInfo] = []

        for entry in self.list_status(normalized_path):
            path_suffix = str(entry.get("pathSuffix", ""))
            entry_type = str(entry.get("type", ""))
            child_path = self.normalize_path(f"{normalized_path}/{path_suffix}")

            if entry_type == "DIRECTORY" and recursive:
                collected.extend(self.list_files(child_path, recursive=True))
                continue

            if entry_type == "FILE":
                collected.append(
                    HdfsFileInfo(
                        object_name=child_path,
                        path_suffix=path_suffix,
                        length=int(entry.get("length", 0)),
                    )
                )

        return collected

    def open_file_stream(self, hdfs_path: str):
        response = self._request_with_redirect(
            "GET",
            hdfs_path,
            params={"op": "OPEN"},
            stream=True,
        )
        response.raise_for_status()
        return response


def build_hdfs_client() -> HdfsBronzeClient:
    return HdfsBronzeClient(HDFS_WEB_ENDPOINT, HDFS_NAMENODE_URI, HDFS_WEBHDFS_USER)


def bronze_dataset_path(dataset_key: str) -> str:
    return HdfsBronzeClient.normalize_path(f"{HDFS_BRONZE_ROOT}/{dataset_key}")


def bronze_dataset_prefix(dataset_key: str) -> str:
    """Compatibility alias used by the Kafka bronze consumer."""
    return bronze_dataset_path(dataset_key)


def bronze_run_path(dataset_key: str, run_id: str) -> str:
    return HdfsBronzeClient.normalize_path(f"{bronze_dataset_path(dataset_key)}/{run_id}")


def bronze_run_prefix(dataset_key: str, run_id: str) -> str:
    """Compatibility alias used by the Kafka bronze consumer."""
    return bronze_run_path(dataset_key, run_id)


def ensure_bronze_root_exists(client: HdfsBronzeClient) -> None:
    client.ensure_directory(HDFS_BRONZE_ROOT)


def upload_bronze_batch_file(
    *,
    client: HdfsBronzeClient,
    dataset_key: str,
    run_id: str,
    batch_index: int,
    local_path: Path,
) -> str:
    ensure_bronze_root_exists(client)
    client.ensure_directory(bronze_dataset_path(dataset_key))
    client.ensure_directory(bronze_run_path(dataset_key, run_id))

    target_path = HdfsBronzeClient.normalize_path(
        f"{bronze_run_path(dataset_key, run_id)}/batch_{batch_index:06d}.jsonl"
    )
    client.upload_file(target_path, local_path, overwrite=True)
    return target_path


def list_bronze_objects(client: HdfsBronzeClient, dataset_key: str) -> list[HdfsFileInfo]:
    return client.list_files(bronze_dataset_path(dataset_key), recursive=True)


def list_bronze_objects_by_prefix(client: HdfsBronzeClient, prefix: str) -> list[HdfsFileInfo]:
    return client.list_files(prefix, recursive=True)


def remove_bronze_objects(client: HdfsBronzeClient, prefix: str | None = None) -> bool:
    target_path = prefix or HDFS_BRONZE_ROOT
    if not client.path_exists(target_path):
        return False

    deleted = client.delete_path(target_path, recursive=True)
    client.ensure_directory(HDFS_BRONZE_ROOT)
    return deleted
