#!/usr/bin/env zsh
# pack.zsh — MongoDB Stack für macOS Apple Silicon (Colima + Docker, vmType=vz)
typeset -r STACK_VERSION="1.0.3"

set -e
set -u
(set -o pipefail 2>/dev/null) || setopt pipefail

# ---------- Config ----------
PROJECT="gmunden-mongo-stack"
MONGO_IMAGE="mongo:7.0"
MONGO_USER="admin"
MONGO_PASS="change_me_strong"
MONGO_DB="appdb"
HOST_BIND_IP="127.0.0.1"
HOST_BIND_PORT="27017"
COLIMA_PROFILE="gmunden-mongo"
COLIMA_MEM="2"       # GB
COLIMA_CPU="2"
COLIMA_DISK="20"     # GB

# ---------- Helpers ----------
die(){ print -r -- "ERROR: $*" >&2; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1; }
is_macos_arm(){ [[ "$OSTYPE" == darwin* ]] && [[ "$(uname -m)" == "arm64" ]]; }
brew_silent(){ HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_ENV_HINTS=1 "$@"; }

ensure_brew(){ need brew || die "Homebrew fehlt."; }

ensure_colima(){
  if ! need colima; then
    print "Installiere Colima…"
    ensure_brew
    brew_silent brew install colima || die "brew install colima fehlgeschlagen"
  fi
}

ensure_docker_cli(){
  if ! need docker; then
    print "Installiere Docker CLI…"
    ensure_brew
    brew_silent brew install docker || die "brew install docker fehlgeschlagen"
  fi
}

start_colima(){
  if ! colima status --profile "$COLIMA_PROFILE" >/dev/null 2>&1; then
    print "Starte Colima-VM ($COLIMA_PROFILE)…"
    colima start \
      --profile "$COLIMA_PROFILE" \
      --arch aarch64 \
      --cpu "$COLIMA_CPU" \
      --memory "$COLIMA_MEM" \
      --disk "$COLIMA_DISK" \
      --dns 1.1.1.1 \
      --mount-type virtiofs \
      --vm-type vz
  elif ! colima status --profile "$COLIMA_PROFILE" | grep -q 'Running'; then
    colima start --profile "$COLIMA_PROFILE"
  fi
}

ensure_docker_compose(){
  # v2 bevorzugt: 'docker compose'
  if docker compose version >/dev/null 2>&1; then
    export DOCKER_COMPOSE_FLAVOR="v2"
  elif command -v docker-compose >/dev/null 2>&1; then
    export DOCKER_COMPOSE_FLAVOR="v1"
  else
    ensure_brew
    brew_silent brew install docker-compose || true
    if docker compose version >/dev/null 2>&1; then
      export DOCKER_COMPOSE_FLAVOR="v2"
    elif command -v docker-compose >/dev/null 2>&1; then
      export DOCKER_COMPOSE_FLAVOR="v1"
    else
      die "Docker Compose nicht gefunden."
    fi
  fi
  # Kontext auf Colima
  if docker context ls | grep -q '^colima'; then
    docker context use colima >/dev/null 2>&1 || true
  fi
}

DCMD(){  # Compose-Wrapper
  if [[ "${DOCKER_COMPOSE_FLAVOR:-}" == "v2" ]]; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

# ---------- Main ----------
is_macos_arm || die "Nur für macOS Apple Silicon."
ensure_brew
ensure_colima
ensure_docker_cli
start_colima
ensure_docker_compose

mkdir -p "$PROJECT"
cd "$PROJECT"
mkdir -p compose backups exports cron tools
print -r -- "$STACK_VERSION" > VERSION

# Compose .env
cat > compose/.env <<EOF
MONGO_IMAGE=${MONGO_IMAGE}
MONGO_INITDB_ROOT_USERNAME=${MONGO_USER}
MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASS}
MONGO_INITDB_DATABASE=${MONGO_DB}
HOST_BIND=${HOST_BIND_IP}
HOST_PORT=${HOST_BIND_PORT}
VOLUME_NAME=mongo_data
EOF

# docker-compose.yml
cat > compose/docker-compose.yml <<'YML'
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

# init.js (Seed)
cat > compose/init.js <<'JS'
db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE || "appdb");
db.createCollection("status");
db.status.updateOne(
  { _id: "bootstrap" },
  { $set: { createdAt: new Date(), note: "gmunden-mongo initialized" } },
  { upsert: true }
);
JS

# init.sh (siehe Erklärung unten)
cat > compose/init.sh <<'ISH'
#!/usr/bin/env bash
set -euo pipefail
source ./.env

# Compose v2 bevorzugt, v1 Fallback
if docker compose version >/dev/null 2>&1; then
  C() { docker compose "$@"; }
else
  C() { docker-compose "$@"; }
fi

C up -d

# auf "healthy" warten
for i in $(seq 1 60); do
  CID=$(C ps -q mongo)
  state=$(docker inspect --format='{{json .State.Health.Status}}' "$CID" | tr -d '"')
  if [ "$state" = "healthy" ]; then break; fi
  sleep 2
done

C exec -T mongo mongosh \
  -u "$MONGO_INITDB_ROOT_USERNAME" \
  -p "$MONGO_INITDB_ROOT_PASSWORD" \
  --authenticationDatabase admin \
  --eval "load('/compose/init.js')"
ISH
chmod +x compose/init.sh

# Backups
cat > backups/backup.sh <<'BCK'
#!/usr/bin/env bash
set -euo pipefail
BASE="$(cd "$(dirname "$0")/.."; pwd)"
cd "$BASE/compose"
source ./.env

if docker compose version >/dev/null 2>&1; then
  C(){ docker compose "$@"; }
else
  C(){ docker-compose "$@"; }
fi

TS=$(date -u +%Y%m%dT%H%M%SZ)
VER="v$(cat ../VERSION 2>/dev/null || echo 0.0.0)"
OUT="$BASE/exports/mongodump_${TS}_${VER}.tar.gz"
CID=$(C ps -q mongo)

docker exec "$CID" bash -lc "mongodump -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --authenticationDatabase admin --archive" | gzip -c > "$OUT"
echo "$OUT"
BCK
chmod +x backups/backup.sh

cat > backups/restore.sh <<'RST'
#!/usr/bin/env bash
set -euo pipefail
FILE="${1:-}"
[ -n "$FILE" ] || { echo "Usage: restore.sh <mongodump_*.tar.gz>" >&2; exit 1; }

BASE="$(cd "$(dirname "$0")/.."; pwd)"
cd "$BASE/compose"
source ./.env

if docker compose version >/dev/null 2>&1; then
  C(){ docker compose "$@"; }
else
  C(){ docker-compose "$@"; }
fi

CID=$(C ps -q mongo)
gzip -dc "$FILE" | docker exec -i "$CID" bash -lc "mongorestore --archive --drop -u $MONGO_INITDB_ROOT_USERNAME -p $MONGO_INITDB_ROOT_PASSWORD --authenticationDatabase admin"
echo "Restore done."
RST
chmod +x backups/restore.sh

# Launchd (wöchentl. Mo 03:00)
cat > cron/weekly-backup.sh <<'WEEK'
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.."; pwd)"
"$DIR/backups/backup.sh" >> "$DIR/weekly-backup.log" 2>&1
WEEK
chmod +x cron/weekly-backup.sh

cat > tools/mk-launchd.zsh <<'PLZ'
#!/usr/bin/env zsh
set -e
JOB=gmunden.mongo.weekly
PLIST="$HOME/Library/LaunchAgents/${JOB}.plist"
ROOT="$(cd "$(dirname "$0")/.."; pwd)"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>${JOB}</string>
  <key>ProgramArguments</key>
  <array><string>${ROOT}/cron/weekly-backup.sh</string></array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>1</integer>
    <key>Hour</key><integer>3</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>StandardOutPath</key><string>${ROOT}/launchd.out.log</string>
  <key>StandardErrorPath</key><string>${ROOT}/launchd.err.log</string>
  <key>RunAtLoad</key><true/>
</dict></plist>
EOF
echo "Created: $PLIST"
echo "Aktivieren: launchctl load -w \"$PLIST\""
PLZ
chmod +x tools/mk-launchd.zsh

# Stack starten + seed
cd compose
DCMD up -d
./init.sh

print -r -- "\nFertig."
print -r -- "MongoDB: ${HOST_BIND_IP}:${HOST_BIND_PORT}"
print -r -- "Backup:   ./backups/backup.sh"
print -r -- "Restore:  ./backups/restore.sh ./exports/<dump>.tar.gz"
print -r -- "Launchd:  zsh ./tools/mk-launchd.zsh && launchctl load -w ~/Library/LaunchAgents/gmunden.mongo.weekly.plist"

