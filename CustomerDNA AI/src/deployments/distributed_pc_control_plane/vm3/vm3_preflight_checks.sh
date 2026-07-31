#!/usr/bin/env bash

set -euo pipefail

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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================================"
echo " CustomerDNA VM3 - Preflight Checks"
echo "============================================================"

echo "[Local tools]"
command -v git >/dev/null 2>&1 && echo "[OK] git" || echo "[WARN] git missing"
command -v docker >/dev/null 2>&1 && echo "[OK] docker" || echo "[WARN] docker missing"
docker compose version >/dev/null 2>&1 && echo "[OK] docker compose" || echo "[WARN] docker compose missing"

echo
echo "[Bundle files]"
[[ -f "${SCRIPT_DIR}/docker-compose.yml" ]] && echo "[OK] docker-compose.yml" || echo "[WARN] docker-compose.yml missing"
[[ -f "${SCRIPT_DIR}/.env" ]] && echo "[OK] .env" || echo "[WARN] .env missing"
[[ -f "${SCRIPT_DIR}/prepare_fresh_vm3.sh" ]] && echo "[OK] prepare_fresh_vm3.sh" || echo "[WARN] prepare_fresh_vm3.sh missing"
[[ -f "${SCRIPT_DIR}/start_vm3_stack.sh" ]] && echo "[OK] start_vm3_stack.sh" || echo "[WARN] start_vm3_stack.sh missing"

echo
echo "[Peer endpoints]"
check_tcp 10.10.252.11 22 "VM1 SSH"
check_tcp 10.10.252.12 22 "VM2 SSH"
check_tcp 10.10.252.11 9093 "Kafka controller peer on VM1"
check_tcp 10.10.252.12 9093 "Kafka controller peer on VM2"
check_tcp 10.10.252.12 9000 "HDFS NameNode RPC on VM2"
check_tcp 10.10.252.12 9870 "HDFS NameNode web on VM2"
check_tcp 10.10.252.12 7077 "Spark master on VM2"
check_tcp 10.10.252.12 8088 "Trino coordinator on VM2"

echo
echo "[Local host ports before startup]"
for port in 9092 9093 29092 9864 8087 8080 8081; do
  if ss -ltn "( sport = :${port} )" | grep -q ":${port}"; then
    echo "[WARN] Port ${port} already in use on this VM"
  else
    echo "[OK] Port ${port} free"
  fi
done
