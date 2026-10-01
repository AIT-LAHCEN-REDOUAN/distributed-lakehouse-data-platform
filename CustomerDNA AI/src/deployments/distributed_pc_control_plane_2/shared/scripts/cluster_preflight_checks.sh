#!/usr/bin/env bash

set -euo pipefail

LABEL="${LABEL:-CustomerDNA Distributed Cluster}"
VM1_IP="${VM1_IP:-10.10.252.11}"
VM2_IP="${VM2_IP:-10.10.252.12}"
VM3_IP="${VM3_IP:-10.10.252.13}"

check_tcp() {
  local host="$1"
  local port="$2"
  local label="$3"

  if timeout 5 bash -lc "</dev/tcp/${host}/${port}" >/dev/null 2>&1; then
    echo "[OK] ${label} -> ${host}:${port}"
  else
    echo "[WARN] ${label} -> ${host}:${port} not reachable"
  fi
}

echo "============================================================"
echo " ${LABEL} - Shared Preflight Checks"
echo "============================================================"

check_tcp "${VM1_IP}" 9092 "Kafka broker on VM1"
check_tcp "${VM2_IP}" 9092 "Kafka broker on VM2"
check_tcp "${VM3_IP}" 9092 "Kafka broker on VM3"

check_tcp "${VM2_IP}" 9000 "HDFS NameNode RPC on VM2"
check_tcp "${VM2_IP}" 9870 "HDFS NameNode web on VM2"
check_tcp "${VM2_IP}" 9083 "Hive Metastore on VM2"
check_tcp "${VM2_IP}" 5435 "Hive Metastore PostgreSQL on VM2"

check_tcp "${VM2_IP}" 7077 "Spark master on VM2"
check_tcp "${VM2_IP}" 8086 "Spark master UI on VM2"
check_tcp "${VM2_IP}" 10000 "Spark Thrift on VM2"
check_tcp "${VM2_IP}" 4040 "Spark Thrift UI on VM2"

check_tcp "${VM2_IP}" 8088 "Trino coordinator on VM2"

check_tcp "${VM1_IP}" 8081 "cAdvisor on VM1"
check_tcp "${VM2_IP}" 8081 "cAdvisor on VM2"
check_tcp "${VM3_IP}" 8081 "cAdvisor on VM3"
