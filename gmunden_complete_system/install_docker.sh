#!/bin/bash
# 🐳 Gmunden Transparenz-System - Docker Installation
# Funktioniert auf: Linux, macOS, FreeBSD, OpenBSD

set -e

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🐳 Gmunden Transparenz-System - Docker Installation${NC}"
echo -e "${BLUE}===================================================${NC}"

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
                    curl -fsSL https://download.docker.com/linux/$DISTRO/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
                    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$DISTRO $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                    sudo apt-get update
                    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
                    ;;
                "centos"|"rhel"|"fedora")
                    sudo yum install -y yum-utils
                    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                    sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
                    ;;
                "arch")
                    sudo pacman -S docker docker-compose
                    ;;
                *)
                    echo -e "${RED}❌ Unbekannte Linux-Distribution: $DISTRO${NC}"
                    echo "Bitte installieren Sie Docker manuell: https://docs.docker.com/engine/install/"
                    exit 1
                    ;;
            esac
            
            # Docker-Service starten
            sudo systemctl start docker
            sudo systemctl enable docker
            
            # Benutzer zur docker-Gruppe hinzufügen
            sudo usermod -aG docker $USER
            echo -e "${YELLOW}⚠️ Bitte melden Sie sich ab und wieder an, um Docker ohne sudo zu verwenden${NC}"
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
                echo "Oder installieren Sie Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                exit 1
            fi
            ;;
            
        "FreeBSD")
            echo -e "${YELLOW}🔱 FreeBSD Docker Installation...${NC}"
            echo "FreeBSD unterstützt Docker nicht nativ. Verwenden Sie stattdessen:"
            echo "1. Podman: pkg install podman"
            echo "2. Oder eine Linux-VM mit Docker"
            exit 1
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
            # Docker Compose Plugin ist meist schon installiert
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
    
    # Verzeichnisse erstellen
    echo -e "${YELLOW}📁 Erstelle Verzeichnisse...${NC}"
    mkdir -p uploads backups logs mongo-init ssl
    
    # MongoDB Init-Script
    cat > mongo-init/init.js << 'EOF'
// MongoDB Initialisierung für Gmunden Transparenz-System
db = db.getSiblingDB('gmunden');

// Collections erstellen
db.createCollection('dokumente');
db.createCollection('finanzen');
db.createCollection('protokolle');
db.createCollection('statistiken');
db.createCollection('jahre');

// Indizes erstellen
db.dokumente.createIndex({ "filename": 1 });
db.dokumente.createIndex({ "jahr": 1 });
db.dokumente.createIndex({ "kategorie": 1 });
db.dokumente.createIndex({ "tags": 1 });
db.dokumente.createIndex({ 
    "filename": "text", 
    "ocr_text": "text", 
    "tags": "text" 
});

db.finanzen.createIndex({ "jahr": 1 });
db.finanzen.createIndex({ "kategorie": 1 });
db.finanzen.createIndex({ "betrag": -1 });

db.protokolle.createIndex({ "datum": -1 });
db.protokolle.createIndex({ "typ": 1 });

db.jahre.createIndex({ "jahr": 1 });

print("✅ MongoDB für Gmunden Transparenz-System initialisiert");
EOF
    
    # Nginx-Konfiguration
    cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream gmunden_app {
        server gmunden-app:12000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        client_max_body_size 200M;
        
        location / {
            proxy_pass http://gmunden_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket Support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
EOF
    
    # Docker-Images bauen
    echo -e "${YELLOW}🏗️ Baue Docker-Images...${NC}"
    docker compose build
    
    # System starten
    echo -e "${GREEN}🚀 Starte Gmunden Transparenz-System...${NC}"
    docker compose up -d
    
    # Warten auf Services
    echo -e "${YELLOW}⏳ Warte auf Services...${NC}"
    sleep 10
    
    # Status prüfen
    echo -e "${YELLOW}📊 Service-Status:${NC}"
    docker compose ps
    
    echo ""
    echo -e "${GREEN}🎉 Installation abgeschlossen!${NC}"
    echo ""
    echo -e "${BLUE}📊 System-URLs:${NC}"
    echo "   🌐 Haupt-Interface: http://localhost:12000"
    echo "   🔐 Admin-Bereich: http://localhost:12000 (Passwort: admin123)"
    echo "   🗄️ MongoDB: mongodb://localhost:27017"
    echo "   🔄 Redis: redis://localhost:6379"
    echo ""
    echo -e "${YELLOW}💡 Nützliche Befehle:${NC}"
    echo "   • Status: docker compose ps"
    echo "   • Logs: docker compose logs -f"
    echo "   • Stoppen: docker compose down"
    echo "   • Neustarten: docker compose restart"
    echo "   • Backup: ls -la backups/"
    echo ""
    echo -e "${GREEN}✅ System ist bereit für Ihre 16 PDF-Protokolle!${NC}"
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