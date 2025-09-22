#!/usr/bin/env zsh
# pack.zsh — Portable, closed MongoDB stack (Vagrant VM + Docker)
# Stack version
typeset -r STACK_VERSION="1.0.1"

# Safety flags for zsh
set -e
set -u
(set -o pipefail 2>/dev/null) || setopt pipefail

# ---- Config ----
PROJECT="gmunden-mongo-stack"
VM_NAME="gmunden-mongo"
UBUNTU_BOX="ubuntu/jammy64"
MONGO_IMAGE="mongo:7.0"
MONGO_USER="admin"
MONGO_PASS="change_me_strong"
MONGO_DB="appdb"
HOST_BIND_IP="127.0.0.1"
HOST_BIND_PORT="27017"
VM_RAM=2048
VM_CPUS=2

# ---- Helpers ----
die() { print -r -- "ERROR: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1; }

install_vagrant() {
  print "Vagrant not found. Installing…"
  if [[ "$OSTYPE" == "darwin"* ]]; then
    if need brew; then
      HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_ENV_HINTS=1 brew install --cask vagrant || die "brew failed"
    else
      die "Homebrew missing. Install Homebrew or Vagrant manually."
    fi
  elif [[ -f /etc/debian_version ]]; then
    sudo apt-get update -y
    sudo apt-get install -y vagrant
  elif [[ -f /etc/redhat-release ]]; then
    sudo yum install -y vagrant
  else
    die "Unsupported OS for automatic Vagrant install."
  fi
}

install_virtualbox() {
  print "VirtualBox not found. Installing…"
  if [[ "$OSTYPE" == "darwin"* ]]; then
    HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_ENV_HINTS=1 brew install --cask virtualbox || die "brew failed"
  elif [[ -f /etc/debian_version ]]; then
    sudo apt-get update -y && sudo apt-get install -y virtualbox
  elif [[ -f /etc/redhat-release ]]; then
    sudo yum install -y VirtualBox
  else
    die "Unsupported OS for automatic VirtualBox install."
  fi
}

# call only if necessary
need vagrant || install_vagrant
command -v VBoxManage >/dev/null 2>&1 || install_virtualbox


# ---- Dependency check ----
if ! need vagrant; then
  install_vagrant
fi
need vagrant || die "Vagrant installation failed."
need awk || die "Missing awk"
need sed || die "Missing sed"
need printf || die "Missing printf"

# ---- Project ----
mkdir -p -- "$PROJECT" || die "cannot create $PROJECT"
cd "$PROJECT"

# ---- Vagrantfile ----
cat > Vagrantfile <<'VFILE'
Vagrant.configure("2") do |config|
  config.vm.box = ENV.fetch("UBUNTU_BOX", "ubuntu/jammy64")
  config.vm.hostname = ENV.fetch("VM_NAME", "gmunden-mongo")
  config.vm.network "forwarded_port",
    guest: 27017,
    host: ENV.fetch("HOST_BIND_PORT","27017"),
    host_ip: ENV.fetch("HOST_BIND_IP","127.0.0.1"),
    auto_correct: true
  config.vm.provider "virtualbox" do |vb|
    vb.memory = ENV.fetch("VM_RAM","2048")
    vb.cpus   = ENV.fetch("VM_CPUS","2")
  end
  config.vm.provision "shell", path: "provision.sh", args: []
end
VFILE

# ---- provision.sh (runs inside VM; uses bash) ----
cat > provision.sh <<'PSH'
#!/usr/bin/env bash
set -euo pipefail
MONGO_IMAGE="${MONGO_IMAGE:-mongo:7.0}"
MONGO_USER="${MONGO_USER:-admin}"
MONGO_PASS="${MONGO_PASS:-change_me_strong}"
MONGO_DB="${MONGO_DB:-appdb}"
STACK_VERSION_FILE="/opt/mongo-stack/VERSION"

apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release jq tar cron

# Docker Engine + Compose Plugin
install -d -m 0755 /etc/apt/keyrings
if ! test -f /etc/apt/keyrings/docker.gpg; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
fi
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

usermod -aG docker vagrant || true
systemctl enable --now docker

# Project structure
mkdir -p /opt/mongo-stack/{compose,backups,exports}
chown -R vagrant:vagrant /opt/mongo-stack
echo "${STACK_VERSION:-1.0.1}" > "${STACK_VERSION_FILE}"

# Compose .env
cat > /opt/mongo-stack/compose/.env <<ENVF
MONGO_IMAGE=${MONGO_IMAGE}
MONGO_INITDB_ROOT_USERNAME=${MONGO_USER}
MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASS}
MONGO_INITDB_DATABASE=${MONGO_DB}
HOST_BIND=127.0.0.1
HOST_PORT=27017
VOLUME_NAME=mongo_data
ENVF

# docker-compose.yml
cat > /opt/mongo-stack/compose/docker-compose.yml <<'YML'
name: gmunden-mongo
services:
  mongo:
    image: ${MONGO_IMAGE}
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_INITDB_ROOT_USERNAME}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_INITDB_ROOT_PASSWORD}
      MONGO_INITDB_DATABASE: ${MONGO_INITDB_DATABASE}
    ports:
      - "${HOST_BIND}:${HOST_PORT}:27017"
    volumes:
      - ${VOLUME_NAME}:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--username", "${MONGO_INITDB_ROOT_USERNAME}", "--password", "${MONGO_INITDB_ROOT_PASSWORD}", "--eval", "db.adminCommand('ping')"]
      interval: 15s
      timeout: 5s
      retries: 20
volumes:
  ${VOLUME_NAME}:
YML

# Init seed
cat > /opt/mongo-stack/compose/init.js <<'JS'
db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE || "appdb");
db.createCollection("status");
db.status.updateOne(
  { _id: "bootstrap" },
  { $set: { createdAt: new Date(), note: "gmunden-mongo initialized" } },
  { upsert: true }
);
JS

cat > /opt/mongo-stack/compose/init.sh <<'ISH'
#!/usr/bin/env bash
set -euo pipefail
source ./.env
docker compose up -d
for i in $(seq 1 60); do
  state=$(docker inspect --format='{{json .State.Health.Status}}' $(docker compose ps -q mongo) | tr -d '"')
  if [ "$state" = "healthy" ]; then break; fi
  sleep 2
done
docker compose exec -T mongo mongosh -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --eval "load('/compose/init.js')"
ISH
chmod +x /opt/mongo-stack/compose/init.sh

# Backup/Restore
cat > /opt/mongo-stack/backups/backup.sh <<'BCK'
#!/usr/bin/env bash
set -euo pipefail
BASE="$(cd "$(dirname "$0")/.."; pwd)"
cd "$BASE/compose"
source ./.env
TS=$(date -u +%Y%m%dT%H%M%SZ)
VER="v$(cat ../VERSION 2>/dev/null || echo 0.0.0)"
OUT="$BASE/exports/mongodump_${TS}_${VER}.tar.gz"
CID=$(docker compose ps -q mongo)
docker exec "$CID" bash -lc "mongodump -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --authenticationDatabase admin --archive" | gzip -c > "$OUT"
echo "$OUT"
BCK
chmod +x /opt/mongo-stack/backups/backup.sh

cat > /opt/mongo-stack/backups/restore.sh <<'RST'
#!/usr/bin/env bash
set -euo pipefail
FILE="${1:-}"
if [ -z "$FILE" ]; then
  echo "Usage: restore.sh <mongodump_*.tar.gz>" >&2
  exit 1
fi
BASE="$(cd "$(dirname "$0")/.."; pwd)"
cd "$BASE/compose"
source ./.env
CID=$(docker compose ps -q mongo)
gzip -dc "$FILE" | docker exec -i "$CID" bash -lc "mongorestore --archive --drop -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --authenticationDatabase admin"
echo "Restore done."
RST
chmod +x /opt/mongo-stack/backups/restore.sh

# Weekly cron job
CRON_LINE='0 3 * * 1 /opt/mongo-stack/backups/backup.sh >> /var/log/mongo-backup.log 2>&1'
( crontab -l 2>/dev/null | grep -v 'mongo-backup' ; echo "$CRON_LINE" ) | crontab -

# Start + Seed
su - vagrant -c 'cd /opt/mongo-stack/compose && docker compose up -d && ./init.sh'
echo "Setup complete. Mongo available on 127.0.0.1:27017."
PSH
chmod +x provision.sh

# ---- Host .env ----
cat > .env <<ENVV
UBUNTU_BOX=${UBUNTU_BOX}
VM_NAME=${VM_NAME}
HOST_BIND_IP=${HOST_BIND_IP}
HOST_BIND_PORT=${HOST_BIND_PORT}
VM_RAM=${VM_RAM}
VM_CPUS=${VM_CPUS}
ENVV

print -r -- "Pack v${STACK_VERSION} ready. Bringing VM up…"
vagrant up
print -r -- "Access: ${HOST_BIND_IP}:${HOST_BIND_PORT} (user: ${MONGO_USER})"

