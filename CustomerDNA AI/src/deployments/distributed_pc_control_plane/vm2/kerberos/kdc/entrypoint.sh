#!/usr/bin/env bash

set -euo pipefail

: "${KRB5_REALM:=CUSTOMERDNA.LOCAL}"
: "${KRB5_KDC_HOST:=10.10.252.12}"
: "${KRB5_ADMIN_PRINCIPAL:=admin/admin@CUSTOMERDNA.LOCAL}"
: "${KRB5_ADMIN_PASSWORD:=CustomerDNA_Krb_Admin_2026!}"
: "${KRB5_MASTER_PASSWORD:=CustomerDNA_Krb_Master_2026!}"

mkdir -p /var/lib/krb5kdc /run/krb5kdc

if [[ ! -f /var/lib/krb5kdc/principal ]]; then
  echo "[INFO] Initializing Kerberos database for realm ${KRB5_REALM}"
  kdb5_util create -s -P "${KRB5_MASTER_PASSWORD}"
  kadmin.local -q "addprinc -pw ${KRB5_ADMIN_PASSWORD} ${KRB5_ADMIN_PRINCIPAL}"
else
  echo "[INFO] Reusing existing Kerberos database for realm ${KRB5_REALM}"
fi

echo "[INFO] Starting krb5kdc and kadmind"
/usr/sbin/krb5kdc -n &
exec /usr/sbin/kadmind -nofork
