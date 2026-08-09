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
  echo "        Run: sudo bash ${SCRIPT_DIR}/setup_encrypted_storage_vm1.sh"
  exit 1
fi

mkdir -p \
  "${CUSTOMERDNA_RUNTIME_KAFKA_DATA_DIR:-${SCRIPT_DIR}/runtime/kafka/data}" \
  "${CUSTOMERDNA_RUNTIME_HDFS_DATANODE_DIR:-${SCRIPT_DIR}/runtime/hdfs/datanode}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_EVENTS_DIR:-${SCRIPT_DIR}/runtime/spark/events}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_IVY2_DIR:-${SCRIPT_DIR}/runtime/spark/ivy2}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_IVY2_DIR:-${SCRIPT_DIR}/runtime/spark/ivy2}/cache" \
  "${CUSTOMERDNA_RUNTIME_SPARK_IVY2_DIR:-${SCRIPT_DIR}/runtime/spark/ivy2}/jars" \
  "${CUSTOMERDNA_RUNTIME_TRINO_DATA_DIR:-${SCRIPT_DIR}/runtime/trino/data}"

chmod -R 777 \
  "${CUSTOMERDNA_RUNTIME_KAFKA_DATA_DIR:-${SCRIPT_DIR}/runtime/kafka/data}" \
  "${CUSTOMERDNA_RUNTIME_HDFS_DATANODE_DIR:-${SCRIPT_DIR}/runtime/hdfs/datanode}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_EVENTS_DIR:-${SCRIPT_DIR}/runtime/spark/events}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_IVY2_DIR:-${SCRIPT_DIR}/runtime/spark/ivy2}" \
  "${CUSTOMERDNA_RUNTIME_TRINO_DATA_DIR:-${SCRIPT_DIR}/runtime/trino/data}"

echo "[1/4] Building shared Spark image"
docker compose --env-file "${SCRIPT_DIR}/.env" build spark-worker-1

echo "[2/4] Building and starting VM1 services"
docker compose --env-file "${SCRIPT_DIR}/.env" up -d --build

echo "[3/4] Listing running services"
docker compose --env-file "${SCRIPT_DIR}/.env" ps

echo "[4/4] Access points"
echo "Kafka broker 1     : ${VM1_HOST_IP:-10.10.252.11}:9092"
echo "HDFS DataNode web  : http://${VM1_HOST_IP:-10.10.252.11}:9864"
echo "Spark worker UI    : http://${VM1_HOST_IP:-10.10.252.11}:8087"
echo "Trino worker       : http://${VM1_HOST_IP:-10.10.252.11}:8080"
echo "cAdvisor           : http://${VM1_HOST_IP:-10.10.252.11}:8081"
