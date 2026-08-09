#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "${SCRIPT_DIR}"

echo "============================================================"
echo " CustomerDNA VM2 - Start Data Plane Leader"
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

wait_for_kadmin() {
  local timeout_seconds="${1:-120}"
  local start_epoch
  start_epoch="$(date +%s)"

  while true; do
    if docker exec kerberos-kdc kadmin.local -q "listprincs" >/dev/null 2>&1; then
      return 0
    fi

    if (( "$(date +%s)" - start_epoch >= timeout_seconds )); then
      echo "[ERROR] Kerberos admin interface did not become ready within ${timeout_seconds}s."
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
  echo "        Run: sudo bash ${SCRIPT_DIR}/setup_encrypted_storage_vm2.sh"
  exit 1
fi

if [[ "${CUSTOMERDNA_HADOOP_SECURE_MODE:-false}" == "true" ]]; then
  require_command python3 "python3 is required to wait for Kerberos services."
  require_command kadmin "Kerberos client tools are required. Run: sudo bash prepare_fresh_vm2.sh"
fi

KRB5_CONFIG_FILE="${SCRIPT_DIR}/kerberos/krb5.conf"

mkdir -p \
  "${CUSTOMERDNA_RUNTIME_KAFKA_DATA_DIR:-${SCRIPT_DIR}/runtime/kafka/data}" \
  "${CUSTOMERDNA_RUNTIME_HDFS_NAMENODE_DIR:-${SCRIPT_DIR}/runtime/hdfs/namenode}" \
  "${CUSTOMERDNA_RUNTIME_HDFS_DATANODE_DIR:-${SCRIPT_DIR}/runtime/hdfs/datanode}" \
  "${CUSTOMERDNA_RUNTIME_HIVE_POSTGRES_DIR:-${SCRIPT_DIR}/runtime/hive/postgres}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_EVENTS_DIR:-${SCRIPT_DIR}/runtime/spark/events}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_IVY2_DIR:-${SCRIPT_DIR}/runtime/spark/ivy2}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_IVY2_DIR:-${SCRIPT_DIR}/runtime/spark/ivy2}/cache" \
  "${CUSTOMERDNA_RUNTIME_SPARK_IVY2_DIR:-${SCRIPT_DIR}/runtime/spark/ivy2}/jars" \
  "${CUSTOMERDNA_RUNTIME_SPARK_LOGS_DIR:-${SCRIPT_DIR}/runtime/spark/logs}" \
  "${CUSTOMERDNA_RUNTIME_TRINO_DATA_DIR:-${SCRIPT_DIR}/runtime/trino/data}" \
  "${CUSTOMERDNA_RUNTIME_TRINO_CADDY_DATA_DIR:-${SCRIPT_DIR}/runtime/trino/caddy/data}" \
  "${CUSTOMERDNA_RUNTIME_TRINO_CADDY_CONFIG_DIR:-${SCRIPT_DIR}/runtime/trino/caddy/config}" \
  "${CUSTOMERDNA_RUNTIME_TRINO_AUDIT_LOG_DIR:-${SCRIPT_DIR}/runtime/trino/audit_logs}" \
  "${CUSTOMERDNA_RUNTIME_KERBEROS_KDC_DB_DIR:-${SCRIPT_DIR}/runtime/kerberos/kdc_db}" \
  "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/namenode" \
  "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/datanode-2" \
  "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/hive" \
  "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/spark" \
  "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/trino" \
  "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/airflow" \
  "${CUSTOMERDNA_RUNTIME_HDFS_ADMIN_STAGING_DIR:-${SCRIPT_DIR}/runtime/hdfs/admin_staging}"

chmod -R 777 \
  "${CUSTOMERDNA_RUNTIME_KAFKA_DATA_DIR:-${SCRIPT_DIR}/runtime/kafka/data}" \
  "${CUSTOMERDNA_RUNTIME_HDFS_NAMENODE_DIR:-${SCRIPT_DIR}/runtime/hdfs/namenode}" \
  "${CUSTOMERDNA_RUNTIME_HDFS_DATANODE_DIR:-${SCRIPT_DIR}/runtime/hdfs/datanode}" \
  "${CUSTOMERDNA_RUNTIME_HIVE_POSTGRES_DIR:-${SCRIPT_DIR}/runtime/hive/postgres}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_EVENTS_DIR:-${SCRIPT_DIR}/runtime/spark/events}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_IVY2_DIR:-${SCRIPT_DIR}/runtime/spark/ivy2}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_LOGS_DIR:-${SCRIPT_DIR}/runtime/spark/logs}" \
  "${CUSTOMERDNA_RUNTIME_TRINO_DATA_DIR:-${SCRIPT_DIR}/runtime/trino/data}" \
  "${CUSTOMERDNA_RUNTIME_TRINO_CADDY_DATA_DIR:-${SCRIPT_DIR}/runtime/trino/caddy/data}" \
  "${CUSTOMERDNA_RUNTIME_TRINO_CADDY_CONFIG_DIR:-${SCRIPT_DIR}/runtime/trino/caddy/config}" \
  "${CUSTOMERDNA_RUNTIME_TRINO_AUDIT_LOG_DIR:-${SCRIPT_DIR}/runtime/trino/audit_logs}" \
  "${CUSTOMERDNA_RUNTIME_HDFS_ADMIN_STAGING_DIR:-${SCRIPT_DIR}/runtime/hdfs/admin_staging}"

echo "[1/6] Starting Kerberos KDC"
docker compose --env-file "${SCRIPT_DIR}/.env" up -d --build kerberos-kdc

echo "[2/6] Waiting for Kerberos services"
wait_for_tcp "127.0.0.1" "${CUSTOMERDNA_KRB5_KDC_PORT:-88}" "Kerberos KDC"
wait_for_tcp "127.0.0.1" "${CUSTOMERDNA_KRB5_ADMIN_SERVER_PORT:-749}" "Kerberos admin server"
wait_for_kadmin 120

if [[ "${CUSTOMERDNA_HADOOP_SECURE_MODE:-false}" == "true" ]]; then
  echo "[3/6] Provisioning Kerberos principals and keytabs"
  provision_principal_keytab "nn/namenode@${CUSTOMERDNA_KRB5_REALM}" \
    "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/namenode/nn.service.keytab"
  provision_principal_keytab "dn/datanode-2@${CUSTOMERDNA_KRB5_REALM}" \
    "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/datanode-2/dn.service.keytab"
  provision_principal_keytab "hive/hive-metastore@${CUSTOMERDNA_KRB5_REALM}" \
    "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/hive/hive.service.keytab"
  provision_principal_keytab "spark@${CUSTOMERDNA_KRB5_REALM}" \
    "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/spark/spark.service.keytab"
  provision_principal_keytab "trino@${CUSTOMERDNA_KRB5_REALM}" \
    "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/trino/trino.service.keytab"
  provision_principal_keytab "airflow@${CUSTOMERDNA_KRB5_REALM}" \
    "${CUSTOMERDNA_RUNTIME_KERBEROS_KEYTAB_DIR:-${SCRIPT_DIR}/runtime/kerberos/keytabs}/airflow/airflow.service.keytab"
else
  echo "[3/6] Kerberos secure mode disabled; skipping keytab provisioning"
fi

echo "[4/6] Building shared Spark image"
docker compose --env-file "${SCRIPT_DIR}/.env" build spark-master

echo "[5/6] Building and starting VM2 services"
docker compose --env-file "${SCRIPT_DIR}/.env" up -d --build \
  broker-2 \
  namenode \
  datanode-2 \
  hdfs-admin-client \
  hive-metastore-db \
  hive-metastore \
  spark-master \
  spark-submit-client \
  spark-worker-2 \
  spark-history-server \
  spark-thrift-server \
  trino-coordinator \
  trino-gateway \
  cadvisor

echo "[6/6] Listing running services"
docker compose --env-file "${SCRIPT_DIR}/.env" ps

echo
echo "Access points"
echo "------------------------------------------------------------"
echo "Kerberos KDC      : ${VM2_HOST_IP:-10.10.252.12}:${CUSTOMERDNA_KRB5_KDC_PORT:-88}"
echo "Kerberos admin    : ${VM2_HOST_IP:-10.10.252.12}:${CUSTOMERDNA_KRB5_ADMIN_SERVER_PORT:-749}"
echo "Kafka broker 2    : ${VM2_HOST_IP:-10.10.252.12}:9092"
echo "HDFS NameNode RPC : ${VM2_HOST_IP:-10.10.252.12}:9000"
echo "HDFS NameNode web : http://${VM2_HOST_IP:-10.10.252.12}:9870"
echo "Hive Metastore    : ${VM2_HOST_IP:-10.10.252.12}:9083"
echo "Hive Metastore DB : ${VM2_HOST_IP:-10.10.252.12}:5435"
echo "Spark master      : spark://${VM2_HOST_IP:-10.10.252.12}:7077"
echo "Spark master UI   : http://${VM2_HOST_IP:-10.10.252.12}:8086"
echo "Spark History UI  : http://${VM2_HOST_IP:-10.10.252.12}:18080"
echo "Spark submit host : ssh ${USER:-redouan}@${VM2_HOST_IP:-10.10.252.12}"
echo "Spark Thrift      : ${VM2_HOST_IP:-10.10.252.12}:10000"
echo "Trino gateway HTTP: http://${VM2_HOST_IP:-10.10.252.12}:8088"
echo "Trino gateway TLS : https://${VM2_HOST_IP:-10.10.252.12}:${CUSTOMERDNA_TRINO_TLS_PORT:-8443}"
echo "cAdvisor          : http://${VM2_HOST_IP:-10.10.252.12}:8081"
