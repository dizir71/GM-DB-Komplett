#!/usr/bin/env bash
# pack.sh — Portable, abgeschlossene MongoDB-Umgebung (VM + Docker)
# Version des Stacks:
STACK_VERSION="1.0.0"

set -euo pipefail

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

mkdir -p "${PROJECT}"
cd "${PROJECT}"

# Vagrantfile
cat &gt; Vagrantfile &lt;&lt;'VFILE'
Vagrant.configure("2") do |config|
  config.vm.box = ENV.fetch("UBUNTU_BOX", "ubuntu/jammy64")
  config.vm.hostname = ENV.fetch("VM_NAME", "gmunden-mongo")
  config.vm.network "forwarded_port", guest: 27017, host: ENV.fetch("HOST_BIND_PORT","27017"), host_ip: ENV.fetch("HOST_BIND_IP","127.0.0.1"), auto_correct: true
  config.vm.provider "virtualbox" do |vb|
    vb.memory = ENV.fetch("VM_RAM","2048")
    vb.cpus   = ENV.fetch("VM_CPUS","2")
  end
  config.vm.provision "shell", path: "provision.sh", args: []
end
VFILE

# Provisioning
cat &gt; provision.sh &lt;&lt;'PSH'
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
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release &amp;&amp; echo $VERSION_CODENAME) stable" &gt; /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

usermod -aG docker vagrant || true
systemctl enable --now docker

# Projektstruktur
mkdir -p /opt/mongo-stack/{compose,backups,exports}
chown -R vagrant:vagrant /opt/mongo-stack

# Version schreiben
echo "${STACK_VERSION:-1.0.0}" &gt; "${STACK_VERSION_FILE}"

# .env (Compose)
cat &gt; /opt/mongo-stack/compose/.env &lt;&lt;ENVF
MONGO_IMAGE=${MONGO_IMAGE}
MONGO_INITDB_ROOT_USERNAME=${MONGO_USER}
MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASS}
MONGO_INITDB_DATABASE=${MONGO_DB}
HOST_BIND=127.0.0.1
HOST_PORT=27017
VOLUME_NAME=mongo_data
ENVF

# docker-compose.yml
cat &gt; /opt/mongo-stack/compose/docker-compose.yml &lt;&lt;'YML'
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

# Optionales Seeding
cat &gt; /opt/mongo-stack/compose/init.js &lt;&lt;'JS'
db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE || "appdb");
db.createCollection("status");
db.status.updateOne(
  { _id: "bootstrap" },
  { $set: { createdAt: new Date(), note: "gmunden-mongo initialized" } },
  { upsert: true }
);
JS

cat &gt; /opt/mongo-stack/compose/init.sh &lt;&lt;'ISH'
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
cat &gt; /opt/mongo-stack/backups/backup.sh &lt;&lt;'BCK'
#!/usr/bin/env bash
set -euo pipefail
BASE="$(cd "$(dirname "$0")/.."; pwd)"
cd "$BASE/compose"
source ./.env
TS=$(date -u +%Y%m%dT%H%M%SZ)
VER="v$(cat ../VERSION 2>/dev/null || echo 0.0.0)"
OUT="$BASE/exports/mongodump_${TS}_${VER}.tar.gz"
CID=$(docker compose ps -q mongo)
docker exec "$CID" bash -lc "mongodump -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --authenticationDatabase admin --archive" | gzip -c &gt; "$OUT"
echo "$OUT"
BCK
chmod +x /opt/mongo-stack/backups/backup.sh

cat &gt; /opt/mongo-stack/backups/restore.sh &lt;&lt;'RST'
#!/usr/bin/env bash
set -euo pipefail
FILE="${1:-}"
if [ -z "$FILE" ]; then
  echo "Usage: restore.sh &lt;mongodump_*.tar.gz&gt;" &gt;&amp;2
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

# Wöchentliche Backups via Cron (Mo 03:00)
CRON_LINE='0 3 * * 1 /opt/mongo-stack/backups/backup.sh &gt;&gt; /var/log/mongo-backup.log 2&gt;&amp;1'
( crontab -l 2&gt;/dev/null | grep -v 'mongo-backup' ; echo "$CRON_LINE" ) | crontab -

# Start + Seed
su - vagrant -c 'cd /opt/mongo-stack/compose &amp;&amp; docker compose up -d &amp;&amp; ./init.sh'
echo "Setup abgeschlossen. Mongo auf 127.0.0.1:27017 (VM-Portweiterleitung)."
PSH
chmod +x provision.sh

# Host-ENV für Vagrant
cat &gt; .env &lt;&lt;ENVV
UBUNTU_BOX=${UBUNTU_BOX}
VM_NAME=${VM_NAME}
HOST_BIND_IP=${HOST_BIND_IP}
HOST_BIND_PORT=${HOST_BIND_PORT}
VM_RAM=${VM_RAM}
VM_CPUS=${VM_CPUS}
ENVV

echo "Pack v${STACK_VERSION} erstellt. Starte vagrant up…"
vagrant up
echo "Bereit. Zugriff: 127.0.0.1:${HOST_BIND_PORT} (User: ${MONGO_USER})"


