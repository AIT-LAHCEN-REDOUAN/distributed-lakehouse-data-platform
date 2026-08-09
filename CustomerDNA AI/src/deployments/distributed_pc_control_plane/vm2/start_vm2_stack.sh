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

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] Docker is not installed."
  exit 1
fi

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
  "${CUSTOMERDNA_RUNTIME_TRINO_AUDIT_LOG_DIR:-${SCRIPT_DIR}/runtime/trino/audit_logs}"

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
  "${CUSTOMERDNA_RUNTIME_TRINO_AUDIT_LOG_DIR:-${SCRIPT_DIR}/runtime/trino/audit_logs}"

echo "[1/4] Building shared Spark image"
docker compose --env-file "${SCRIPT_DIR}/.env" build spark-master

echo "[2/4] Building and starting VM2 services"
docker compose --env-file "${SCRIPT_DIR}/.env" up -d --build

echo "[3/4] Listing running services"
docker compose --env-file "${SCRIPT_DIR}/.env" ps

echo "[4/4] Access points"
echo "Kafka broker 2     : ${VM2_HOST_IP:-10.10.252.12}:9092"
echo "HDFS NameNode RPC  : ${VM2_HOST_IP:-10.10.252.12}:9000"
echo "HDFS NameNode web  : http://${VM2_HOST_IP:-10.10.252.12}:9870"
echo "Hive Metastore     : ${VM2_HOST_IP:-10.10.252.12}:9083"
echo "Hive Metastore DB  : ${VM2_HOST_IP:-10.10.252.12}:5435"
echo "Spark master       : spark://${VM2_HOST_IP:-10.10.252.12}:7077"
echo "Spark master UI    : http://${VM2_HOST_IP:-10.10.252.12}:8086"
echo "Spark History UI   : http://${VM2_HOST_IP:-10.10.252.12}:18080"
echo "Spark submit host  : ssh ${USER:-redouan}@${VM2_HOST_IP:-10.10.252.12}"
echo "Spark Thrift       : ${VM2_HOST_IP:-10.10.252.12}:10000"
echo "Trino gateway HTTP : http://${VM2_HOST_IP:-10.10.252.12}:8088"
echo "Trino gateway TLS  : https://${VM2_HOST_IP:-10.10.252.12}:${CUSTOMERDNA_TRINO_TLS_PORT:-8443}"
echo "cAdvisor           : http://${VM2_HOST_IP:-10.10.252.12}:8081"
