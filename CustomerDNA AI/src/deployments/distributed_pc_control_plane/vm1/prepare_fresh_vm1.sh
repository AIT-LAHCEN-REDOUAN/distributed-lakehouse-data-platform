#!/usr/bin/env bash

set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo: sudo bash prepare_fresh_vm1.sh"
  exit 1
fi

TARGET_USER="${SUDO_USER:-${USER}}"
ENABLE_UFW="${ENABLE_UFW:-false}"

echo "============================================================"
echo " CustomerDNA VM1 - Fresh Ubuntu Preparation"
echo "============================================================"
echo "Target user          : ${TARGET_USER}"
echo "Enable UFW           : ${ENABLE_UFW}"
echo "Host                 : $(hostname)"
echo "OS                   : $(. /etc/os-release && echo "${PRETTY_NAME}")"
echo "============================================================"

echo "[1/7] Updating APT metadata and installing base packages"
apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release git ufw cryptsetup krb5-user

echo "[2/7] Removing conflicting container packages if present"
for pkg in docker.io docker-compose docker-compose-v2 docker-doc docker-buildx podman-docker containerd runc; do
  apt-get remove -y "${pkg}" >/dev/null 2>&1 || true
done

echo "[3/7] Installing Docker repository key and source"
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

cat >/etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

echo "[4/7] Installing Docker Engine and Compose plugin"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "[5/7] Enabling Docker service"
systemctl enable docker
systemctl restart docker

if id "${TARGET_USER}" >/dev/null 2>&1; then
  echo "[6/7] Adding ${TARGET_USER} to docker group"
  usermod -aG docker "${TARGET_USER}" || true
else
  echo "[WARN] User ${TARGET_USER} does not exist; skipping docker group update"
fi

echo "[7/7] Optional firewall configuration"
if [[ "${ENABLE_UFW}" == "true" ]]; then
  ufw allow 22/tcp
  ufw allow 9092/tcp
  ufw allow 9093/tcp
  ufw allow 29092/tcp
  ufw allow 9865/tcp
  ufw allow 8087/tcp
  ufw allow 8080/tcp
  ufw allow 8081/tcp
  ufw --force enable
  ufw status verbose
else
  echo "[INFO] Skipping UFW enable. To enable later, run:"
  echo "       sudo ENABLE_UFW=true bash prepare_fresh_vm1.sh"
fi

echo
echo "Verification"
echo "------------------------------------------------------------"
docker --version
docker compose version
systemctl --no-pager --full status docker | sed -n '1,10p'

echo
echo "Preparation complete."
echo "Next:"
echo "  1. Log out and log back in so '${TARGET_USER}' picks up docker-group membership."
echo "  2. Upload the prepared VM1 bundle and extract it on VM1."
echo "  3. Run ./vm1_preflight_checks.sh from the extracted VM1 folder."
echo "  4. Run ./start_vm1_stack.sh to start the VM1 distributed worker node."
