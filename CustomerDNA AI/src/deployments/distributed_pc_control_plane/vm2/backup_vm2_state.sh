#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${SCRIPT_DIR}/runtime/backups/vm2/${TIMESTAMP}"

mkdir -p "${BACKUP_DIR}"

set -a
source "${SCRIPT_DIR}/.env"
set +a

echo "============================================================"
echo " CustomerDNA VM2 - Backup State"
echo "============================================================"
echo "Target directory: ${BACKUP_DIR}"

cp "${SCRIPT_DIR}/.env" "${BACKUP_DIR}/.env"
cp "${SCRIPT_DIR}/docker-compose.yml" "${BACKUP_DIR}/docker-compose.yml"
cp -R "${SCRIPT_DIR}/trino" "${BACKUP_DIR}/trino"
cp -R "${SCRIPT_DIR}/hive" "${BACKUP_DIR}/hive"
cp -R "${SCRIPT_DIR}/spark/config" "${BACKUP_DIR}/spark-config"

docker exec hive-metastore-db pg_dump \
  -h 127.0.0.1 \
  -p "${HIVE_METASTORE_POSTGRES_PORT}" \
  -U "${HIVE_METASTORE_USER}" \
  "${HIVE_METASTORE_DB}" > "${BACKUP_DIR}/hive_metastore_postgres.sql"

echo "[OK] Backup completed."
echo "Hive metastore dump: ${BACKUP_DIR}/hive_metastore_postgres.sql"
