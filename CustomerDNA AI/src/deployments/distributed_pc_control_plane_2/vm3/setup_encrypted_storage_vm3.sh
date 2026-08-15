#!/usr/bin/env bash

set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo: sudo bash setup_encrypted_storage_vm3.sh"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[ERROR] Missing ${ENV_FILE}"
  exit 1
fi

set -a
source "${ENV_FILE}"
set +a

if [[ "${CUSTOMERDNA_SECURE_STORAGE_ENABLED:-true}" != "true" ]]; then
  echo "[INFO] Secure storage is disabled in .env. Nothing to do."
  exit 0
fi

if ! command -v cryptsetup >/dev/null 2>&1; then
  echo "[ERROR] cryptsetup is not installed. Run sudo bash prepare_fresh_vm3.sh first."
  exit 1
fi

SECURE_ROOT="${CUSTOMERDNA_SECURE_STORAGE_ROOT:-/mnt/customerdna_secure}"
IMAGE_PATH="${CUSTOMERDNA_SECURE_STORAGE_IMAGE_PATH:-/var/lib/customerdna-secure/customerdna-vm3.img}"
MAPPER_NAME="${CUSTOMERDNA_SECURE_STORAGE_MAPPER_NAME:-customerdna_vm3_secure}"
SIZE_GB="${CUSTOMERDNA_SECURE_STORAGE_SIZE_GB:-6}"
PASSPHRASE="${CUSTOMERDNA_SECURE_STORAGE_PASSPHRASE:-}"

if [[ -z "${PASSPHRASE}" ]]; then
  echo "[ERROR] CUSTOMERDNA_SECURE_STORAGE_PASSPHRASE is empty."
  exit 1
fi

echo "============================================================"
echo " CustomerDNA VM3 - Setup Encrypted Runtime Storage"
echo "============================================================"
echo "Secure root : ${SECURE_ROOT}"
echo "Image path  : ${IMAGE_PATH}"
echo "Mapper name : ${MAPPER_NAME}"
echo "Size (GB)   : ${SIZE_GB}"
echo "============================================================"

mkdir -p "$(dirname "${IMAGE_PATH}")" "${SECURE_ROOT}"
chmod 700 "$(dirname "${IMAGE_PATH}")"

if [[ ! -f "${IMAGE_PATH}" ]]; then
  echo "[1/5] Creating sparse encrypted storage image"
  truncate -s "${SIZE_GB}G" "${IMAGE_PATH}"
  chmod 600 "${IMAGE_PATH}"
else
  echo "[1/5] Reusing existing encrypted storage image"
fi

if ! cryptsetup isLuks "${IMAGE_PATH}" >/dev/null 2>&1; then
  echo "[2/5] Formatting LUKS container"
  printf '%s' "${PASSPHRASE}" | cryptsetup luksFormat "${IMAGE_PATH}" --batch-mode --type luks2 --key-file -
else
  echo "[2/5] LUKS header already present"
fi

if ! cryptsetup status "${MAPPER_NAME}" >/dev/null 2>&1; then
  echo "[3/5] Opening encrypted mapper"
  printf '%s' "${PASSPHRASE}" | cryptsetup open "${IMAGE_PATH}" "${MAPPER_NAME}" --key-file -
else
  echo "[3/5] Encrypted mapper already open"
fi

if ! blkid "/dev/mapper/${MAPPER_NAME}" >/dev/null 2>&1; then
  echo "[4/5] Creating ext4 filesystem"
  mkfs.ext4 -F "/dev/mapper/${MAPPER_NAME}"
else
  echo "[4/5] Filesystem already exists"
fi

if ! mountpoint -q "${SECURE_ROOT}"; then
  echo "[5/5] Mounting encrypted filesystem"
  mount "/dev/mapper/${MAPPER_NAME}" "${SECURE_ROOT}"
else
  echo "[5/5] Encrypted filesystem already mounted"
fi

mkdir -p \
  "${CUSTOMERDNA_RUNTIME_KAFKA_DATA_DIR:-${SECURE_ROOT}/kafka/data}" \
  "${CUSTOMERDNA_RUNTIME_HDFS_DATANODE_DIR:-${SECURE_ROOT}/hdfs/datanode}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_EVENTS_DIR:-${SECURE_ROOT}/spark/events}" \
  "${CUSTOMERDNA_RUNTIME_SPARK_IVY2_DIR:-${SECURE_ROOT}/spark/ivy2}" \
  "${CUSTOMERDNA_RUNTIME_TRINO_DATA_DIR:-${SECURE_ROOT}/trino/data}"

chmod -R 777 "${SECURE_ROOT}"

echo
echo "Encrypted runtime storage is ready for VM3."
