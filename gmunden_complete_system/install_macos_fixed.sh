#!/usr/bin/env bash
# Gmunden Transparenz-Datenbank - macOS Fix-Script
# Behebt sqlite3 und andere macOS-spezifische Probleme

set -euo pipefail

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="install_macos_fixed.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    🏛️  GMUNDEN TRANSPARENZ-DATENBANK                        ║"
    echo "║                      macOS Fix-Script (sqlite3-Problem)                     ║"
    echo "║                              Version 2.0.2                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${CYAN}[$(date '+%H:%M:%S')] 🔧 $1${NC}"
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
    echo -e "${PURPLE}[$(date '+%H:%M:%S')] ℹ️  $1${NC}"
}

check_macos() {
    print_step "Prüfe macOS-System..."
    
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "Dieses Script ist nur für macOS!"
        exit 1
    fi
    
    MACOS_VERSION=$(sw_vers -productVersion)
    ARCH=$(uname -m)
    
    print_info "macOS Version: $MACOS_VERSION"
    print_info "Architektur: $ARCH"
    
    if [[ "$ARCH" == "arm64" ]]; then
        HOMEBREW_PREFIX="/opt/homebrew"
        print_info "Apple Silicon (M1/M2) erkannt"
    else
        HOMEBREW_PREFIX="/usr/local"
        print_info "Intel Mac erkannt"
    fi
    
    print_success "macOS-System OK"
}

install_homebrew_safe() {
    print_step "Installiere/Prüfe Homebrew..."
    
    if command -v brew &> /dev/null; then
        print_success "Homebrew bereits verfügbar"
        
        # PATH sicherstellen
        if [[ ":$PATH:" != *":$HOMEBREW_PREFIX/bin:"* ]]; then
            export PATH="$HOMEBREW_PREFIX/bin:$PATH"
        fi
        
        # Vorsichtiges Update
        print_step "Aktualisiere Homebrew (kann übersprungen werden bei Fehlern)..."
        brew update || print_warning "Homebrew-Update übersprungen"
    else
        print_step "Installiere Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # PATH setzen
        eval "$($HOMEBREW_PREFIX/bin/brew shellenv)"
        echo "eval \"\$($HOMEBREW_PREFIX/bin/brew shellenv)\"" >> ~/.zshrc
        
        print_success "Homebrew installiert"
    fi
}

install_python_safe() {
    print_step "Installiere Python (sicher)..."
    
    # Prüfe System-Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_info "System-Python gefunden: $PYTHON_VERSION"
        
        # Version prüfen
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            print_success "Python-Version ist kompatibel"
            PYTHON_CMD="python3"
        else
            print_step "Installiere neuere Python-Version..."
            install_python_homebrew
        fi
    else
        print_step "Kein Python gefunden, installiere..."
        install_python_homebrew
    fi
    
    # pip sicherstellen
    if ! $PYTHON_CMD -m pip --version &> /dev/null; then
        print_step "Installiere pip..."
        $PYTHON_CMD -m ensurepip --upgrade --user
    fi
    
    print_success "Python bereit: $($PYTHON_CMD --version)"
}

install_python_homebrew() {
    # Versuche verschiedene Python-Versionen
    python_versions=("python@3.11" "python@3.10" "python@3.9")
    
    for py_version in "${python_versions[@]}"; do
        print_step "Versuche $py_version..."
        if brew install "$py_version" 2>/dev/null; then
            print_success "$py_version installiert"
            
            # Finde Python-Pfad
            if command -v python3.11 &> /dev/null; then
                PYTHON_CMD="python3.11"
            elif command -v python3.10 &> /dev/null; then
                PYTHON_CMD="python3.10"
            elif command -v python3.9 &> /dev/null; then
                PYTHON_CMD="python3.9"
            else
                PYTHON_CMD="python3"
            fi
            
            return 0
        fi
    done
    
    print_warning "Homebrew Python-Installation fehlgeschlagen"
    PYTHON_CMD="python3"
}

create_clean_requirements() {
    print_step "Erstelle bereinigte requirements.txt..."
    
    mkdir -p config
    
    cat > config/requirements_clean.txt << 'EOF'
# Gmunden Transparenz-Datenbank - Bereinigte Dependencies
# KEINE eingebauten Module (sqlite3, json, os, etc.)

# Web Framework
streamlit>=1.28.0
streamlit-option-menu>=0.3.6

# Data Processing
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0

# Database
pymongo>=4.5.0

# Visualization
plotly>=5.15.0
matplotlib>=3.7.0
seaborn>=0.12.0

# NLP
spacy>=3.6.0

# Document Processing
PyMuPDF>=1.23.0
pytesseract>=0.3.10
Pillow>=10.0.0

# API and Web
requests>=2.31.0
urllib3>=2.0.0

# Configuration
PyYAML>=6.0
python-dotenv>=1.0.0

# Utilities
python-dateutil>=2.8.0

# Security
cryptography>=41.0.0
EOF
    
    print_success "Bereinigte requirements.txt erstellt"
}

setup_python_environment_safe() {
    print_step "Richte Python-Umgebung ein (sicher)..."
    
    # Virtual Environment erstellen
    if [ ! -d "venv" ]; then
        print_step "Erstelle Virtual Environment..."
        $PYTHON_CMD -m venv venv
    fi
    
    # Aktivieren
    source venv/bin/activate
    
    # pip upgraden
    pip install --upgrade pip setuptools wheel
    
    # Pakete einzeln installieren (sicherer)
    print_step "Installiere kritische Pakete..."
    
    # Basis-Pakete
    critical_packages=(
        "streamlit>=1.28.0"
        "pandas>=2.0.0"
        "numpy>=1.24.0"
        "plotly>=5.15.0"
        "pymongo>=4.5.0"
        "requests>=2.31.0"
        "PyYAML>=6.0"
        "python-dateutil>=2.8.0"
        "Pillow>=10.0.0"
    )
    
    for package in "${critical_packages[@]}"; do
        print_step "Installiere $package..."
        if pip install "$package"; then
            print_success "$package ✅"
        else
            print_warning "$package ❌ (nicht kritisch)"
        fi
    done
    
    # Erweiterte Pakete (optional)
    print_step "Installiere erweiterte Pakete..."
    
    extended_packages=(
        "streamlit-option-menu>=0.3.6"
        "openpyxl>=3.1.0"
        "matplotlib>=3.7.0"
        "seaborn>=0.12.0"
        "spacy>=3.6.0"
        "PyMuPDF>=1.23.0"
        "pytesseract>=0.3.10"
        "python-dotenv>=1.0.0"
        "cryptography>=41.0.0"
    )
    
    for package in "${extended_packages[@]}"; do
        if pip install "$package" 2>/dev/null; then
            print_info "$package ✅ (optional)"
        else
            print_info "$package ❌ (übersprungen)"
        fi
    done
    
    # spaCy deutsches Modell
    if pip show spacy &> /dev/null; then
        print_step "Installiere deutsches spaCy-Modell..."
        python -m spacy download de_core_news_sm || print_info "spaCy-Modell übersprungen"
    fi
    
    print_success "Python-Umgebung eingerichtet"
}

install_docker_simple() {
    print_step "Installiere Docker Desktop..."
    
    if [ -d "/Applications/Docker.app" ] && docker info &> /dev/null; then
        print_success "Docker Desktop bereits verfügbar"
        return 0
    fi
    
    if [ -d "/Applications/Docker.app" ]; then
        print_step "Docker Desktop gefunden, starte..."
        open -a Docker
    else
        print_step "Installiere Docker Desktop..."
        
        if command -v brew &> /dev/null; then
            # Versuche Homebrew zuerst
            if brew install --cask docker 2>/dev/null; then
                print_success "Docker Desktop über Homebrew installiert"
            else
                print_warning "Homebrew fehlgeschlagen, versuche direkten Download..."
                download_docker_direct
            fi
        else
            download_docker_direct
        fi
        
        print_step "Starte Docker Desktop..."
        open -a Docker
    fi
    
    # Warte auf Docker
    print_info "Warte auf Docker-Start..."
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
    
    print_warning "Docker-Start dauert länger als erwartet"
    print_info "Bitte warten Sie, bis Docker Desktop vollständig gestartet ist"
}

download_docker_direct() {
    if [[ "$ARCH" == "arm64" ]]; then
        DOCKER_URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
    else
        DOCKER_URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
    fi
    
    print_step "Lade Docker Desktop herunter..."
    curl -L "$DOCKER_URL" -o Docker.dmg
    
    print_step "Installiere Docker Desktop..."
    hdiutil attach Docker.dmg -quiet
    cp -R /Volumes/Docker/Docker.app /Applications/
    hdiutil detach /Volumes/Docker -quiet
    rm Docker.dmg
    
    print_success "Docker Desktop installiert"
}

install_ocr_tools_safe() {
    print_step "Installiere OCR-Tools (optional)..."
    
    if command -v brew &> /dev/null; then
        # Tesseract
        if brew install tesseract 2>/dev/null; then
            print_success "Tesseract OCR installiert"
            
            # Deutsche Sprache
            brew install tesseract-lang 2>/dev/null || print_info "Deutsche Tesseract-Sprache übersprungen"
        else
            print_info "Tesseract übersprungen"
        fi
        
        # Poppler
        brew install poppler 2>/dev/null && print_success "Poppler installiert" || print_info "Poppler übersprungen"
        
        # ImageMagick
        brew install imagemagick 2>/dev/null && print_success "ImageMagick installiert" || print_info "ImageMagick übersprungen"
    else
        print_info "OCR-Tools übersprungen (Homebrew nicht verfügbar)"
    fi
}

create_simple_docker_setup() {
    print_step "Erstelle einfaches Docker-Setup..."
    
    # Einfaches docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: gmunden-transparenz-mongodb
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
    
    # Verzeichnisse
    mkdir -p data/{imports,processed,backups} logs
    
    print_success "Docker-Setup erstellt"
}

start_services_safe() {
    print_step "Starte Services..."
    
    # Docker Compose ermitteln
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose nicht verfügbar!"
        return 1
    fi
    
    # Nur MongoDB starten
    print_step "Starte MongoDB..."
    $COMPOSE_CMD up -d mongodb
    
    # Warten auf MongoDB
    print_info "Warte auf MongoDB..."
    for i in {1..30}; do
        if docker exec gmunden-transparenz-mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
            print_success "MongoDB ist bereit"
            break
        fi
        sleep 2
    done
    
    # Web-Service lokal starten
    print_step "Starte Web-Service lokal..."
    source venv/bin/activate
    
    # Streamlit im Hintergrund starten
    nohup streamlit run web/app.py --server.port 12000 --server.address 0.0.0.0 > logs/web.log 2>&1 &
    WEB_PID=$!
    echo $WEB_PID > web.pid
    
    # Warten auf Web-Service
    print_info "Warte auf Web-Service..."
    for i in {1..30}; do
        if curl -f http://localhost:12000/_stcore/health &> /dev/null; then
            print_success "Web-Service ist bereit"
            break
        fi
        sleep 2
    done
    
    print_success "Services gestartet"
}

create_management_scripts_safe() {
    print_step "Erstelle Management-Scripts..."
    
    # Docker Compose ermitteln
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    # Start-Script
    cat > start.sh << EOF
#!/bin/bash
echo "🚀 Starte Gmunden Transparenz-Datenbank..."

# MongoDB starten
$COMPOSE_CMD up -d mongodb

# Web-Service starten
source venv/bin/activate
nohup streamlit run web/app.py --server.port 12000 --server.address 0.0.0.0 > logs/web.log 2>&1 &
echo \$! > web.pid

echo "✅ Services gestartet"
echo "🌐 Web-Interface: http://localhost:12000"
EOF
    chmod +x start.sh
    
    # Stop-Script
    cat > stop.sh << EOF
#!/bin/bash
echo "🛑 Stoppe Services..."

# Web-Service stoppen
if [ -f web.pid ]; then
    kill \$(cat web.pid) 2>/dev/null || true
    rm web.pid
fi

# MongoDB stoppen
$COMPOSE_CMD down

echo "✅ Services gestoppt"
EOF
    chmod +x stop.sh
    
    # Status-Script
    cat > status.sh << EOF
#!/bin/bash
echo "📊 Service-Status:"
echo "=================="

# MongoDB
if docker ps | grep gmunden-transparenz-mongodb > /dev/null; then
    echo "🗄️  MongoDB: ✅ Läuft"
else
    echo "🗄️  MongoDB: ❌ Gestoppt"
fi

# Web-Service
if [ -f web.pid ] && kill -0 \$(cat web.pid) 2>/dev/null; then
    echo "🌐 Web-Service: ✅ Läuft (PID: \$(cat web.pid))"
else
    echo "🌐 Web-Service: ❌ Gestoppt"
fi

echo ""
echo "🌐 Web-Interface: http://localhost:12000"
echo "🗄️  MongoDB: localhost:27017"
EOF
    chmod +x status.sh
    
    print_success "Management-Scripts erstellt"
}

show_completion_info() {
    print_success "Installation erfolgreich abgeschlossen!"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎉 macOS INSTALLATION ERFOLGREICH! 🎉                    ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${CYAN}📍 ZUGRIFF:${NC}"
    echo -e "   🌐 Web-Interface:     ${GREEN}http://localhost:12000${NC}"
    echo ""
    
    echo -e "${CYAN}🛠️  VERWALTUNG:${NC}"
    echo -e "   ▶️  Starten:           ${GREEN}./start.sh${NC}"
    echo -e "   ⏹️  Stoppen:           ${RED}./stop.sh${NC}"
    echo -e "   📊 Status:            ${BLUE}./status.sh${NC}"
    echo ""
    
    echo -e "${CYAN}🔧 BESONDERHEITEN DIESER INSTALLATION:${NC}"
    echo -e "   ✅ sqlite3-Problem behoben"
    echo -e "   ✅ Nur externe Python-Pakete installiert"
    echo -e "   ✅ Web-Service läuft lokal (nicht in Docker)"
    echo -e "   ✅ MongoDB läuft in Docker"
    echo -e "   ✅ Robuste Fehlerbehandlung"
    echo ""
    
    echo -e "${CYAN}🚀 ERSTE SCHRITTE:${NC}"
    echo -e "   1. Öffnen Sie ${GREEN}http://localhost:12000${NC} in Ihrem Browser"
    echo -e "   2. Testen Sie die Suche"
    echo -e "   3. Laden Sie Dokumente hoch"
    echo ""
    
    echo -e "${CYAN}📋 LOGS:${NC}"
    echo -e "   📄 Installation: ${BLUE}$LOG_FILE${NC}"
    echo -e "   📄 Web-Service: ${BLUE}logs/web.log${NC}"
    echo ""
    
    # Browser öffnen
    read -p "🌐 Web-Interface jetzt öffnen? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "http://localhost:12000"
    fi
}

# Hauptfunktion
main() {
    print_header
    
    # macOS prüfen
    check_macos
    
    # Homebrew sicher installieren
    install_homebrew_safe
    
    # Python sicher installieren
    install_python_safe
    
    # Bereinigte requirements erstellen
    create_clean_requirements
    
    # Python-Umgebung sicher einrichten
    setup_python_environment_safe
    
    # Docker einfach installieren
    install_docker_simple
    
    # OCR-Tools optional
    install_ocr_tools_safe
    
    # Einfaches Docker-Setup
    create_simple_docker_setup
    
    # Services sicher starten
    start_services_safe
    
    # Management-Scripts
    create_management_scripts_safe
    
    # Abschluss
    show_completion_info
}

# Fehlerbehandlung
trap 'print_error "Installation fehlgeschlagen! Siehe $LOG_FILE für Details."; exit 1' ERR

# Script ausführen
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi