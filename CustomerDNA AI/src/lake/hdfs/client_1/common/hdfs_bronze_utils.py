"""Utility helpers for Client 1 bronze files stored in HDFS via WebHDFS."""

from __future__ import annotations

import json
import os
import re
import shlex
import socket
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

import requests

try:
    import paramiko  # type: ignore
except Exception:  # pragma: no cover - optional dependency for secure deployment mode
    paramiko = None

from hdfs_bronze_config import (
    HDFS_ACCESS_MODE,
    HDFS_BRONZE_ROOT,
    HDFS_NAMENODE_URI,
    HDFS_REMOTE_CONTAINER_NAME,
    HDFS_REMOTE_KINIT_KEYTAB_PATH,
    HDFS_REMOTE_KINIT_PRINCIPAL,
    HDFS_REMOTE_KRB5_CONFIG_PATH,
    HDFS_REMOTE_SSH_HOST,
    HDFS_REMOTE_SSH_KEY_PATH,
    HDFS_REMOTE_SSH_KNOWN_HOSTS_PATH,
    HDFS_REMOTE_SSH_PORT,
    HDFS_REMOTE_SSH_USER,
    HDFS_REMOTE_STAGING_CONTAINER_DIR,
    HDFS_REMOTE_STAGING_HOST_DIR,
    HDFS_WEB_CA_CERT_PATH,
    HDFS_WEB_ENDPOINT,
    HDFS_WEB_VERIFY_TLS,
    HDFS_WEBHDFS_USER,
)


REQUEST_TIMEOUT_SECONDS = 120
DATANODE_ALIAS_CACHE_TTL_SECONDS = 60
SSH_CONNECT_TIMEOUT_SECONDS = 20
HDFS_LS_LINE_PATTERN = re.compile(
    r"^(?P<permissions>[dl-][rwx-]{9})\s+"
    r"(?P<replication>\d+|-)\s+"
    r"(?P<owner>\S+)\s+"
    r"(?P<group>\S+)\s+"
    r"(?P<length>\d+)\s+"
    r"(?P<date>\d{4}-\d{2}-\d{2})\s+"
    r"(?P<time>\d{2}:\d{2})\s+"
    r"(?P<path>.+)$"
)


def _requests_verify_argument() -> bool | str:
    if HDFS_WEB_VERIFY_TLS and HDFS_WEB_CA_CERT_PATH:
        return HDFS_WEB_CA_CERT_PATH
    return HDFS_WEB_VERIFY_TLS


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
            base = f"{'https' if HDFS_WEB_VERIFY_TLS else 'http'}://{base}"

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
            verify=_requests_verify_argument(),
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
            verify=_requests_verify_argument(),
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
                verify=_requests_verify_argument(),
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


class RemoteSshHdfsBronzeClient:
    """HDFS client that executes authenticated CLI operations on a remote VM over SSH."""

    def __init__(
        self,
        *,
        ssh_host: str,
        ssh_port: int,
        ssh_user: str,
        ssh_key_path: str,
        ssh_known_hosts_path: str,
        container_name: str,
        krb5_config_path: str,
        kinit_principal: str,
        kinit_keytab_path: str,
        staging_host_dir: str,
        staging_container_dir: str,
    ) -> None:
        self.ssh_host = ssh_host.strip()
        self.ssh_port = int(ssh_port)
        self.ssh_user = ssh_user.strip()
        self.ssh_key_path = ssh_key_path.strip()
        self.ssh_known_hosts_path = ssh_known_hosts_path.strip()
        self.container_name = container_name.strip()
        self.krb5_config_path = krb5_config_path.strip() or "/etc/krb5.conf"
        self.kinit_principal = kinit_principal.strip()
        self.kinit_keytab_path = kinit_keytab_path.strip()
        self.staging_host_dir = staging_host_dir.strip().rstrip("/") or "/tmp/customerdna_hdfs_admin_staging"
        self.staging_container_dir = (
            staging_container_dir.strip().rstrip("/") or self.staging_host_dir
        )

        missing_fields = []
        if not self.ssh_host:
            missing_fields.append("CUSTOMERDNA_HDFS_REMOTE_SSH_HOST")
        if not self.ssh_user:
            missing_fields.append("CUSTOMERDNA_HDFS_REMOTE_SSH_USER")
        if not self.ssh_key_path:
            missing_fields.append("CUSTOMERDNA_HDFS_REMOTE_SSH_KEY_PATH")
        if not self.ssh_known_hosts_path:
            missing_fields.append("CUSTOMERDNA_HDFS_REMOTE_SSH_KNOWN_HOSTS_PATH")
        if not self.kinit_principal:
            missing_fields.append("CUSTOMERDNA_HDFS_REMOTE_KINIT_PRINCIPAL")
        if not self.kinit_keytab_path:
            missing_fields.append("CUSTOMERDNA_HDFS_REMOTE_KINIT_KEYTAB_PATH")
        if missing_fields:
            raise RuntimeError(
                "Secure HDFS SSH mode is missing required settings: "
                + ", ".join(missing_fields)
            )

        if paramiko is None:
            raise RuntimeError(
                "Secure HDFS SSH mode requires the 'paramiko' package in the current Python runtime."
            )

        if not Path(self.ssh_key_path).exists():
            raise RuntimeError(
                "Secure HDFS SSH mode could not find the SSH private key inside the current runtime: "
                f"{self.ssh_key_path}"
            )

        if not Path(self.ssh_known_hosts_path).exists():
            raise RuntimeError(
                "Secure HDFS SSH mode could not find the SSH known_hosts file inside the current runtime: "
                f"{self.ssh_known_hosts_path}"
            )

    @staticmethod
    def normalize_path(hdfs_path: str) -> str:
        cleaned = "/" + str(hdfs_path).strip().strip("/")
        return cleaned.rstrip("/") or "/"

    def _connect(self):
        assert paramiko is not None  # pragma: no cover - guarded in __init__
        client = paramiko.SSHClient()
        client.load_host_keys(self.ssh_known_hosts_path)
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        client.connect(
            hostname=self.ssh_host,
            port=self.ssh_port,
            username=self.ssh_user,
            key_filename=self.ssh_key_path,
            look_for_keys=False,
            allow_agent=False,
            timeout=SSH_CONNECT_TIMEOUT_SECONDS,
            banner_timeout=SSH_CONNECT_TIMEOUT_SECONDS,
            auth_timeout=SSH_CONNECT_TIMEOUT_SECONDS,
        )
        return client

    def _build_container_command(self, shell_body: str) -> str:
        inner_command = (
            "set -euo pipefail; "
            f"export KRB5_CONFIG={shlex.quote(self.krb5_config_path)}; "
            "kdestroy >/dev/null 2>&1 || true; "
            f"kinit -kt {shlex.quote(self.kinit_keytab_path)} {shlex.quote(self.kinit_principal)} >/dev/null; "
            f"{shell_body}"
        )
        return (
            f"docker exec {shlex.quote(self.container_name)} "
            f"/bin/bash -lc {shlex.quote(inner_command)}"
        )

    def _run_remote_host_command(
        self,
        command: str,
        *,
        allow_exit_codes: set[int] | None = None,
    ) -> tuple[int, str, str]:
        allow_exit_codes = allow_exit_codes or {0}
        client = self._connect()
        try:
            _, stdout, stderr = client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode("utf-8", errors="replace")
            stderr_text = stderr.read().decode("utf-8", errors="replace")
        finally:
            client.close()

        if exit_code not in allow_exit_codes:
            raise RuntimeError(
                f"Remote HDFS command failed on {self.ssh_user}@{self.ssh_host}:{self.ssh_port} "
                f"with exit code {exit_code}.\nCommand: {command}\n"
                f"stdout:\n{stdout_text}\n"
                f"stderr:\n{stderr_text}"
            )

        return exit_code, stdout_text, stderr_text

    def _run_hdfs_command(
        self,
        shell_body: str,
        *,
        allow_exit_codes: set[int] | None = None,
    ) -> tuple[int, str, str]:
        return self._run_remote_host_command(
            self._build_container_command(shell_body),
            allow_exit_codes=allow_exit_codes,
        )

    def path_exists(self, hdfs_path: str) -> bool:
        normalized = self.normalize_path(hdfs_path)
        exit_code, _, _ = self._run_hdfs_command(
            f"hdfs dfs -test -e {shlex.quote(normalized)}",
            allow_exit_codes={0, 1},
        )
        return exit_code == 0

    def ensure_directory(self, hdfs_path: str) -> None:
        normalized = self.normalize_path(hdfs_path)
        self._run_hdfs_command(f"hdfs dfs -mkdir -p {shlex.quote(normalized)}")

    def delete_path(self, hdfs_path: str, *, recursive: bool = True) -> bool:
        normalized = self.normalize_path(hdfs_path)
        if not self.path_exists(normalized):
            return False

        recursive_flag = "-r " if recursive else ""
        self._run_hdfs_command(f"hdfs dfs -rm {recursive_flag}-f {shlex.quote(normalized)}")
        return True

    def upload_file(self, hdfs_path: str, local_path: Path, *, overwrite: bool = True) -> None:
        normalized = self.normalize_path(hdfs_path)
        remote_host_temp = f"{self.staging_host_dir}/{uuid.uuid4().hex}_{local_path.name}"
        remote_container_temp = f"{self.staging_container_dir}/{Path(remote_host_temp).name}"
        remote_parent = str(Path(normalized).parent).replace("\\", "/")

        client = self._connect()
        try:
            mkdir_command = f"mkdir -p {shlex.quote(self.staging_host_dir)}"
            _, stdout, stderr = client.exec_command(mkdir_command)
            if stdout.channel.recv_exit_status() != 0:
                raise RuntimeError(stderr.read().decode("utf-8", errors="replace"))

            sftp = client.open_sftp()
            try:
                sftp.put(str(local_path), remote_host_temp)
            finally:
                sftp.close()

            put_flags = "-f " if overwrite else ""
            remote_command = self._build_container_command(
                f"hdfs dfs -mkdir -p {shlex.quote(remote_parent)} && "
                f"hdfs dfs -put {put_flags}{shlex.quote(remote_container_temp)} {shlex.quote(normalized)} && "
                f"rm -f {shlex.quote(remote_container_temp)}"
            )
            _, stdout, stderr = client.exec_command(remote_command)
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                raise RuntimeError(
                    "Remote HDFS upload failed.\n"
                    f"stdout:\n{stdout.read().decode('utf-8', errors='replace')}\n"
                    f"stderr:\n{stderr.read().decode('utf-8', errors='replace')}"
                )
        finally:
            try:
                cleanup_command = f"rm -f {shlex.quote(remote_host_temp)}"
                _, stdout, _ = client.exec_command(cleanup_command)
                stdout.channel.recv_exit_status()
            except Exception:
                pass
            client.close()

    def list_status(self, hdfs_path: str, *, recursive: bool = False) -> list[dict[str, object]]:
        normalized = self.normalize_path(hdfs_path)
        if not self.path_exists(normalized):
            return []

        recursive_flag = "-R " if recursive else ""
        _, stdout_text, _ = self._run_hdfs_command(
            f"hdfs dfs -ls {recursive_flag}{shlex.quote(normalized)}",
        )
        entries: list[dict[str, object]] = []
        for raw_line in stdout_text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("Found "):
                continue
            match = HDFS_LS_LINE_PATTERN.match(line)
            if not match:
                continue
            path_value = str(match.group("path")).strip()
            permissions = str(match.group("permissions"))
            entries.append(
                {
                    "type": "DIRECTORY" if permissions.startswith("d") else "FILE",
                    "path": path_value,
                    "pathSuffix": Path(path_value).name,
                    "length": int(match.group("length")),
                }
            )
        return entries

    def list_files(self, hdfs_path: str, *, recursive: bool = False) -> list[HdfsFileInfo]:
        normalized_path = self.normalize_path(hdfs_path)
        collected: list[HdfsFileInfo] = []

        for entry in self.list_status(normalized_path, recursive=recursive):
            if str(entry.get("type", "")) != "FILE":
                continue
            collected.append(
                HdfsFileInfo(
                    object_name=str(entry.get("path", "")),
                    path_suffix=str(entry.get("pathSuffix", "")),
                    length=int(entry.get("length", 0)),
                )
            )

        return collected

    def open_file_stream(self, hdfs_path: str):  # pragma: no cover - not used in the deployed pipeline
        raise NotImplementedError("SSH-backed HDFS access does not implement streamed file reads.")


def build_hdfs_client() -> HdfsBronzeClient:
    if HDFS_ACCESS_MODE == "ssh_cli":
        return RemoteSshHdfsBronzeClient(
            ssh_host=HDFS_REMOTE_SSH_HOST,
            ssh_port=HDFS_REMOTE_SSH_PORT,
            ssh_user=HDFS_REMOTE_SSH_USER,
            ssh_key_path=HDFS_REMOTE_SSH_KEY_PATH,
            ssh_known_hosts_path=HDFS_REMOTE_SSH_KNOWN_HOSTS_PATH,
            container_name=HDFS_REMOTE_CONTAINER_NAME,
            krb5_config_path=HDFS_REMOTE_KRB5_CONFIG_PATH,
            kinit_principal=HDFS_REMOTE_KINIT_PRINCIPAL,
            kinit_keytab_path=HDFS_REMOTE_KINIT_KEYTAB_PATH,
            staging_host_dir=HDFS_REMOTE_STAGING_HOST_DIR,
            staging_container_dir=HDFS_REMOTE_STAGING_CONTAINER_DIR,
        )
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
