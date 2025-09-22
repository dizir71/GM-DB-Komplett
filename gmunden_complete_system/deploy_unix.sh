#!/bin/bash
# 🌐 Gmunden Transparenz-System - Unix Deployment Script
# Repliziert das System auf verschiedene Unix-Systeme

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Konfiguration
REPO_URL="https://github.com/YOUR_USERNAME/gmunden-transparenz-system.git"
DOCKER_IMAGE="gmunden/transparenz-system"
DOCKER_TAG="latest"

echo -e "${BLUE}🌐 Gmunden Transparenz-System - Unix Deployment${NC}"
echo -e "${BLUE}===============================================${NC}"

# Funktionen
show_help() {
    echo "Usage: $0 [OPTION] [TARGET]"
    echo ""
    echo "Optionen:"
    echo "  --local          Lokale Installation"
    echo "  --remote HOST    Remote-Installation über SSH"
    echo "  --docker         Docker-basierte Installation"
    echo "  --build          Docker-Image bauen und pushen"
    echo "  --replicate      Auf mehrere Hosts replizieren"
    echo "  --help           Diese Hilfe anzeigen"
    echo ""
    echo "Beispiele:"
    echo "  $0 --local"
    echo "  $0 --remote user@server.com"
    echo "  $0 --docker"
    echo "  $0 --replicate hosts.txt"
}

detect_system() {
    OS=$(uname -s)
    ARCH=$(uname -m)
    
    case "$OS" in
        "Linux")
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                DISTRO=$ID
                VERSION=$VERSION_ID
            else
                DISTRO="unknown"
                VERSION="unknown"
            fi
            ;;
        "Darwin")
            DISTRO="macos"
            VERSION=$(sw_vers -productVersion)
            ;;
        "FreeBSD")
            DISTRO="freebsd"
            VERSION=$(freebsd-version)
            ;;
        "OpenBSD")
            DISTRO="openbsd"
            VERSION=$(uname -r)
            ;;
        *)
            DISTRO="unknown"
            VERSION="unknown"
            ;;
    esac
    
    echo -e "${YELLOW}📊 Ziel-System:${NC}"
    echo "   OS: $OS"
    echo "   Distribution: $DISTRO"
    echo "   Version: $VERSION"
    echo "   Architektur: $ARCH"
    echo ""
}

install_dependencies() {
    echo -e "${YELLOW}📦 Installiere Abhängigkeiten...${NC}"
    
    case "$DISTRO" in
        "ubuntu"|"debian")
            sudo apt-get update
            sudo apt-get install -y curl wget git unzip
            ;;
        "centos"|"rhel"|"fedora")
            if command -v dnf >/dev/null 2>&1; then
                sudo dnf install -y curl wget git unzip
            else
                sudo yum install -y curl wget git unzip
            fi
            ;;
        "arch")
            sudo pacman -S --noconfirm curl wget git unzip
            ;;
        "macos")
            if ! command -v brew >/dev/null 2>&1; then
                echo "Installiere Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install curl wget git
            ;;
        "freebsd")
            sudo pkg install -y curl wget git unzip
            ;;
        "openbsd")
            sudo pkg_add curl wget git unzip
            ;;
        *)
            echo -e "${RED}❌ Unbekannte Distribution: $DISTRO${NC}"
            echo "Bitte installieren Sie manuell: curl, wget, git, unzip"
            ;;
    esac
}

download_system() {
    echo -e "${YELLOW}📥 Lade Gmunden Transparenz-System...${NC}"
    
    # Arbeitsverzeichnis erstellen
    INSTALL_DIR="$HOME/gmunden-transparenz-system"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # System herunterladen
    if [ -n "$REPO_URL" ] && [[ "$REPO_URL" == *"github.com"* ]]; then
        echo "Klone von GitHub Repository..."
        git clone "$REPO_URL" .
    else
        echo "Lade ZIP-Archiv..."
        curl -L -o gmunden_system.zip "https://github.com/YOUR_USERNAME/gmunden-transparenz-system/archive/main.zip"
        unzip gmunden_system.zip
        mv gmunden-transparenz-system-main/* .
        rm -rf gmunden-transparenz-system-main gmunden_system.zip
    fi
    
    # Berechtigungen setzen
    chmod +x *.sh
    
    echo -e "${GREEN}✅ System heruntergeladen nach: $INSTALL_DIR${NC}"
}

local_install() {
    echo -e "${YELLOW}🏠 Lokale Installation...${NC}"
    
    detect_system
    install_dependencies
    download_system
    
    # Installation starten
    if [ -f "install_docker.sh" ]; then
        echo -e "${YELLOW}🐳 Starte Docker-Installation...${NC}"
        ./install_docker.sh
    else
        echo -e "${YELLOW}🍎 Starte native Installation...${NC}"
        if [ -f "start_m3_silicon.sh" ] && [ "$DISTRO" = "macos" ]; then
            ./start_m3_silicon.sh
        elif [ -f "install_linux.sh" ]; then
            ./install_linux.sh
        else
            echo -e "${RED}❌ Kein passendes Install-Script gefunden${NC}"
            exit 1
        fi
    fi
}

remote_install() {
    local HOST=$1
    
    if [ -z "$HOST" ]; then
        echo -e "${RED}❌ Kein Host angegeben${NC}"
        echo "Usage: $0 --remote user@hostname"
        exit 1
    fi
    
    echo -e "${YELLOW}🌐 Remote-Installation auf: $HOST${NC}"
    
    # SSH-Verbindung testen
    if ! ssh -o ConnectTimeout=10 "$HOST" "echo 'SSH-Verbindung OK'"; then
        echo -e "${RED}❌ SSH-Verbindung zu $HOST fehlgeschlagen${NC}"
        exit 1
    fi
    
    # System auf Remote-Host kopieren
    echo -e "${YELLOW}📤 Kopiere System auf Remote-Host...${NC}"
    
    # Lokales System vorbereiten
    if [ ! -d "gmunden_complete_system" ]; then
        download_system
    fi
    
    # Auf Remote-Host kopieren
    scp -r gmunden_complete_system/ "$HOST:~/gmunden-transparenz-system/"
    
    # Remote-Installation starten
    ssh "$HOST" "
        cd ~/gmunden-transparenz-system
        chmod +x *.sh
        ./install_docker.sh
    "
    
    echo -e "${GREEN}✅ Remote-Installation auf $HOST abgeschlossen${NC}"
    echo "   URL: http://$HOST:12000"
}

docker_install() {
    echo -e "${YELLOW}🐳 Docker-Installation...${NC}"
    
    detect_system
    download_system
    
    # Docker-Installation
    ./install_docker.sh
    
    echo -e "${GREEN}✅ Docker-Installation abgeschlossen${NC}"
}

build_and_push() {
    echo -e "${YELLOW}🏗️ Baue und pushe Docker-Image...${NC}"
    
    if [ ! -f "Dockerfile" ]; then
        echo -e "${RED}❌ Dockerfile nicht gefunden${NC}"
        exit 1
    fi
    
    # Image bauen
    echo "Baue Docker-Image..."
    docker build -t "$DOCKER_IMAGE:$DOCKER_TAG" .
    docker build -t "$DOCKER_IMAGE:$(date +%Y%m%d)" .
    
    # Image pushen (falls Docker Hub Login vorhanden)
    if docker info | grep -q "Username:"; then
        echo "Pushe Docker-Image..."
        docker push "$DOCKER_IMAGE:$DOCKER_TAG"
        docker push "$DOCKER_IMAGE:$(date +%Y%m%d)"
        echo -e "${GREEN}✅ Docker-Image gepusht: $DOCKER_IMAGE:$DOCKER_TAG${NC}"
    else
        echo -e "${YELLOW}⚠️ Nicht bei Docker Hub angemeldet. Image nur lokal verfügbar.${NC}"
    fi
}

replicate_to_hosts() {
    local HOSTS_FILE=$1
    
    if [ -z "$HOSTS_FILE" ] || [ ! -f "$HOSTS_FILE" ]; then
        echo -e "${RED}❌ Hosts-Datei nicht gefunden: $HOSTS_FILE${NC}"
        echo "Erstellen Sie eine Datei mit einem Host pro Zeile:"
        echo "user@server1.com"
        echo "user@server2.com"
        exit 1
    fi
    
    echo -e "${YELLOW}🌐 Repliziere auf mehrere Hosts...${NC}"
    
    # Hosts-Datei lesen
    while IFS= read -r host; do
        # Leere Zeilen und Kommentare überspringen
        [[ -z "$host" || "$host" =~ ^#.*$ ]] && continue
        
        echo -e "${BLUE}📡 Repliziere auf: $host${NC}"
        
        # Remote-Installation für jeden Host
        if remote_install "$host"; then
            echo -e "${GREEN}✅ $host: Erfolgreich${NC}"
        else
            echo -e "${RED}❌ $host: Fehlgeschlagen${NC}"
        fi
        
        echo "---"
    done < "$HOSTS_FILE"
    
    echo -e "${GREEN}🎉 Replikation abgeschlossen${NC}"
}

create_deployment_package() {
    echo -e "${YELLOW}📦 Erstelle Deployment-Paket...${NC}"
    
    # Deployment-Verzeichnis erstellen
    DEPLOY_DIR="gmunden_deployment_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$DEPLOY_DIR"
    
    # Alle notwendigen Dateien kopieren
    cp -r gmunden_complete_system/* "$DEPLOY_DIR/"
    
    # Deployment-Dokumentation
    cat > "$DEPLOY_DIR/DEPLOYMENT.md" << 'EOF'
# 🚀 Gmunden Transparenz-System - Deployment

## Schnellstart

### Docker (Empfohlen)
```bash
./install_docker.sh
```

### Native Installation
```bash
# macOS M3 Silicon
./start_m3_silicon.sh

# Linux
./install_linux.sh
```

### Remote-Deployment
```bash
./deploy_unix.sh --remote user@server.com
```

## URLs nach Installation
- Web-Interface: http://localhost:12000
- Admin-Bereich: http://localhost:12000 (Passwort: admin123)

## Support
- Logs: docker compose logs -f
- Status: docker compose ps
- Stoppen: docker compose down
EOF
    
    # Paket komprimieren
    tar -czf "${DEPLOY_DIR}.tar.gz" "$DEPLOY_DIR"
    rm -rf "$DEPLOY_DIR"
    
    echo -e "${GREEN}✅ Deployment-Paket erstellt: ${DEPLOY_DIR}.tar.gz${NC}"
}

# Hauptfunktion
main() {
    case "$1" in
        "--local")
            local_install
            ;;
        "--remote")
            remote_install "$2"
            ;;
        "--docker")
            docker_install
            ;;
        "--build")
            build_and_push
            ;;
        "--replicate")
            replicate_to_hosts "$2"
            ;;
        "--package")
            create_deployment_package
            ;;
        "--help"|"-h"|"")
            show_help
            ;;
        *)
            echo -e "${RED}❌ Unbekannte Option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Script starten
main "$@"