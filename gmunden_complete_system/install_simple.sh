#!/usr/bin/env bash
# Gmunden Transparenz-Datenbank - Vereinfachtes Install-Script
# Fokus auf Stabilität und Kompatibilität

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
LOG_FILE="install_simple.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    🏛️  GMUNDEN TRANSPARENZ-DATENBANK                        ║"
    echo "║                      Vereinfachtes Install-Script                           ║"
    echo "║                              Version 2.0.1                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] 🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] ℹ️  $1${NC}"
}

check_prerequisites() {
    print_step "Prüfe Grundvoraussetzungen..."
    
    # Betriebssystem
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
        print_info "System: macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="Linux"
        print_info "System: Linux"
    else
        print_error "Nicht unterstütztes System: $OSTYPE"
        print_info "Unterstützt: macOS, Linux"
        exit 1
    fi
    
    # Internet-Verbindung
    if ! ping -c 1 google.com &> /dev/null; then
        print_error "Keine Internet-Verbindung!"
        exit 1
    fi
    print_success "Internet-Verbindung verfügbar"
    
    # Speicher
    if [[ "$OS" == "macOS" ]]; then
        MEMORY_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    else
        MEMORY_GB=$(( $(grep MemTotal /proc/meminfo | awk '{print $2}') / 1024 / 1024 ))
    fi
    
    if [ "$MEMORY_GB" -lt 2 ]; then
        print_error "Mindestens 2GB RAM erforderlich! Gefunden: ${MEMORY_GB}GB"
        exit 1
    fi
    print_success "Speicher OK: ${MEMORY_GB}GB"
}

install_docker_simple() {
    print_step "Installiere Docker..."
    
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        print_success "Docker bereits verfügbar: $(docker --version)"
        return 0
    fi
    
    if [[ "$OS" == "macOS" ]]; then
        print_step "Installiere Docker Desktop für macOS..."
        
        # Prüfe ob bereits installiert
        if [ -d "/Applications/Docker.app" ]; then
            print_info "Docker Desktop bereits installiert, starte..."
            open -a Docker
        else
            print_info "Lade Docker Desktop herunter..."
            
            # Architektur erkennen
            if [[ $(uname -m) == "arm64" ]]; then
                DOCKER_URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
            else
                DOCKER_URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
            fi
            
            curl -L "$DOCKER_URL" -o Docker.dmg
            
            print_step "Installiere Docker Desktop..."
            hdiutil attach Docker.dmg -quiet
            cp -R /Volumes/Docker/Docker.app /Applications/
            hdiutil detach /Volumes/Docker -quiet
            rm Docker.dmg
            
            print_step "Starte Docker Desktop..."
            open -a Docker
        fi
        
        # Warte auf Docker-Start
        print_info "Warte auf Docker-Start (kann 1-2 Minuten dauern)..."
        for i in {1..60}; do
            if docker info &> /dev/null; then
                print_success "Docker ist bereit"
                return 0
            fi
            sleep 2
            if [ $((i % 15)) -eq 0 ]; then
                print_info "Warte noch... ($i/60)"
            fi
        done
        
        print_error "Docker-Start-Timeout!"
        print_info "Bitte starten Sie Docker Desktop manuell und führen Sie das Script erneut aus."
        exit 1
        
    else
        # Linux
        print_step "Installiere Docker für Linux..."
        
        # Offizielles Docker-Script verwenden
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        rm get-docker.sh
        
        # Docker-Service starten
        sudo systemctl start docker
        sudo systemctl enable docker
        
        # Benutzer zur docker-Gruppe hinzufügen
        sudo usermod -aG docker $USER
        
        print_warning "Bitte melden Sie sich ab und wieder an, um Docker ohne sudo zu verwenden."
        print_info "Oder führen Sie aus: newgrp docker"
    fi
    
    print_success "Docker installiert"
}

install_python_simple() {
    print_step "Prüfe Python-Installation..."
    
    # Python3 prüfen
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_info "Python gefunden: $PYTHON_VERSION"
        
        # Version prüfen (mindestens 3.8)
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python-Version ist kompatibel"
        else
            print_error "Python 3.8+ erforderlich, gefunden: $PYTHON_VERSION"
            install_python_version
        fi
    else
        print_step "Python3 nicht gefunden, installiere..."
        install_python_version
    fi
    
    # pip prüfen
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        print_step "Installiere pip..."
        if [[ "$OS" == "macOS" ]]; then
            # pip ist normalerweise mit Python installiert
            python3 -m ensurepip --upgrade
        else
            # Linux
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y python3-pip
            elif command -v yum &> /dev/null; then
                sudo yum install -y python3-pip
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y python3-pip
            fi
        fi
    fi
    
    print_success "Python-Installation OK"
}

install_python_version() {
    if [[ "$OS" == "macOS" ]]; then
        # Homebrew verwenden falls verfügbar
        if command -v brew &> /dev/null; then
            print_step "Installiere Python über Homebrew..."
            brew install python3 || print_warning "Homebrew-Installation fehlgeschlagen"
        else
            print_info "Homebrew nicht verfügbar"
            print_info "Bitte installieren Sie Python 3.8+ manuell von python.org"
            exit 1
        fi
    else
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3 python3-pip
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3 python3-pip
        else
            print_error "Paketmanager nicht unterstützt"
            exit 1
        fi
    fi
}

setup_python_environment() {
    print_step "Richte Python-Umgebung ein..."
    
    # Virtual Environment erstellen
    if [ ! -d "venv" ]; then
        print_step "Erstelle Virtual Environment..."
        python3 -m venv venv
    fi
    
    # Aktivieren
    source venv/bin/activate
    
    # pip upgraden
    pip install --upgrade pip
    
    # Basis-Pakete installieren
    print_step "Installiere Python-Pakete..."
    
    # Verwende minimale requirements falls verfügbar
    if [ -f "config/requirements_minimal.txt" ]; then
        print_step "Installiere minimale Pakete..."
        pip install -r config/requirements_minimal.txt || {
            print_warning "requirements_minimal.txt Installation fehlgeschlagen, versuche einzeln..."
            install_packages_individually
        }
    else
        install_packages_individually
    fi
    
    print_success "Python-Pakete installiert"
}

install_packages_individually() {
    # Kritische Pakete einzeln installieren
    critical_packages=(
        "streamlit>=1.28.0"
        "pandas>=1.5.0"
        "plotly>=5.0.0"
        "pymongo>=4.0.0"
        "requests>=2.25.0"
        "PyYAML>=6.0"
        "python-dateutil>=2.8.0"
        "Pillow>=9.0.0"
    )
    
    for package in "${critical_packages[@]}"; do
        print_step "Installiere $package..."
        pip install "$package" || print_warning "Konnte $package nicht installieren"
    done
    
    print_success "Python-Umgebung eingerichtet"
}

create_docker_compose() {
    print_step "Erstelle Docker-Konfiguration..."
    
    # Dockerfile
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python-Abhängigkeiten (verwende minimale requirements)
COPY config/requirements_minimal.txt ./requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# App kopieren
COPY . .

# Verzeichnisse erstellen
RUN mkdir -p data/imports data/processed data/backups logs

# Port freigeben
EXPOSE 12000

# Gesundheitscheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:12000/_stcore/health || exit 1

# Startbefehl
CMD ["streamlit", "run", "web/app.py", "--server.port=12000", "--server.address=0.0.0.0", "--server.enableCORS=true"]
EOF

    # docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  web:
    build: .
    ports:
      - "12000:12000"
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./data:/app/data
    depends_on:
      - mongodb
    restart: unless-stopped

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_DATABASE=gmunden_db
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped

volumes:
  mongodb_data:
EOF

    print_success "Docker-Konfiguration erstellt"
}

create_directories() {
    print_step "Erstelle Verzeichnisse..."
    
    mkdir -p data/{imports,processed,backups}
    mkdir -p logs
    
    # .gitkeep Dateien
    touch data/imports/.gitkeep
    touch data/processed/.gitkeep
    touch data/backups/.gitkeep
    touch logs/.gitkeep
    
    print_success "Verzeichnisse erstellt"
}

start_services() {
    print_step "Starte Services..."
    
    # Docker Compose verwenden
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose nicht verfügbar!"
        exit 1
    fi
    
    # Services starten
    $COMPOSE_CMD up -d --build
    
    # Warten auf Services
    print_info "Warte auf Service-Start..."
    sleep 15
    
    # MongoDB prüfen
    for i in {1..30}; do
        if docker exec $(docker ps -q -f name=mongodb) mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
            print_success "MongoDB ist bereit"
            break
        fi
        sleep 2
    done
    
    # Web-Service prüfen
    for i in {1..30}; do
        if curl -f http://localhost:12000/_stcore/health &> /dev/null; then
            print_success "Web-Service ist bereit"
            break
        fi
        sleep 2
    done
    
    print_success "Services gestartet"
}

create_management_scripts() {
    print_step "Erstelle Management-Scripts..."
    
    # Compose-Befehl ermitteln
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    # Start-Script
    cat > start.sh << EOF
#!/bin/bash
echo "🚀 Starte Gmunden Transparenz-Datenbank..."
$COMPOSE_CMD up -d
echo "✅ Services gestartet"
echo "🌐 Web-Interface: http://localhost:12000"
EOF
    chmod +x start.sh
    
    # Stop-Script
    cat > stop.sh << EOF
#!/bin/bash
echo "🛑 Stoppe Services..."
$COMPOSE_CMD down
echo "✅ Services gestoppt"
EOF
    chmod +x stop.sh
    
    # Status-Script
    cat > status.sh << EOF
#!/bin/bash
echo "📊 Service-Status:"
$COMPOSE_CMD ps
echo ""
echo "🌐 Web-Interface: http://localhost:12000"
echo "🗄️  MongoDB: localhost:27017"
EOF
    chmod +x status.sh
    
    print_success "Management-Scripts erstellt"
}

show_final_info() {
    print_success "Installation erfolgreich abgeschlossen!"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎉 INSTALLATION ERFOLGREICH! 🎉                          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${BLUE}📍 ZUGRIFF:${NC}"
    echo -e "   🌐 Web-Interface:     ${GREEN}http://localhost:12000${NC}"
    echo ""
    
    echo -e "${BLUE}🛠️  VERWALTUNG:${NC}"
    echo -e "   ▶️  Starten:           ${GREEN}./start.sh${NC}"
    echo -e "   ⏹️  Stoppen:           ${RED}./stop.sh${NC}"
    echo -e "   📊 Status:            ${BLUE}./status.sh${NC}"
    echo ""
    
    echo -e "${BLUE}🚀 ERSTE SCHRITTE:${NC}"
    echo -e "   1. Öffnen Sie ${GREEN}http://localhost:12000${NC} in Ihrem Browser"
    echo -e "   2. Testen Sie die Suche: ${YELLOW}'Zeige mir alle Daten'${NC}"
    echo -e "   3. Laden Sie Dokumente hoch"
    echo ""
    
    echo -e "${BLUE}🆘 SUPPORT:${NC}"
    echo -e "   📋 Logs:              ${BLUE}tail -f $LOG_FILE${NC}"
    echo -e "   🐛 Container-Logs:    ${BLUE}docker-compose logs${NC}"
    echo ""
    
    # Browser öffnen (optional)
    if [[ "$OS" == "macOS" ]]; then
        read -p "🌐 Web-Interface jetzt öffnen? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            open "http://localhost:12000"
        fi
    fi
}

# Hauptfunktion
main() {
    print_header
    
    # Grundprüfungen
    check_prerequisites
    
    # Docker installieren
    install_docker_simple
    
    # Python einrichten
    install_python_simple
    setup_python_environment
    
    # Docker-Setup
    create_docker_compose
    create_directories
    
    # Services starten
    start_services
    
    # Management-Tools
    create_management_scripts
    
    # Abschluss
    show_final_info
}

# Fehlerbehandlung
trap 'print_error "Installation fehlgeschlagen! Siehe $LOG_FILE für Details."; exit 1' ERR

# Script ausführen
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi