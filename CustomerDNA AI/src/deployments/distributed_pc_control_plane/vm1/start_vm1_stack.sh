#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "${SCRIPT_DIR}"

echo "============================================================"
echo " CustomerDNA VM1 - Start Distributed Worker Node"
echo "============================================================"
echo "Directory: ${SCRIPT_DIR}"
echo "Compose   : ${SCRIPT_DIR}/docker-compose.yml"
echo "Env file  : ${SCRIPT_DIR}/.env"
echo "============================================================"

require_command() {
  local command_name="$1"
  local message="$2"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "[ERROR] ${message}"
    exit 1
  fi
}

ensure_runtime_directory_access() {
  local target_dir="$1"

  if ! mkdir -p "${target_dir}" >/dev/null 2>&1; then
    sudo mkdir -p "${target_dir}"
  fi

  if chmod -R 777 "${target_dir}" >/dev/null 2>&1; then
    return 0
  fi

  if sudo chmod -R 777 "${target_dir}" >/dev/null 2>&1; then
    return 0
  fi

  if [[ -w "${target_dir}" ]]; then
    echo "[WARN] Could not change permissions for ${target_dir}, but it is writable. Continuing."
    return 0
  fi

  echo "[ERROR] ${target_dir} is not writable for deployment startup."
  echo "        Verify the encrypted storage mount ownership or run:"
  echo "        sudo chmod -R 777 ${target_dir}"
  exit 1
}

wait_for_tcp() {
  local host="$1"
  local port="$2"
  local label="$3"
  local timeout_seconds="${4:-120}"

  if ! python3 - "${host}" "${port}" "${timeout_seconds}" <<'PY'
import socket
import sys
import time

host = sys.argv[1]
port = int(sys.argv[2])
timeout_seconds = int(sys.argv[3])
deadline = time.time() + timeout_seconds

while time.time() < deadline:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        sock.connect((host, port))
        sock.close()
        sys.exit(0)
    except OSError:
        time.sleep(2)
    finally:
        try:
            sock.close()
        except OSError:
            pass

sys.exit(1)
PY
  then
    echo "[ERROR] ${label} did not become reachable at ${host}:${port} within ${timeout_seconds}s."
    exit 1
  fi
}

wait_for_remote_kadmin() {
  local timeout_seconds="${1:-120}"
  local start_epoch
  start_epoch="$(date +%s)"

  while true; do
    if KRB5_CONFIG="${KRB5_CONFIG_FILE}" \
      kadmin -p "${CUSTOMERDNA_KRB5_ADMIN_PRINCIPAL}" -w "${CUSTOMERDNA_KRB5_ADMIN_PASSWORD}" \
      -q "listprincs" >/dev/null 2>&1; then
      return 0
    fi

    if (( "$(date +%s)" - start_epoch >= timeout_seconds )); then
      echo "[ERROR] Kerberos admin interface on VM2 did not become ready within ${timeout_seconds}s."
      exit 1
    fi

    sleep 2
  done
}

ensure_principal() {
  local principal="$1"

  if ! KRB5_CONFIG="${KRB5_CONFIG_FILE}" \
    kadmin -p "${CUSTOMERDNA_KRB5_ADMIN_PRINCIPAL}" -w "${CUSTOMERDNA_KRB5_ADMIN_PASSWORD}" \
    -q "getprinc ${principal}" >/dev/null 2>&1; then
    KRB5_CONFIG="${KRB5_CONFIG_FILE}" \
      kadmin -p "${CUSTOMERDNA_KRB5_ADMIN_PRINCIPAL}" -w "${CUSTOMERDNA_KRB5_ADMIN_PASSWORD}" \
      -q "addprinc -randkey ${principal}" >/dev/null
  fi
}

write_keytab() {
  local principal="$1"
  local target_path="$2"
  local temp_keytab

  temp_keytab="$(mktemp)"
  KRB5_CONFIG="${KRB5_CONFIG_FILE}" \
    kadmin -p "${CUSTOMERDNA_KRB5_ADMIN_PRINCIPAL}" -w "${CUSTOMERDNA_KRB5_ADMIN_PASSWORD}" \
    -q "ktadd -k ${temp_keytab} -norandkey ${principal}" >/dev/null

  sudo mkdir -p "$(dirname "${target_path}")"
  sudo install -m 0644 "${temp_keytab}" "${target_path}"
  rm -f "${temp_keytab}"
}

provision_principal_keytab() {
  local principal="$1"
  local target_path="$2"
  echo "[INFO] Provisioning ${principal} -> ${target_path}"
  ensure_principal "${principal}"
  write_keytab "${principal}" "${target_path}"
}

require_command docker "Docker is not installed."
if ! docker compose version >/dev/null 2>&1; then
  echo "[ERROR] Docker Compose plugin is not available."
  exit 1
fi

if [[ ! -f "${SCRIPT_DIR}/.env" ]]; then
  echo "[ERROR] Missing ${SCRIPT_DIR}/.env"
  exit 1
fi

set -a
source "${SCRIPT_DIR}/.env"
set +a

if [[ "${CUSTOMERDNA_SECURE_STORAGE_ENABLED:-true}" == "true" ]] && ! mountpoint -q "${CUSTOMERDNA_SECURE_STORAGE_ROOT:-/mnt/customerdna_secure}"; then
  echo "[ERROR] Encrypted storage is enabled but not mounted at ${CUSTOMERDNA_SECURE_STORAGE_ROOT:-/mnt/customerdna_secure}"
  echo "        Run: sudo bash ${SCRIPT_DIR}/setup_encrypted_storage_vm1.sh"
  exit 1
fi

if [[ "${CUSTOMERDNA_HADOOP_SECURE_MODE:-false}" == "true" ]]; then
  require_command python3 "python3 is required to wait for Kerberos services."
  require_command kadmin "Kerberos client tools are required. Run: sudo bash prepare_fresh_vm1.sh"
fi

KRB5_CONFIG_FILE="${SCRIPT_DIR}/kerberos/krb5.conf"

for runtime_dir in \
  "${CUSTOMERDNA_RUNTIME_KAFKA_DATA_DIR:-${SCRIPT_DIR}/runtime/kafka/data}" \
  "${CUSTOMERDNA_RUNTIME_HDFS_DATANODE_DIR:-${SCRIPT_DIR}/runtime/hdfs/datanode}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_EVENTS_DIR:-${SCRIPT_DIR}/runtime/spark/events}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_IVY2_DIR:-${SCRIPT_DIR}/runtime/spark/ivy2}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_IVY2_DIR:-${SCRIPT_DIR}/runtime/spark/ivy2}/cache" \
  "${CUSTOMERDNA_RUNTIME_SPARK_IVY2_DIR:-${SCRIPT_DIR}/runtime/spark/ivy2}/jars" \
  "${CUSTOMERDNA_RUNTIME_TRINO_DATA_DIR:-${SCRIPT_DIR}/runtime/trino/data}" \
  "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/datanode-1" \
  "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/spark" \
  "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/trino"; do
  ensure_runtime_directory_access "${runtime_dir}"
done

if [[ "${CUSTOMERDNA_HADOOP_SECURE_MODE:-false}" == "true" ]]; then
  echo "[1/5] Waiting for Kerberos services on VM2"
  wait_for_tcp "${CUSTOMERDNA_KRB5_KDC_HOST}" "${CUSTOMERDNA_KRB5_KDC_PORT:-88}" "Kerberos KDC"
  wait_for_tcp "${CUSTOMERDNA_KRB5_KDC_HOST}" "${CUSTOMERDNA_KRB5_ADMIN_SERVER_PORT:-749}" "Kerberos admin server"
  wait_for_remote_kadmin 120

  echo "[2/5] Provisioning Kerberos principals and keytabs"
  provision_principal_keytab "dn/datanode-1@${CUSTOMERDNA_KRB5_REALM}" \
    "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/datanode-1/dn.service.keytab"
  provision_principal_keytab "spark@${CUSTOMERDNA_KRB5_REALM}" \
    "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/spark/spark.service.keytab"
  provision_principal_keytab "trino@${CUSTOMERDNA_KRB5_REALM}" \
    "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/trino/trino.service.keytab"
else
  echo "[1/5] Kerberos secure mode disabled; skipping remote KDC wait"
  echo "[2/5] Kerberos secure mode disabled; skipping keytab provisioning"
fi

echo "[3/5] Building shared Spark image"
docker compose --env-file "${SCRIPT_DIR}/.env" build spark-worker-1

echo "[4/5] Building and starting VM1 services"
docker compose --env-file "${SCRIPT_DIR}/.env" up -d --build

echo "[5/5] Listing running services"
docker compose --env-file "${SCRIPT_DIR}/.env" ps

echo
echo "Access points"
echo "------------------------------------------------------------"
echo "Kafka broker 1    : ${VM1_HOST_IP:-10.10.252.11}:9092"
echo "HDFS DataNode web : http://${VM1_HOST_IP:-10.10.252.11}:9864"
echo "Spark worker UI   : http://${VM1_HOST_IP:-10.10.252.11}:8087"
echo "Trino worker      : http://${VM1_HOST_IP:-10.10.252.11}:8080"
echo "cAdvisor          : http://${VM1_HOST_IP:-10.10.252.11}:8081"
