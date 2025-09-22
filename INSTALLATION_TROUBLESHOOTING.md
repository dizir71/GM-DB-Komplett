# 🛠️ Installation Troubleshooting Guide

## Häufige macOS-Probleme und Lösungen

### Problem: "No available formula with the name 'tar'"

**Ursache**: `tar` und `gzip` sind auf macOS bereits vorinstalliert, Homebrew versucht sie aber zu installieren.

**Lösung**: Das Install-Script wurde korrigiert und installiert nur noch die notwendigen Tools.

```bash
# Falls das Problem weiterhin auftritt:
brew install curl wget git unzip
# tar und gzip sind bereits verfügbar
```

### Problem: Homebrew-Installation schlägt fehl

**Ursache**: Netzwerkprobleme oder Berechtigungsfehler.

**Lösungen**:

1. **Homebrew manuell installieren**:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **PATH korrekt setzen**:
   ```bash
   # Für Apple Silicon Macs:
   eval "$(/opt/homebrew/bin/brew shellenv)"
   
   # Für Intel Macs:
   eval "$(/usr/local/bin/brew shellenv)"
   ```

3. **Homebrew-Berechtigungen reparieren**:
   ```bash
   sudo chown -R $(whoami) /opt/homebrew
   # oder für Intel Macs:
   sudo chown -R $(whoami) /usr/local/Homebrew
   ```

### Problem: Docker Desktop startet nicht

**Ursache**: Docker Desktop benötigt Zeit zum Starten oder Berechtigungsprobleme.

**Lösungen**:

1. **Manuell starten**:
   ```bash
   open -a Docker
   # Warten bis Docker-Icon in der Menüleiste erscheint
   ```

2. **Docker Desktop neu installieren**:
   ```bash
   # Alte Installation entfernen
   rm -rf /Applications/Docker.app
   
   # Neu herunterladen und installieren
   # Für Apple Silicon:
   curl -L https://desktop.docker.com/mac/main/arm64/Docker.dmg -o Docker.dmg
   # Für Intel:
   curl -L https://desktop.docker.com/mac/main/amd64/Docker.dmg -o Docker.dmg
   
   # Installieren
   hdiutil attach Docker.dmg
   cp -R /Volumes/Docker/Docker.app /Applications/
   hdiutil detach /Volumes/Docker
   rm Docker.dmg
   ```

3. **Docker-Status prüfen**:
   ```bash
   docker --version
   docker info
   ```

### Problem: Python-Installation schlägt fehl

**Ursache**: Verschiedene Python-Versionen oder Homebrew-Konflikte.

**Lösungen**:

1. **System-Python verwenden**:
   ```bash
   # macOS hat Python3 vorinstalliert
   python3 --version
   python3 -m pip --version
   ```

2. **Python über Homebrew installieren**:
   ```bash
   brew install python@3.11
   # oder
   brew install python@3.10
   ```

3. **Python-Pfad korrigieren**:
   ```bash
   export PATH="/opt/homebrew/bin:$PATH"
   # oder für Intel Macs:
   export PATH="/usr/local/bin:$PATH"
   ```

## Allgemeine Linux-Probleme

### Problem: Berechtigungsfehler bei Docker

**Ursache**: Benutzer ist nicht in der docker-Gruppe.

**Lösung**:
```bash
sudo usermod -aG docker $USER
# Abmelden und wieder anmelden
newgrp docker
```

### Problem: Python-Pakete können nicht installiert werden

**Ursache**: Fehlende Entwicklungstools oder Python-Header.

**Lösung**:
```bash
# Ubuntu/Debian:
sudo apt-get install python3-dev python3-pip build-essential

# CentOS/RHEL:
sudo yum install python3-devel python3-pip gcc

# Arch Linux:
sudo pacman -S python python-pip base-devel
```

### Problem: Tesseract OCR nicht verfügbar

**Ursache**: OCR-Tools nicht installiert.

**Lösung**:
```bash
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-deu

# CentOS/RHEL:
sudo yum install tesseract tesseract-langpack-deu

# Arch Linux:
sudo pacman -S tesseract tesseract-data-deu
```

## System-spezifische Lösungen

### macOS Monterey/Ventura/Sonoma

1. **Xcode Command Line Tools installieren**:
   ```bash
   xcode-select --install
   ```

2. **Rosetta 2 für Apple Silicon** (falls Intel-Software benötigt):
   ```bash
   softwareupdate --install-rosetta
   ```

### Ubuntu 20.04/22.04

1. **Snap-Pakete aktualisieren**:
   ```bash
   sudo snap refresh
   ```

2. **Alternative Docker-Installation**:
   ```bash
   sudo snap install docker
   ```

### CentOS/RHEL 8/9

1. **EPEL Repository aktivieren**:
   ```bash
   sudo dnf install epel-release
   ```

2. **Podman als Docker-Alternative**:
   ```bash
   sudo dnf install podman podman-compose
   alias docker=podman
   ```

## Manuelle Installation (Fallback)

Falls das automatische Install-Script nicht funktioniert:

### 1. Docker manuell installieren

**macOS**:
```bash
# Docker Desktop herunterladen und installieren
open https://www.docker.com/products/docker-desktop/

# Oder via Homebrew:
brew install --cask docker
```

**Linux**:
```bash
# Offizielles Docker-Script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. Python-Umgebung einrichten

```bash
# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# Requirements installieren
pip install -r config/requirements.txt
```

### 3. Services starten

```bash
# Docker Compose starten
docker-compose up -d

# Web-Interface starten
streamlit run web/app.py --server.port 12000 --server.address 0.0.0.0
```

## Verifikation nach Installation

### System-Check ausführen

```bash
# Vollständige System-Verifikation
./verify_system.sh

# Einzelne Komponenten prüfen
docker --version
docker info
python3 --version
pip --version
```

### Services testen

```bash
# Container-Status
docker-compose ps

# Web-Interface
curl http://localhost:12000/_stcore/health

# MongoDB
docker exec gmunden-transparenz-db-mongodb mongosh --eval "db.adminCommand('ping')"

# OCR-Agent
curl http://localhost:8080/health
```

## Support-Kontakte

### Technischer Support
- **Logs prüfen**: `tail -f install.log`
- **System-Diagnose**: `./verify_system.sh`
- **Container-Logs**: `docker-compose logs`

### Community-Support
- **GitHub Issues**: Für Bug-Reports und Feature-Requests
- **Dokumentation**: README.md für detaillierte Informationen

## Bekannte Einschränkungen

### macOS
- Docker Desktop benötigt macOS 10.15+ (Catalina)
- Apple Silicon Macs benötigen spezielle Docker-Images
- Homebrew-Installation kann bei Corporate-Netzwerken fehlschlagen

### Linux
- Einige Distributionen benötigen zusätzliche Repositories
- SELinux kann Docker-Container blockieren
- Firewall-Einstellungen können Ports blockieren

### Windows
- Derzeit nicht unterstützt
- WSL2 wird empfohlen als Alternative

---

**Bei weiteren Problemen**: Erstellen Sie ein GitHub Issue mit den Logs aus `install.log` und der Ausgabe von `./verify_system.sh`.