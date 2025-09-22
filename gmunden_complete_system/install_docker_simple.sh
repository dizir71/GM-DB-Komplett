#!/bin/bash
# 🐳 Gmunden Transparenz-System - Vereinfachte Docker Installation
# Behebt Docker-Build-Probleme

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🐳 Gmunden Transparenz-System - Vereinfachte Installation${NC}"
echo -e "${BLUE}======================================================${NC}"

# System erkennen
OS=$(uname -s)
ARCH=$(uname -m)

echo -e "${YELLOW}📊 System-Information:${NC}"
echo "   Betriebssystem: $OS"
echo "   Architektur: $ARCH"
echo "   Benutzer: $(whoami)"
echo ""

# Docker prüfen/installieren
check_docker() {
    if command -v docker >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker ist bereits installiert${NC}"
        docker --version
        return 0
    else
        echo -e "${YELLOW}📦 Docker wird installiert...${NC}"
        return 1
    fi
}

install_docker() {
    case "$OS" in
        "Linux")
            echo -e "${YELLOW}🐧 Linux Docker Installation...${NC}"
            
            # Distribution erkennen
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                DISTRO=$ID
            else
                DISTRO="unknown"
            fi
            
            case "$DISTRO" in
                "ubuntu"|"debian")
                    sudo apt-get update
                    sudo apt-get install -y ca-certificates curl gnupg lsb-release
                    curl -fsSL https://get.docker.com | sh
                    sudo usermod -aG docker $USER
                    ;;
                "centos"|"rhel"|"fedora")
                    curl -fsSL https://get.docker.com | sh
                    sudo usermod -aG docker $USER
                    sudo systemctl start docker
                    sudo systemctl enable docker
                    ;;
                "arch")
                    sudo pacman -S docker docker-compose
                    sudo systemctl start docker
                    sudo systemctl enable docker
                    sudo usermod -aG docker $USER
                    ;;
                *)
                    echo -e "${YELLOW}⚠️ Unbekannte Distribution, verwende universelles Script${NC}"
                    curl -fsSL https://get.docker.com | sh
                    sudo usermod -aG docker $USER
                    ;;
            esac
            ;;
            
        "Darwin")
            echo -e "${YELLOW}🍎 macOS Docker Installation...${NC}"
            
            if command -v brew >/dev/null 2>&1; then
                echo "Installiere Docker Desktop über Homebrew..."
                brew install --cask docker
                echo -e "${YELLOW}⚠️ Bitte starten Sie Docker Desktop manuell${NC}"
            else
                echo -e "${RED}❌ Homebrew nicht gefunden!${NC}"
                echo "Installieren Sie Docker Desktop manuell: https://docs.docker.com/desktop/mac/install/"
                exit 1
            fi
            ;;
            
        *)
            echo -e "${RED}❌ Unbekanntes Betriebssystem: $OS${NC}"
            echo "Bitte installieren Sie Docker manuell: https://docs.docker.com/engine/install/"
            exit 1
            ;;
    esac
}

# Docker Compose prüfen
check_docker_compose() {
    if docker compose version >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Compose ist verfügbar${NC}"
        docker compose version
        return 0
    elif command -v docker-compose >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker Compose (standalone) ist verfügbar${NC}"
        docker-compose --version
        return 0
    else
        echo -e "${YELLOW}📦 Docker Compose wird installiert...${NC}"
        return 1
    fi
}

install_docker_compose() {
    case "$OS" in
        "Linux")
            if ! docker compose version >/dev/null 2>&1; then
                echo "Installiere Docker Compose..."
                sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
                sudo chmod +x /usr/local/bin/docker-compose
            fi
            ;;
        "Darwin")
            echo "Docker Compose ist in Docker Desktop enthalten"
            ;;
    esac
}

# Hauptinstallation
main() {
    echo -e "${YELLOW}🔍 Prüfe Docker-Installation...${NC}"
    
    if ! check_docker; then
        install_docker
    fi
    
    if ! check_docker_compose; then
        install_docker_compose
    fi
    
    # Warten auf Docker
    echo -e "${YELLOW}⏳ Warte auf Docker-Service...${NC}"
    for i in {1..30}; do
        if docker info >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Docker ist bereit!${NC}"
            break
        fi
        sleep 2
        echo -n "."
    done
    echo ""
    
    # Verzeichnisse erstellen
    echo -e "${YELLOW}📁 Erstelle Verzeichnisse...${NC}"
    mkdir -p uploads logs data/{cache,backup,uploads,exports}
    
    # Vereinfachtes Docker Compose verwenden
    echo -e "${YELLOW}🔧 Verwende vereinfachte Konfiguration...${NC}"
    
    # Prüfen ob vereinfachtes Compose existiert
    if [ -f "docker-compose.simple.yml" ]; then
        COMPOSE_FILE="docker-compose.simple.yml"
        echo -e "${GREEN}✅ Verwende vereinfachte Konfiguration${NC}"
    else
        COMPOSE_FILE="docker-compose.yml"
        echo -e "${YELLOW}⚠️ Verwende Standard-Konfiguration${NC}"
    fi
    
    # Docker-Images bauen (mit Fehlerbehandlung)
    echo -e "${YELLOW}🏗️ Baue Docker-Images...${NC}"
    
    if [ "$COMPOSE_FILE" = "docker-compose.simple.yml" ]; then
        # Vereinfachter Build
        if docker compose -f "$COMPOSE_FILE" build --no-cache; then
            echo -e "${GREEN}✅ Docker-Images erfolgreich gebaut${NC}"
        else
            echo -e "${RED}❌ Docker-Build fehlgeschlagen${NC}"
            echo -e "${YELLOW}💡 Versuche Fallback-Methode...${NC}"
            
            # Fallback: Nur App-Container ohne komplexe Features
            cat > docker-compose.fallback.yml << 'EOF'
version: '3.8'
services:
  gmunden-app:
    image: python:3.11-slim
    container_name: gmunden-transparenz
    ports:
      - "12000:12000"
    volumes:
      - .:/app
      - gmunden_data:/app/data
    working_dir: /app
    command: >
      bash -c "
        apt-get update && 
        apt-get install -y curl tesseract-ocr tesseract-ocr-deu poppler-utils &&
        pip install -r requirements.txt &&
        streamlit run web/app.py --server.port 12000 --server.address 0.0.0.0
      "
    environment:
      - STREAMLIT_SERVER_PORT=12000
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
    restart: unless-stopped

volumes:
  gmunden_data:
EOF
            COMPOSE_FILE="docker-compose.fallback.yml"
        fi
    else
        docker compose -f "$COMPOSE_FILE" build
    fi
    
    # System starten
    echo -e "${GREEN}🚀 Starte Gmunden Transparenz-System...${NC}"
    docker compose -f "$COMPOSE_FILE" up -d
    
    # Warten auf Services
    echo -e "${YELLOW}⏳ Warte auf Services...${NC}"
    sleep 15
    
    # Status prüfen
    echo -e "${YELLOW}📊 Service-Status:${NC}"
    docker compose -f "$COMPOSE_FILE" ps
    
    # Gesundheitscheck
    echo -e "${YELLOW}🏥 Prüfe System-Gesundheit...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:12000 >/dev/null 2>&1; then
            echo -e "${GREEN}✅ System ist bereit!${NC}"
            break
        fi
        sleep 2
        echo -n "."
    done
    echo ""
    
    echo ""
    echo -e "${GREEN}🎉 Installation abgeschlossen!${NC}"
    echo ""
    echo -e "${BLUE}📊 System-URLs:${NC}"
    echo "   🌐 Haupt-Interface: http://localhost:12000"
    echo "   🔐 Admin-Bereich: http://localhost:12000 (Passwort: admin123)"
    echo ""
    echo -e "${YELLOW}💡 Nützliche Befehle:${NC}"
    echo "   • Status: docker compose -f $COMPOSE_FILE ps"
    echo "   • Logs: docker compose -f $COMPOSE_FILE logs -f"
    echo "   • Stoppen: docker compose -f $COMPOSE_FILE down"
    echo "   • Neustarten: docker compose -f $COMPOSE_FILE restart"
    echo ""
    echo -e "${GREEN}✅ System ist bereit für Ihre 16 PDF-Protokolle!${NC}"
    
    # Browser öffnen (falls möglich)
    if command -v open >/dev/null 2>&1; then
        echo -e "${YELLOW}🌐 Öffne Browser...${NC}"
        sleep 3
        open http://localhost:12000
    elif command -v xdg-open >/dev/null 2>&1; then
        echo -e "${YELLOW}🌐 Öffne Browser...${NC}"
        sleep 3
        xdg-open http://localhost:12000
    fi
}

# Cleanup bei Fehler
cleanup() {
    echo -e "${RED}❌ Installation fehlgeschlagen!${NC}"
    echo "Bereinige..."
    docker compose down 2>/dev/null || true
    exit 1
}

trap cleanup ERR

# Installation starten
main "$@"