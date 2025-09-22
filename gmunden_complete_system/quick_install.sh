#!/bin/bash
# 🚀 Gmunden Transparenz-System - Ein-Befehl-Installation
# curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/quick_install.sh | bash

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Konfiguration
REPO_URL="https://github.com/YOUR_USERNAME/gmunden-transparenz-system"
INSTALL_DIR="$HOME/gmunden-transparenz-system"
DEFAULT_PORT=12000

echo -e "${BLUE}🚀 Gmunden Transparenz-System - Schnell-Installation${NC}"
echo -e "${BLUE}====================================================${NC}"

# Parameter verarbeiten
INSTALL_TYPE="docker"
CUSTOM_PORT=""
SSL_ENABLED=false
PRODUCTION_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            INSTALL_TYPE="docker"
            shift
            ;;
        --native)
            INSTALL_TYPE="native"
            shift
            ;;
        --port)
            CUSTOM_PORT="$2"
            shift 2
            ;;
        --ssl)
            SSL_ENABLED=true
            shift
            ;;
        --production)
            PRODUCTION_MODE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Optionen:"
            echo "  --docker       Docker-Installation (Standard)"
            echo "  --native       Native Installation"
            echo "  --port PORT    Custom Port (Standard: 12000)"
            echo "  --ssl          SSL aktivieren"
            echo "  --production   Produktions-Modus"
            echo "  --help         Diese Hilfe"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unbekannte Option: $1${NC}"
            exit 1
            ;;
    esac
done

# System erkennen
detect_system() {
    OS=$(uname -s)
    ARCH=$(uname -m)
    
    echo -e "${YELLOW}📊 System-Information:${NC}"
    echo "   OS: $OS"
    echo "   Architektur: $ARCH"
    echo "   Installation: $INSTALL_TYPE"
    echo "   Port: ${CUSTOM_PORT:-$DEFAULT_PORT}"
    echo ""
}

# Abhängigkeiten installieren
install_dependencies() {
    echo -e "${YELLOW}📦 Installiere Basis-Abhängigkeiten...${NC}"
    
    case "$OS" in
        "Linux")
            if command -v apt-get >/dev/null 2>&1; then
                sudo apt-get update >/dev/null 2>&1
                sudo apt-get install -y curl wget git unzip >/dev/null 2>&1
            elif command -v yum >/dev/null 2>&1; then
                sudo yum install -y curl wget git unzip >/dev/null 2>&1
            elif command -v dnf >/dev/null 2>&1; then
                sudo dnf install -y curl wget git unzip >/dev/null 2>&1
            elif command -v pacman >/dev/null 2>&1; then
                sudo pacman -S --noconfirm curl wget git unzip >/dev/null 2>&1
            fi
            ;;
        "Darwin")
            if ! command -v brew >/dev/null 2>&1; then
                echo -e "${YELLOW}📦 Installiere Homebrew...${NC}"
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install curl wget git >/dev/null 2>&1 || true
            ;;
    esac
}

# System herunterladen
download_system() {
    echo -e "${YELLOW}📥 Lade Gmunden Transparenz-System...${NC}"
    
    # Altes Verzeichnis entfernen
    rm -rf "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # System herunterladen
    if curl -fsSL "${REPO_URL}/archive/main.tar.gz" | tar -xz --strip-components=1; then
        echo -e "${GREEN}✅ System erfolgreich heruntergeladen${NC}"
    else
        echo -e "${RED}❌ Download fehlgeschlagen${NC}"
        echo "Versuche alternativen Download..."
        
        # Fallback: ZIP-Download
        curl -L -o system.zip "${REPO_URL}/archive/main.zip"
        unzip -q system.zip
        mv gmunden-transparenz-system-main/* .
        rm -rf gmunden-transparenz-system-main system.zip
    fi
    
    # Berechtigungen setzen
    chmod +x *.sh
}

# Docker-Installation
install_docker() {
    echo -e "${YELLOW}🐳 Docker-Installation...${NC}"
    
    # Docker prüfen
    if ! command -v docker >/dev/null 2>&1; then
        echo -e "${YELLOW}📦 Installiere Docker...${NC}"
        
        case "$OS" in
            "Linux")
                curl -fsSL https://get.docker.com | sh
                sudo usermod -aG docker $USER
                ;;
            "Darwin")
                if command -v brew >/dev/null 2>&1; then
                    brew install --cask docker
                else
                    echo -e "${RED}❌ Bitte installieren Sie Docker Desktop manuell${NC}"
                    exit 1
                fi
                ;;
        esac
    fi
    
    # Docker Compose prüfen
    if ! docker compose version >/dev/null 2>&1; then
        if ! command -v docker-compose >/dev/null 2>&1; then
            echo -e "${YELLOW}📦 Installiere Docker Compose...${NC}"
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi
    fi
    
    # Port konfigurieren
    if [ -n "$CUSTOM_PORT" ]; then
        sed -i.bak "s/12000:12000/${CUSTOM_PORT}:12000/g" docker-compose.yml
    fi
    
    # SSL konfigurieren
    if [ "$SSL_ENABLED" = true ]; then
        echo -e "${YELLOW}🔒 Konfiguriere SSL...${NC}"
        # SSL-Konfiguration hier
    fi
    
    # System starten
    echo -e "${YELLOW}🚀 Starte Docker-Container...${NC}"
    docker compose up -d
    
    # Warten auf Services
    echo -e "${YELLOW}⏳ Warte auf Services...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:${CUSTOM_PORT:-$DEFAULT_PORT} >/dev/null 2>&1; then
            break
        fi
        sleep 2
        echo -n "."
    done
    echo ""
}

# Native Installation
install_native() {
    echo -e "${YELLOW}🏠 Native Installation...${NC}"
    
    case "$OS" in
        "Darwin")
            if [ -f "start_m3_silicon.sh" ]; then
                ./start_m3_silicon.sh
            else
                echo -e "${RED}❌ macOS-Script nicht gefunden${NC}"
                exit 1
            fi
            ;;
        "Linux")
            if [ -f "install_linux.sh" ]; then
                ./install_linux.sh
            else
                echo -e "${RED}❌ Linux-Script nicht gefunden${NC}"
                exit 1
            fi
            ;;
        *)
            echo -e "${RED}❌ Native Installation für $OS nicht unterstützt${NC}"
            echo "Verwenden Sie --docker für universelle Installation"
            exit 1
            ;;
    esac
}

# Hauptinstallation
main() {
    detect_system
    install_dependencies
    download_system
    
    case "$INSTALL_TYPE" in
        "docker")
            install_docker
            ;;
        "native")
            install_native
            ;;
        *)
            echo -e "${RED}❌ Unbekannter Installations-Typ: $INSTALL_TYPE${NC}"
            exit 1
            ;;
    esac
    
    # Erfolgsmeldung
    PORT=${CUSTOM_PORT:-$DEFAULT_PORT}
    
    echo ""
    echo -e "${GREEN}🎉 Installation erfolgreich abgeschlossen!${NC}"
    echo ""
    echo -e "${BLUE}📊 System-Informationen:${NC}"
    echo "   🌐 Web-Interface: http://localhost:$PORT"
    echo "   🔐 Admin-Bereich: http://localhost:$PORT (Passwort: admin123)"
    echo "   📁 Installation: $INSTALL_DIR"
    echo ""
    echo -e "${YELLOW}💡 Nächste Schritte:${NC}"
    echo "   1. Öffnen Sie http://localhost:$PORT"
    echo "   2. Melden Sie sich als Admin an (Passwort: admin123)"
    echo "   3. Gehen Sie zu 'Datei-Import' → 'Mehrere Dateien'"
    echo "   4. Laden Sie Ihre 16 PDF-Protokolle hoch"
    echo "   5. Starten Sie den Bulk-Import"
    echo ""
    echo -e "${GREEN}✅ Ihr Gmunden Transparenz-System ist einsatzbereit!${NC}"
    
    # Browser öffnen (falls möglich)
    if command -v open >/dev/null 2>&1; then
        echo -e "${YELLOW}🌐 Öffne Browser...${NC}"
        sleep 3
        open "http://localhost:$PORT"
    elif command -v xdg-open >/dev/null 2>&1; then
        echo -e "${YELLOW}🌐 Öffne Browser...${NC}"
        sleep 3
        xdg-open "http://localhost:$PORT"
    fi
}

# Fehlerbehandlung
cleanup() {
    echo -e "${RED}❌ Installation fehlgeschlagen!${NC}"
    echo "Bereinige..."
    cd "$HOME"
    rm -rf "$INSTALL_DIR" 2>/dev/null || true
    exit 1
}

trap cleanup ERR

# Installation starten
main "$@"