# 🐳 Docker Troubleshooting Guide

## Häufige Docker-Build-Probleme

### Problem: "No matching distribution found for sqlite3"

**Ursache**: `sqlite3` ist ein eingebautes Python-Modul und kann nicht über pip installiert werden.

**Lösung**: ✅ Bereits behoben in den aktualisierten requirements.txt

### Problem: Docker-Build schlägt fehl

**Symptome**:
```
ERROR: Could not find a version that satisfies the requirement [package]
ERROR: No matching distribution found for [package]
```

**Lösungen**:

#### 1. Cache leeren und neu bauen
```bash
# Docker-Cache komplett leeren
docker system prune -a

# Neu bauen ohne Cache
docker-compose build --no-cache
```

#### 2. Minimale Installation verwenden
```bash
# Verwende install_simple.sh statt install.sh
./install_simple.sh
```

#### 3. Manuelle Docker-Installation
```bash
# Stoppe alle Container
docker-compose down

# Entferne alte Images
docker rmi $(docker images -q)

# Baue nur die kritischen Services
docker-compose up -d mongodb

# Starte Web-Service lokal (ohne Docker)
source venv/bin/activate
streamlit run web/app.py --server.port 12000
```

### Problem: Docker Desktop startet nicht (macOS)

**Symptome**:
- Docker-Befehle funktionieren nicht
- "Cannot connect to the Docker daemon" Fehler

**Lösungen**:

#### 1. Docker Desktop neu starten
```bash
# Docker Desktop beenden
pkill -f Docker

# Neu starten
open -a Docker

# Warten bis bereit
sleep 30
docker info
```

#### 2. Docker Desktop neu installieren
```bash
# Alte Installation entfernen
rm -rf /Applications/Docker.app

# Neu herunterladen (Apple Silicon)
curl -L https://desktop.docker.com/mac/main/arm64/Docker.dmg -o Docker.dmg

# Oder für Intel Macs:
curl -L https://desktop.docker.com/mac/main/amd64/Docker.dmg -o Docker.dmg

# Installieren
hdiutil attach Docker.dmg
cp -R /Volumes/Docker/Docker.app /Applications/
hdiutil detach /Volumes/Docker
rm Docker.dmg
```

#### 3. Colima als Alternative (für Entwickler)
```bash
# Colima installieren
brew install colima

# Starten
colima start

# Docker-Kontext setzen
docker context use colima
```

### Problem: Speicher-/Performance-Probleme

**Symptome**:
- Docker-Container sind langsam
- Build-Prozess hängt
- "Out of memory" Fehler

**Lösungen**:

#### 1. Docker Desktop Ressourcen erhöhen
1. Docker Desktop öffnen
2. Settings → Resources
3. Memory auf mindestens 4GB setzen
4. CPU auf mindestens 2 Cores
5. Apply & Restart

#### 2. Nicht verwendete Container/Images aufräumen
```bash
# Alle gestoppten Container entfernen
docker container prune

# Nicht verwendete Images entfernen
docker image prune -a

# Nicht verwendete Volumes entfernen
docker volume prune

# Alles auf einmal
docker system prune -a --volumes
```

### Problem: Port-Konflikte

**Symptome**:
```
Error starting userland proxy: listen tcp 0.0.0.0:12000: bind: address already in use
```

**Lösungen**:

#### 1. Port-Nutzung prüfen
```bash
# Welcher Prozess nutzt Port 12000?
lsof -i :12000

# Prozess beenden (PID aus obigem Befehl)
kill -9 [PID]
```

#### 2. Anderen Port verwenden
```bash
# docker-compose.yml bearbeiten
sed -i 's/12000:12000/12001:12000/' docker-compose.yml

# Oder manuell in docker-compose.yml:
# ports:
#   - "12001:12000"  # Externer Port 12001, interner Port 12000
```

### Problem: MongoDB-Verbindung fehlschlägt

**Symptome**:
- Web-Interface kann nicht auf Datenbank zugreifen
- "Connection refused" Fehler

**Lösungen**:

#### 1. MongoDB-Container prüfen
```bash
# Container-Status
docker-compose ps

# MongoDB-Logs
docker-compose logs mongodb

# MongoDB-Container neu starten
docker-compose restart mongodb
```

#### 2. MongoDB-Verbindung testen
```bash
# In MongoDB-Container einloggen
docker exec -it $(docker ps -q -f name=mongodb) mongosh

# Oder von außen testen
mongosh mongodb://localhost:27017/gmunden_db
```

#### 3. Netzwerk-Probleme beheben
```bash
# Docker-Netzwerk neu erstellen
docker-compose down
docker network prune
docker-compose up -d
```

## Alternative Installationsmethoden

### Methode 1: Nur lokale Installation (ohne Docker)

```bash
# Python-Umgebung einrichten
python3 -m venv venv
source venv/bin/activate

# Minimale Pakete installieren
pip install streamlit pandas plotly pymongo requests PyYAML

# MongoDB separat installieren (macOS)
brew install mongodb-community
brew services start mongodb-community

# Oder MongoDB Atlas (Cloud) verwenden
# Verbindungsstring in config/system_config.yaml anpassen

# Web-Interface starten
streamlit run web/app.py --server.port 12000
```

### Methode 2: Docker nur für MongoDB

```bash
# Nur MongoDB in Docker
docker run -d --name gmunden-mongo -p 27017:27017 mongo:7.0

# Web-Interface lokal
source venv/bin/activate
streamlit run web/app.py --server.port 12000
```

### Methode 3: Cloud-basierte Lösung

```bash
# MongoDB Atlas verwenden (kostenlos bis 512MB)
# 1. Account erstellen: https://cloud.mongodb.com
# 2. Cluster erstellen
# 3. Verbindungsstring kopieren
# 4. In config/system_config.yaml eintragen

# Streamlit Cloud verwenden
# 1. Code auf GitHub pushen
# 2. Streamlit Cloud Account: https://share.streamlit.io
# 3. App deployen
```

## Debugging-Befehle

### Container-Informationen
```bash
# Alle Container anzeigen
docker ps -a

# Container-Logs live verfolgen
docker-compose logs -f

# In Container einloggen
docker exec -it [container_name] /bin/bash

# Container-Ressourcen-Nutzung
docker stats
```

### Netzwerk-Debugging
```bash
# Docker-Netzwerke anzeigen
docker network ls

# Netzwerk-Details
docker network inspect [network_name]

# Port-Weiterleitung testen
curl http://localhost:12000/_stcore/health
```

### Image-Management
```bash
# Alle Images anzeigen
docker images

# Image-Details
docker inspect [image_name]

# Image-Größe reduzieren
docker build --squash -t [image_name] .
```

## Notfall-Reset

Falls nichts funktioniert, kompletter Neustart:

```bash
# 1. Alle Container stoppen
docker-compose down

# 2. Alle Docker-Daten löschen
docker system prune -a --volumes

# 3. Docker Desktop neu starten (macOS)
pkill -f Docker
open -a Docker
sleep 30

# 4. Projekt neu installieren
./install_simple.sh

# 5. Falls Docker-Probleme bestehen, lokale Installation:
python3 -m venv venv
source venv/bin/activate
pip install -r config/requirements_minimal.txt
streamlit run web/app.py --server.port 12000
```

## Support

### Log-Dateien sammeln
```bash
# Install-Logs
cat install_simple.log

# Docker-Logs
docker-compose logs > docker_logs.txt

# System-Informationen
docker info > docker_info.txt
docker version >> docker_info.txt
```

### Hilfe anfordern
Wenn Sie Hilfe benötigen, sammeln Sie diese Informationen:

1. **Betriebssystem**: `uname -a`
2. **Docker-Version**: `docker --version`
3. **Python-Version**: `python3 --version`
4. **Fehlermeldung**: Vollständige Ausgabe
5. **Log-Dateien**: install_simple.log, docker-compose logs

---

**Tipp**: Verwenden Sie `install_simple.sh` für die stabilste Installation mit minimalen Abhängigkeiten.