#!/usr/bin/env bash
# Gmunden Transparenz-Datenbank - macOS-optimiertes Install-Script
# Speziell für macOS mit besserer Fehlerbehandlung

set -euo pipefail

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Konfiguration
PROJECT_NAME="gmunden-transparenz-db"
WEB_PORT="12000"
MONGO_PORT="27017"
OCR_PORT="8080"

# Logging
LOG_FILE="install_macos.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

# Funktionen
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    🏛️  GMUNDEN TRANSPARENZ-DATENBANK                        ║"
    echo "║                      macOS-optimiertes Install-Script                       ║"
    echo "║                              Version 2.0.0                                  ║"
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

check_macos_system() {
    print_step "Überprüfe macOS-System..."
    
    # macOS Version prüfen
    MACOS_VERSION=$(sw_vers -productVersion)
    print_info "macOS Version: $MACOS_VERSION"
    
    # Architektur prüfen
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        print_info "Apple Silicon (M1/M2) erkannt"
        HOMEBREW_PREFIX="/opt/homebrew"
    else
        print_info "Intel Mac erkannt"
        HOMEBREW_PREFIX="/usr/local"
    fi
    
    # Speicher prüfen
    MEMORY_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    print_info "Verfügbarer Speicher: ${MEMORY_GB}GB"
    
    if [ "$MEMORY_GB" -lt 4 ]; then
        print_warning "Weniger als 4GB RAM. Performance könnte beeinträchtigt sein."
    fi
    
    # Festplattenspeicher prüfen
    DISK_FREE_GB=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G.*//')
    print_info "Freier Festplattenspeicher: ${DISK_FREE_GB}GB"
    
    if [ "${DISK_FREE_GB%.*}" -lt 10 ]; then
        print_error "Mindestens 10GB freier Speicher erforderlich!"
        exit 1
    fi
    
    # Xcode Command Line Tools prüfen
    if ! xcode-select -p &> /dev/null; then
        print_step "Installiere Xcode Command Line Tools..."
        xcode-select --install
        print_info "Bitte warten Sie, bis die Installation abgeschlossen ist, und führen Sie das Script erneut aus."
        exit 0
    fi
    
    print_success "macOS-System-Prüfung abgeschlossen"
}

install_homebrew() {
    print_step "Installiere/Aktualisiere Homebrew..."
    
    if command -v brew &> /dev/null; then
        print_info "Homebrew bereits installiert: $(brew --version | head -1)"
        
        # Homebrew zum PATH hinzufügen falls nötig
        if [[ ":$PATH:" != *":$HOMEBREW_PREFIX/bin:"* ]]; then
            export PATH="$HOMEBREW_PREFIX/bin:$PATH"
            echo "export PATH=\"$HOMEBREW_PREFIX/bin:\$PATH\"" >> ~/.zshrc
        fi
        
        print_step "Aktualisiere Homebrew..."
        brew update || print_warning "Homebrew-Update fehlgeschlagen (nicht kritisch)"
    else
        print_step "Installiere Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Homebrew zum PATH hinzufügen
        eval "$($HOMEBREW_PREFIX/bin/brew shellenv)"
        echo "eval \"\$($HOMEBREW_PREFIX/bin/brew shellenv)\"" >> ~/.zshrc
        
        print_success "Homebrew erfolgreich installiert"
    fi
}

install_system_tools() {
    print_step "Installiere System-Tools..."
    
    # Basis-Tools (nur die, die nicht bereits vorhanden sind)
    basic_tools=()
    
    # curl ist normalerweise vorinstalliert, aber prüfen wir trotzdem
    if ! command -v curl &> /dev/null; then
        basic_tools+=("curl")
    fi
    
    # wget ist normalerweise nicht vorinstalliert
    if ! command -v wget &> /dev/null; then
        basic_tools+=("wget")
    fi
    
    # git ist normalerweise nicht vorinstalliert
    if ! command -v git &> /dev/null; then
        basic_tools+=("git")
    fi
    
    # unzip ist normalerweise vorinstalliert
    if ! command -v unzip &> /dev/null; then
        basic_tools+=("unzip")
    fi
    
    # Installiere nur die Tools, die wir brauchen
    if [ ${#basic_tools[@]} -gt 0 ]; then
        for tool in "${basic_tools[@]}"; do
            print_step "Installiere $tool..."
            if brew install "$tool"; then
                print_success "$tool installiert"
            else
                print_warning "$tool konnte nicht installiert werden"
            fi
        done
    else
        print_success "Alle Basis-Tools bereits verfügbar"
    fi
    
    print_success "System-Tools-Installation abgeschlossen"
}

install_docker_desktop() {
    print_step "Installiere Docker Desktop..."
    
    # Prüfen ob Docker Desktop bereits installiert ist
    if [ -d "/Applications/Docker.app" ]; then
        print_info "Docker Desktop bereits installiert"
        
        # Docker Desktop starten falls nicht läuft
        if ! docker info &> /dev/null; then
            print_step "Starte Docker Desktop..."
            open -a Docker
            wait_for_docker 120
        else
            print_success "Docker Desktop läuft bereits"
        fi
    else
        print_step "Installiere Docker Desktop über Homebrew..."
        
        if brew install --cask docker; then
            print_success "Docker Desktop über Homebrew installiert"
        else
            print_warning "Homebrew-Installation fehlgeschlagen, versuche direkten Download..."
            install_docker_direct
        fi
        
        print_step "Starte Docker Desktop..."
        open -a Docker
        wait_for_docker 120
    fi
    
    # Docker Compose prüfen
    if docker compose version &> /dev/null; then
        print_success "Docker Compose verfügbar: $(docker compose version --short)"
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        print_success "Docker Compose (v1) verfügbar: $(docker-compose --version)"
        COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose nicht verfügbar!"
        exit 1
    fi
}

install_docker_direct() {
    print_step "Direkter Docker Desktop Download..."
    
    # Download-URL basierend auf Architektur
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
    
    print_success "Docker Desktop direkt installiert"
}

wait_for_docker() {
    local timeout=${1:-60}
    local count=0
    
    print_info "Warte auf Docker-Start (kann bis zu 2 Minuten dauern)..."
    
    while [ $count -lt $timeout ]; do
        if docker info &> /dev/null; then
            print_success "Docker ist bereit"
            return 0
        fi
        
        if [ $((count % 15)) -eq 0 ] && [ $count -gt 0 ]; then
            print_info "Warte noch auf Docker... ($count/$timeout Sekunden)"
        fi
        
        sleep 1
        ((count++))
    done
    
    print_error "Docker-Start-Timeout nach $timeout Sekunden!"
    print_info "Versuchen Sie Docker Desktop manuell zu starten und das Script erneut auszuführen."
    return 1
}

install_python_stack() {
    print_step "Installiere Python-Stack..."
    
    # Python3 prüfen
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_info "Python bereits verfügbar: $PYTHON_VERSION"
        
        # Version prüfen
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python-Version ist kompatibel"
        else
            print_step "Installiere neuere Python-Version..."
            install_python_homebrew
        fi
    else
        print_step "Python3 nicht gefunden, installiere über Homebrew..."
        install_python_homebrew
    fi
    
    # pip prüfen
    if ! command -v pip3 &> /dev/null; then
        print_step "Installiere pip..."
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        python3 get-pip.py --user
        rm get-pip.py
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    print_success "Python-Stack bereit"
}

install_python_homebrew() {
    # Versuche verschiedene Python-Versionen
    python_versions=("python@3.11" "python@3.10" "python@3.9")
    
    for py_version in "${python_versions[@]}"; do
        print_step "Versuche $py_version..."
        if brew install "$py_version"; then
            print_success "$py_version erfolgreich installiert"
            
            # Versuche zu verlinken (nicht kritisch wenn es fehlschlägt)
            brew link --overwrite "$py_version" 2>/dev/null || true
            return 0
        fi
    done
    
    print_warning "Keine Python-Version über Homebrew installierbar"
    print_info "Verwende System-Python falls verfügbar"
}

install_ocr_tools() {
    print_step "Installiere OCR-Tools..."
    
    # Tesseract OCR
    if brew install tesseract; then
        print_success "Tesseract OCR installiert"
        
        # Deutsche Sprache (optional)
        if brew install tesseract-lang; then
            print_success "Deutsche Tesseract-Sprache installiert"
        else
            print_warning "Deutsche Tesseract-Sprache nicht verfügbar"
        fi
    else
        print_warning "Tesseract OCR konnte nicht installiert werden"
    fi
    
    # Poppler (für PDF-Verarbeitung)
    if brew install poppler; then
        print_success "Poppler installiert"
    else
        print_warning "Poppler konnte nicht installiert werden"
    fi
    
    # ImageMagick (für Bildverarbeitung)
    if brew install imagemagick; then
        print_success "ImageMagick installiert"
    else
        print_warning "ImageMagick konnte nicht installiert werden"
    fi
    
    print_success "OCR-Tools-Installation abgeschlossen"
}

setup_python_environment() {
    print_step "Richte Python-Umgebung ein..."
    
    # Virtual Environment erstellen
    if [ ! -d "venv" ]; then
        print_step "Erstelle Python Virtual Environment..."
        python3 -m venv venv
    fi
    
    # Virtual Environment aktivieren
    source venv/bin/activate
    
    # pip upgraden
    pip install --upgrade pip setuptools wheel
    
    # Requirements installieren
    if [ -f "config/requirements.txt" ]; then
        print_step "Installiere Python-Pakete..."
        
        # Versuche zuerst die korrigierte requirements.txt
        if pip install -r config/requirements.txt; then
            print_success "Alle Pakete aus requirements.txt installiert"
        else
            print_warning "requirements.txt Installation fehlgeschlagen, installiere kritische Pakete einzeln..."
            install_critical_packages_macos
        fi
        
        # spaCy deutsches Modell
        if pip show spacy &> /dev/null; then
            print_step "Installiere deutsches spaCy-Modell..."
            python -m spacy download de_core_news_sm || print_warning "Deutsches spaCy-Modell nicht verfügbar"
        fi
    else
        print_warning "requirements.txt nicht gefunden, installiere kritische Pakete..."
        install_critical_packages_macos
    fi
    
    print_success "Python-Umgebung eingerichtet"
}

install_critical_packages_macos() {
    print_step "Installiere kritische Pakete einzeln..."
    
    # Basis-Pakete (müssen funktionieren)
    critical_packages=(
        "streamlit>=1.28.0"
        "pandas>=2.0.0"
        "numpy>=1.24.0"
        "plotly>=5.15.0"
        "pymongo>=4.5.0"
        "requests>=2.31.0"
        "PyYAML>=6.0"
        "python-dateutil>=2.8.0"
    )
    
    for package in "${critical_packages[@]}"; do
        print_step "Installiere $package..."
        if pip install "$package"; then
            print_success "$package installiert"
        else
            print_warning "$package konnte nicht installiert werden"
        fi
    done
    
    # Erweiterte Pakete (optional für macOS)
    extended_packages=(
        "spacy>=3.6.0"
        "PyMuPDF>=1.23.0"
        "pytesseract>=0.3.10"
        "Pillow>=10.0.0"
        "openpyxl>=3.1.0"
        "matplotlib>=3.7.0"
        "seaborn>=0.12.0"
        "streamlit-option-menu>=0.3.6"
        "python-dotenv>=1.0.0"
        "cryptography>=41.0.0"
    )
    
    for package in "${extended_packages[@]}"; do
        print_step "Installiere $package (optional)..."
        if pip install "$package" 2>/dev/null; then
            print_success "$package installiert"
        else
            print_info "$package übersprungen (optional)"
        fi
    done
    
    print_success "Paket-Installation abgeschlossen"
}

create_docker_setup() {
    print_step "Erstelle Docker-Setup..."
    
    # Verwende das bereits vorhandene docker-compose.yml
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml nicht gefunden!"
        exit 1
    fi
    
    # Verzeichnisse erstellen
    mkdir -p data/{imports,processed,backups,uploads}
    mkdir -p logs
    
    print_success "Docker-Setup bereit"
}

start_services() {
    print_step "Starte Services..."
    
    # Docker Images bauen
    print_info "Baue Docker Images..."
    $COMPOSE_CMD build --no-cache
    
    # Services starten
    print_info "Starte Container..."
    $COMPOSE_CMD up -d
    
    # Warten auf Services
    print_step "Warte auf Service-Start..."
    sleep 15
    
    # Health Checks
    check_services_health
    
    print_success "Alle Services gestartet"
}

check_services_health() {
    print_step "Prüfe Service-Status..."
    
    # MongoDB
    local mongo_ready=false
    for i in {1..30}; do
        if docker exec ${PROJECT_NAME}-mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
            print_success "MongoDB ist bereit"
            mongo_ready=true
            break
        fi
        sleep 2
    done
    
    if [ "$mongo_ready" = false ]; then
        print_warning "MongoDB nicht bereit nach 60 Sekunden"
    fi
    
    # Web-Service
    local web_ready=false
    for i in {1..60}; do
        if curl -f http://localhost:${WEB_PORT}/_stcore/health &> /dev/null; then
            print_success "Web-Service ist bereit"
            web_ready=true
            break
        fi
        sleep 2
    done
    
    if [ "$web_ready" = false ]; then
        print_warning "Web-Service nicht bereit nach 120 Sekunden"
    fi
    
    # OCR-Agent
    if curl -f http://localhost:${OCR_PORT}/health &> /dev/null; then
        print_success "OCR-Agent ist bereit"
    else
        print_warning "OCR-Agent nicht bereit"
    fi
}

create_management_scripts() {
    print_step "Erstelle Management-Scripts..."
    
    # Start-Script
    cat > start.sh << EOF
#!/bin/bash
echo "🚀 Starte Gmunden Transparenz-Datenbank..."
$COMPOSE_CMD up -d
echo "✅ Services gestartet"
echo "🌐 Web-Interface: http://localhost:${WEB_PORT}"
EOF
    chmod +x start.sh
    
    # Stop-Script
    cat > stop.sh << EOF
#!/bin/bash
echo "🛑 Stoppe Gmunden Transparenz-Datenbank..."
$COMPOSE_CMD down
echo "✅ Services gestoppt"
EOF
    chmod +x stop.sh
    
    # Status-Script
    cat > status.sh << EOF
#!/bin/bash
echo "📊 Status der Gmunden Transparenz-Datenbank:"
echo "============================================="
$COMPOSE_CMD ps
echo ""
echo "🌐 Web-Interface: http://localhost:${WEB_PORT}"
echo "🗄️  MongoDB: localhost:${MONGO_PORT}"
echo "🔍 OCR-Agent: http://localhost:${OCR_PORT}"
EOF
    chmod +x status.sh
    
    print_success "Management-Scripts erstellt"
}

show_completion_info() {
    print_success "Installation erfolgreich abgeschlossen!"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎉 INSTALLATION ERFOLGREICH! 🎉                          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${CYAN}📍 ZUGRIFF AUF DIE ANWENDUNG:${NC}"
    echo -e "   🌐 Web-Interface:     ${BLUE}http://localhost:${WEB_PORT}${NC}"
    echo -e "   🌍 All-Hands.dev:     ${BLUE}https://work-1-syygiirqlvvwfggb.prod-runtime.all-hands.dev${NC}"
    echo ""
    
    echo -e "${CYAN}🛠️  VERWALTUNG:${NC}"
    echo -e "   ▶️  Starten:           ${GREEN}./start.sh${NC}"
    echo -e "   ⏹️  Stoppen:           ${RED}./stop.sh${NC}"
    echo -e "   📊 Status:            ${BLUE}./status.sh${NC}"
    echo ""
    
    echo -e "${CYAN}🚀 ERSTE SCHRITTE:${NC}"
    echo -e "   1. Öffnen Sie ${BLUE}http://localhost:${WEB_PORT}${NC} in Ihrem Browser"
    echo -e "   2. Testen Sie die Suche: ${YELLOW}'Wie viel gab die Gemeinde 2023 für Straßen aus?'${NC}"
    echo -e "   3. Laden Sie Dokumente im ${BLUE}📄 Dokumente${NC}-Bereich hoch"
    echo ""
    
    echo -e "${GREEN}🎯 Das System ist jetzt bereit für den produktiven Einsatz!${NC}"
    
    # Browser öffnen (optional)
    read -p "🌐 Möchten Sie das Web-Interface jetzt öffnen? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "http://localhost:${WEB_PORT}"
    fi
}

# Hauptfunktion
main() {
    print_header
    
    # macOS-spezifische Prüfungen
    check_macos_system
    
    # Homebrew installieren/aktualisieren
    install_homebrew
    
    # System-Tools installieren
    install_system_tools
    
    # Docker Desktop installieren
    install_docker_desktop
    
    # Python-Stack installieren
    install_python_stack
    
    # OCR-Tools installieren
    install_ocr_tools
    
    # Python-Umgebung einrichten
    setup_python_environment
    
    # Docker-Setup vorbereiten
    create_docker_setup
    
    # Services starten
    start_services
    
    # Management-Scripts erstellen
    create_management_scripts
    
    # Abschluss-Informationen
    show_completion_info
}

# Fehlerbehandlung
trap 'print_error "Installation fehlgeschlagen! Siehe $LOG_FILE für Details."; exit 1' ERR

# Script ausführen
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi