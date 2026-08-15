#!/usr/bin/env bash

set -euo pipefail

: "${DB_DRIVER:=postgres}"

if /opt/hive/bin/schematool -dbType "${DB_DRIVER}" -info >/tmp/customerdna_metastore_info.log 2>&1; then
  export IS_RESUME=true
  echo "[INFO] Existing Hive metastore schema detected. Starting in resume mode."
else
  export IS_RESUME=false
  echo "[INFO] Hive metastore schema not detected yet. Running initialization before startup."
  cat /tmp/customerdna_metastore_info.log
fi

exec /entrypoint.sh "$@"
