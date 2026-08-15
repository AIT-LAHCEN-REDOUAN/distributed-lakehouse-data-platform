#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "${SCRIPT_DIR}"

echo "============================================================"
echo " CustomerDNA VM2 - Reset Local Node State"
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

echo "[1/5] Stopping and removing VM2 compose services"
docker compose --env-file "${SCRIPT_DIR}/.env" down --remove-orphans --volumes || true

echo "[2/5] Removing VM2 runtime data"
rm -rf "${SCRIPT_DIR}/runtime"
mkdir -p "${SCRIPT_DIR}/runtime"

echo "[3/5] Pruning Docker resources"
docker system prune -a -f --volumes || true
docker builder prune -a -f || true

echo "[4/5] Cleaning package and journal caches"
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get clean || true
fi
if command -v journalctl >/dev/null 2>&1; then
  sudo journalctl --vacuum-time=2d || true
fi

echo "[5/5] Disk summary"
df -h
docker system df || true

echo
echo "VM2 reset complete."
echo "Next:"
echo "  1. Remove or replace the extracted VM2 folder if you want a full re-upload test."
echo "  2. Run the local bundle manager from your PC again."
echo "  3. Extract the fresh bundle and start from preflight."
