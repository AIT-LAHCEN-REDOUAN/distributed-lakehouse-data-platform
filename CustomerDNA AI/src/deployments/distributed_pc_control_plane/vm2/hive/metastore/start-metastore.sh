#!/usr/bin/env bash

set -euo pipefail

: "${DB_DRIVER:=postgres}"

# Load the custom Hive/Hadoop configuration before any schema checks so
# schematool inspects the PostgreSQL metastore instead of falling back to Derby.
export HIVE_CONF_DIR=/opt/hive/conf

if [ -d /hive_custom_conf ]; then
  find /hive_custom_conf -type f -exec ln -sfn '{}' /opt/hive/conf/ ';'
fi

export HADOOP_CONF_DIR=/opt/hive/conf
export TEZ_CONF_DIR=/opt/hive/conf
export HADOOP_CLIENT_OPTS="${HADOOP_CLIENT_OPTS:-} ${SERVICE_OPTS:-}"

if /opt/hive/bin/schematool -dbType "${DB_DRIVER}" -info >/tmp/customerdna_metastore_info.log 2>&1; then
  export IS_RESUME=true
  echo "[INFO] Existing Hive metastore schema detected. Starting in resume mode."
else
  export IS_RESUME=false
  echo "[INFO] Hive metastore schema not detected yet. Running initialization before startup."
  cat /tmp/customerdna_metastore_info.log
fi

exec /entrypoint.sh "$@"
