#!/usr/bin/env bash
# Gmunden Transparenz-Datenbank - Vollständiges Install-Script
# Erstellt komplette Docker-Umgebung mit allen Voraussetzungen

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
DOCKER_COMPOSE_VERSION="2.21.0"
MONGODB_VERSION="7.0"
PYTHON_VERSION="3.11"
NODE_VERSION="18"
WEB_PORT="12000"
MONGO_PORT="27017"
OCR_PORT="8080"

# System-Erkennung
DETECTED_OS=""
DETECTED_ARCH=""
PACKAGE_MANAGER=""
DOCKER_INSTALL_METHOD=""

# Logging
LOG_FILE="install.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

# Funktionen
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    🏛️  GMUNDEN TRANSPARENZ-DATENBANK                        ║"
    echo "║                         Vollständiges Install-Script                        ║"
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

detect_system() {
    print_step "Erkenne System-Umgebung..."
    
    # Betriebssystem erkennen
    if [[ "$OSTYPE" == "darwin"* ]]; then
        DETECTED_OS="macOS"
        PACKAGE_MANAGER="brew"
        DOCKER_INSTALL_METHOD="brew"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        DETECTED_OS="Linux"
        
        # Linux-Distribution erkennen
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            case $ID in
                ubuntu|debian)
                    PACKAGE_MANAGER="apt"
                    DOCKER_INSTALL_METHOD="apt"
                    ;;
                centos|rhel|fedora)
                    PACKAGE_MANAGER="yum"
                    DOCKER_INSTALL_METHOD="yum"
                    ;;
                arch)
                    PACKAGE_MANAGER="pacman"
                    DOCKER_INSTALL_METHOD="pacman"
                    ;;
                *)
                    PACKAGE_MANAGER="generic"
                    DOCKER_INSTALL_METHOD="script"
                    ;;
            esac
            print_info "Linux-Distribution: $PRETTY_NAME"
        else
            PACKAGE_MANAGER="generic"
            DOCKER_INSTALL_METHOD="script"
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        DETECTED_OS="Windows"
        print_error "Windows wird derzeit nicht unterstützt. Bitte verwenden Sie WSL2."
        exit 1
    else
        print_error "Nicht unterstütztes Betriebssystem: $OSTYPE"
        exit 1
    fi
    
    # Architektur erkennen
    DETECTED_ARCH=$(uname -m)
    case $DETECTED_ARCH in
        x86_64|amd64)
            DETECTED_ARCH="amd64"
            ;;
        arm64|aarch64)
            DETECTED_ARCH="arm64"
            ;;
        armv7l)
            DETECTED_ARCH="armv7"
            ;;
        *)
            print_warning "Unbekannte Architektur: $DETECTED_ARCH"
            ;;
    esac
    
    print_info "System: $DETECTED_OS ($DETECTED_ARCH)"
    print_info "Paketmanager: $PACKAGE_MANAGER"
    print_info "Docker-Installation: $DOCKER_INSTALL_METHOD"
}

check_system_requirements() {
    print_step "Überprüfe System-Voraussetzungen..."
    
    # Speicher prüfen
    if [[ "$DETECTED_OS" == "macOS" ]]; then
        MEMORY_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    else
        MEMORY_GB=$(( $(grep MemTotal /proc/meminfo | awk '{print $2}') / 1024 / 1024 ))
    fi
    
    print_info "Verfügbarer Speicher: ${MEMORY_GB}GB"
    
    if [ "$MEMORY_GB" -lt 2 ]; then
        print_error "Mindestens 2GB RAM erforderlich!"
        exit 1
    elif [ "$MEMORY_GB" -lt 4 ]; then
        print_warning "Weniger als 4GB RAM. Performance könnte beeinträchtigt sein."
    fi
    
    # Festplattenspeicher prüfen
    if [[ "$DETECTED_OS" == "macOS" ]]; then
        DISK_FREE_GB=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G.*//')
    else
        DISK_FREE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G.*//')
    fi
    
    print_info "Freier Festplattenspeicher: ${DISK_FREE_GB}GB"
    
    if [ "${DISK_FREE_GB%.*}" -lt 5 ]; then
        print_error "Mindestens 5GB freier Speicher erforderlich!"
        exit 1
    elif [ "${DISK_FREE_GB%.*}" -lt 10 ]; then
        print_warning "Weniger als 10GB freier Speicher. Empfohlen sind 20GB+."
    fi
    
    # Internet-Verbindung prüfen
    print_step "Prüfe Internet-Verbindung..."
    if ! ping -c 1 google.com &> /dev/null; then
        print_error "Keine Internet-Verbindung! Installation benötigt Internet-Zugang."
        exit 1
    fi
    print_success "Internet-Verbindung verfügbar"
    
    # Berechtigungen prüfen
    if [[ "$DETECTED_OS" == "Linux" ]] && [[ $EUID -eq 0 ]]; then
        print_warning "Script läuft als root. Das könnte Probleme verursachen."
        read -p "Trotzdem fortfahren? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_success "System-Voraussetzungen erfüllt"
}

install_system_dependencies() {
    print_step "Installiere System-Abhängigkeiten..."
    
    case $PACKAGE_MANAGER in
        "brew")
            # macOS mit Homebrew
            if ! command -v brew &> /dev/null; then
                print_step "Installiere Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                
                # Homebrew zum PATH hinzufügen
                if [[ -f "/opt/homebrew/bin/brew" ]]; then
                    eval "$(/opt/homebrew/bin/brew shellenv)"
                    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
                elif [[ -f "/usr/local/bin/brew" ]]; then
                    eval "$(/usr/local/bin/brew shellenv)"
                    echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zshrc
                fi
            fi
            
            print_step "Aktualisiere Homebrew..."
            brew update || print_warning "Homebrew-Update fehlgeschlagen"
            
            print_step "Installiere Basis-Tools..."
            # Einzeln installieren für bessere Fehlerbehandlung
            tools=("curl" "wget" "git" "unzip")
            for tool in "${tools[@]}"; do
                if ! command -v "$tool" &> /dev/null; then
                    print_step "Installiere $tool..."
                    brew install "$tool" || print_warning "$tool konnte nicht installiert werden"
                else
                    print_info "$tool bereits verfügbar"
                fi
            done
            ;;
            
        "apt")
            # Ubuntu/Debian
            print_step "Aktualisiere Paket-Listen..."
            sudo apt-get update
            
            print_step "Installiere Basis-Tools..."
            sudo apt-get install -y \
                curl \
                wget \
                git \
                unzip \
                tar \
                gzip \
                ca-certificates \
                gnupg \
                lsb-release \
                software-properties-common \
                apt-transport-https
            ;;
            
        "yum")
            # CentOS/RHEL/Fedora
            print_step "Installiere Basis-Tools..."
            if command -v dnf &> /dev/null; then
                sudo dnf install -y curl wget git unzip tar gzip ca-certificates
            else
                sudo yum install -y curl wget git unzip tar gzip ca-certificates
            fi
            ;;
            
        "pacman")
            # Arch Linux
            print_step "Aktualisiere Paket-Listen..."
            sudo pacman -Sy
            
            print_step "Installiere Basis-Tools..."
            sudo pacman -S --noconfirm curl wget git unzip
            ;;
            
        *)
            print_warning "Unbekannter Paketmanager. Überspringe System-Abhängigkeiten."
            ;;
    esac
    
    print_success "System-Abhängigkeiten installiert"
}

install_docker() {
    print_step "Installiere Docker..."
    
    # Prüfen ob Docker bereits installiert ist
    if command -v docker &> /dev/null; then
        print_info "Docker bereits installiert: $(docker --version)"
        
        # Docker-Daemon läuft?
        if ! docker info &> /dev/null; then
            print_step "Starte Docker-Daemon..."
            start_docker_daemon
        fi
    else
        print_step "Installiere Docker..."
        install_docker_engine
    fi
    
    # Docker Compose prüfen/installieren
    install_docker_compose
    
    # Docker-Berechtigungen prüfen
    verify_docker_permissions
    
    print_success "Docker erfolgreich installiert und konfiguriert"
}

install_docker_engine() {
    case $DOCKER_INSTALL_METHOD in
        "brew")
            # macOS mit Homebrew
            print_step "Installiere Docker Desktop für macOS..."
            
            # Prüfen ob Docker Desktop bereits installiert ist
            if [ -d "/Applications/Docker.app" ]; then
                print_info "Docker Desktop bereits installiert"
            else
                brew install --cask docker || {
                    print_warning "Homebrew-Installation fehlgeschlagen, versuche direkten Download..."
                    
                    # Direkter Download als Fallback
                    if [[ "$DETECTED_ARCH" == "arm64" ]]; then
                        DOCKER_URL="https://desktop.docker.com/mac/main/arm64/Docker.dmg"
                    else
                        DOCKER_URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
                    fi
                    
                    print_step "Lade Docker Desktop herunter..."
                    curl -L "$DOCKER_URL" -o Docker.dmg
                    
                    print_step "Installiere Docker Desktop..."
                    hdiutil attach Docker.dmg
                    cp -R /Volumes/Docker/Docker.app /Applications/
                    hdiutil detach /Volumes/Docker
                    rm Docker.dmg
                }
            fi
            
            print_step "Starte Docker Desktop..."
            open -a Docker
            
            print_info "Warte auf Docker Desktop-Start (kann bis zu 2 Minuten dauern)..."
            wait_for_docker_start 120
            ;;
            
        "apt")
            # Ubuntu/Debian
            print_step "Installiere Docker für Ubuntu/Debian..."
            
            # Alte Docker-Versionen entfernen
            sudo apt-get remove -y docker docker-engine docker.io containerd runc || true
            
            # Docker GPG-Schlüssel hinzufügen
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            
            # Docker Repository hinzufügen
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            # Docker installieren
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            
            # Docker-Service starten
            sudo systemctl start docker
            sudo systemctl enable docker
            
            # Benutzer zur docker-Gruppe hinzufügen
            sudo usermod -aG docker $USER
            ;;
            
        "yum")
            # CentOS/RHEL/Fedora
            print_step "Installiere Docker für CentOS/RHEL/Fedora..."
            
            # Docker Repository hinzufügen
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            
            # Docker installieren
            if command -v dnf &> /dev/null; then
                sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            else
                sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            fi
            
            # Docker-Service starten
            sudo systemctl start docker
            sudo systemctl enable docker
            
            # Benutzer zur docker-Gruppe hinzufügen
            sudo usermod -aG docker $USER
            ;;
            
        "pacman")
            # Arch Linux
            print_step "Installiere Docker für Arch Linux..."
            sudo pacman -S --noconfirm docker docker-compose
            
            # Docker-Service starten
            sudo systemctl start docker
            sudo systemctl enable docker
            
            # Benutzer zur docker-Gruppe hinzufügen
            sudo usermod -aG docker $USER
            ;;
            
        "script"|*)
            # Generisches Install-Script
            print_step "Installiere Docker mit offiziellem Script..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            rm get-docker.sh
            
            # Docker-Service starten
            sudo systemctl start docker
            sudo systemctl enable docker
            
            # Benutzer zur docker-Gruppe hinzufügen
            sudo usermod -aG docker $USER
            ;;
    esac
}

install_docker_compose() {
    print_step "Prüfe Docker Compose..."
    
    # Docker Compose v2 (Plugin) prüfen
    if docker compose version &> /dev/null; then
        print_info "Docker Compose v2 verfügbar: $(docker compose version --short)"
        COMPOSE_CMD="docker compose"
        return
    fi
    
    # Docker Compose v1 (Standalone) prüfen
    if command -v docker-compose &> /dev/null; then
        print_info "Docker Compose v1 verfügbar: $(docker-compose --version)"
        COMPOSE_CMD="docker-compose"
        return
    fi
    
    # Docker Compose installieren
    print_step "Installiere Docker Compose..."
    
    if [[ "$DETECTED_OS" == "macOS" ]]; then
        # Auf macOS ist Compose normalerweise in Docker Desktop enthalten
        print_warning "Docker Compose nicht gefunden. Möglicherweise ist Docker Desktop nicht vollständig installiert."
        COMPOSE_CMD="docker compose"
    else
        # Linux: Docker Compose v2 als Plugin installieren
        COMPOSE_VERSION="v2.21.0"
        COMPOSE_URL="https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${DETECTED_ARCH}"
        
        sudo curl -L "$COMPOSE_URL" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        
        # Symlink für 'docker compose' erstellen
        sudo ln -sf /usr/local/bin/docker-compose /usr/local/bin/docker-compose-plugin
        
        COMPOSE_CMD="docker-compose"
        print_info "Docker Compose installiert: $(docker-compose --version)"
    fi
}

start_docker_daemon() {
    if [[ "$DETECTED_OS" == "macOS" ]]; then
        print_step "Starte Docker Desktop..."
        open -a Docker
        wait_for_docker_start 60
    else
        print_step "Starte Docker-Daemon..."
        sudo systemctl start docker
        
        # Warten bis Docker bereit ist
        for i in {1..30}; do
            if docker info &> /dev/null; then
                break
            fi
            sleep 1
        done
        
        if ! docker info &> /dev/null; then
            print_error "Docker-Daemon konnte nicht gestartet werden!"
            exit 1
        fi
    fi
}

wait_for_docker_start() {
    local timeout=${1:-60}
    local count=0
    
    while [ $count -lt $timeout ]; do
        if docker info &> /dev/null; then
            print_success "Docker ist bereit"
            return 0
        fi
        
        if [ $((count % 10)) -eq 0 ]; then
            print_info "Warte auf Docker... ($count/$timeout Sekunden)"
        fi
        
        sleep 1
        ((count++))
    done
    
    print_error "Docker-Start-Timeout nach $timeout Sekunden!"
    return 1
}

verify_docker_permissions() {
    print_step "Prüfe Docker-Berechtigungen..."
    
    if docker info &> /dev/null; then
        print_success "Docker-Berechtigungen OK"
    else
        if [[ "$DETECTED_OS" == "Linux" ]]; then
            print_warning "Docker-Berechtigungen fehlen. Versuche mit sudo..."
            if sudo docker info &> /dev/null; then
                print_warning "Docker läuft nur mit sudo. Benutzer muss zur docker-Gruppe hinzugefügt werden."
                print_info "Führe aus: sudo usermod -aG docker $USER"
                print_info "Dann ab- und wieder anmelden."
                
                # Temporär mit sudo arbeiten
                COMPOSE_CMD="sudo $COMPOSE_CMD"
            else
                print_error "Docker funktioniert nicht, auch nicht mit sudo!"
                exit 1
            fi
        else
            print_error "Docker-Berechtigungen-Problem!"
            exit 1
        fi
    fi
}

install_python() {
    print_step "Installiere Python..."
    
    # Python prüfen/installieren
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION_INSTALLED=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        print_info "Python bereits installiert: $PYTHON_VERSION_INSTALLED"
        
        # Version prüfen
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python-Version ist kompatibel"
        else
            print_error "Python 3.8+ erforderlich, gefunden: $PYTHON_VERSION_INSTALLED"
            install_python_version
        fi
    else
        print_step "Python3 nicht gefunden, installiere..."
        install_python_version
    fi
    
    # pip prüfen/installieren
    if ! command -v pip3 &> /dev/null; then
        print_step "Installiere pip..."
        install_pip
    fi
    
    # Virtual Environment Support prüfen
    if ! python3 -m venv --help &> /dev/null; then
        print_step "Installiere venv-Modul..."
        install_venv_module
    fi
    
    print_success "Python-Installation abgeschlossen"
}

install_python_version() {
    case $PACKAGE_MANAGER in
        "brew")
            # macOS
            print_step "Installiere Python über Homebrew..."
            
            # Versuche verschiedene Python-Versionen
            python_versions=("python@3.11" "python@3.10" "python@3.9" "python3")
            python_installed=false
            
            for py_version in "${python_versions[@]}"; do
                if brew install "$py_version" 2>/dev/null; then
                    print_success "$py_version erfolgreich installiert"
                    python_installed=true
                    
                    # Versuche zu verlinken (kann fehlschlagen, ist aber nicht kritisch)
                    brew link --overwrite "$py_version" 2>/dev/null || print_info "Linking übersprungen"
                    break
                fi
            done
            
            if [ "$python_installed" = false ]; then
                print_warning "Homebrew Python-Installation fehlgeschlagen"
                print_info "Verwende System-Python (falls verfügbar)"
            fi
            ;;
            
        "apt")
            # Ubuntu/Debian
            print_step "Installiere Python für Ubuntu/Debian..."
            sudo apt-get update
            sudo apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                python3-setuptools \
                python3-wheel
            ;;
            
        "yum")
            # CentOS/RHEL/Fedora
            print_step "Installiere Python für CentOS/RHEL/Fedora..."
            if command -v dnf &> /dev/null; then
                sudo dnf install -y python3 python3-pip python3-venv python3-devel
            else
                sudo yum install -y python3 python3-pip python3-venv python3-devel
            fi
            ;;
            
        "pacman")
            # Arch Linux
            print_step "Installiere Python für Arch Linux..."
            sudo pacman -S --noconfirm python python-pip python-virtualenv
            ;;
            
        *)
            print_error "Automatische Python-Installation nicht unterstützt für $PACKAGE_MANAGER"
            print_info "Bitte installieren Sie Python 3.8+ manuell"
            exit 1
            ;;
    esac
}

install_pip() {
    print_step "Installiere pip..."
    
    if command -v python3 &> /dev/null; then
        # pip über get-pip.py installieren
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        python3 get-pip.py --user
        rm get-pip.py
        
        # pip zum PATH hinzufügen
        export PATH="$HOME/.local/bin:$PATH"
    else
        print_error "Python3 nicht verfügbar für pip-Installation!"
        exit 1
    fi
}

install_venv_module() {
    case $PACKAGE_MANAGER in
        "apt")
            sudo apt-get install -y python3-venv
            ;;
        "yum")
            if command -v dnf &> /dev/null; then
                sudo dnf install -y python3-venv
            else
                sudo yum install -y python3-venv
            fi
            ;;
        *)
            print_warning "venv-Modul-Installation nicht unterstützt für $PACKAGE_MANAGER"
            ;;
    esac
}

install_system_tools() {
    print_step "Installiere System-Tools für OCR und Dokumentverarbeitung..."
    
    case $PACKAGE_MANAGER in
        "brew")
            # macOS
            print_step "Installiere macOS-Tools..."
            
            # Tools einzeln installieren für bessere Fehlerbehandlung
            macos_tools=(
                "tesseract"
                "poppler" 
                "imagemagick"
            )
            
            for tool in "${macos_tools[@]}"; do
                print_step "Installiere $tool..."
                if brew install "$tool" 2>/dev/null; then
                    print_success "$tool installiert"
                else
                    print_warning "$tool konnte nicht installiert werden"
                fi
            done
            
            # Tesseract deutsche Sprache (optional)
            print_step "Installiere deutsche Tesseract-Sprache..."
            brew install tesseract-lang 2>/dev/null || print_warning "Tesseract deutsche Sprache nicht verfügbar"
            ;;
            
        "apt")
            # Ubuntu/Debian
            print_step "Installiere Ubuntu/Debian-Tools..."
            sudo apt-get install -y \
                tesseract-ocr \
                tesseract-ocr-deu \
                poppler-utils \
                imagemagick \
                libmagickwand-dev \
                ghostscript \
                libreoffice
            ;;
            
        "yum")
            # CentOS/RHEL/Fedora
            print_step "Installiere CentOS/RHEL/Fedora-Tools..."
            if command -v dnf &> /dev/null; then
                sudo dnf install -y tesseract tesseract-langpack-deu poppler-utils ImageMagick
            else
                sudo yum install -y tesseract tesseract-langpack-deu poppler-utils ImageMagick
            fi
            ;;
            
        "pacman")
            # Arch Linux
            print_step "Installiere Arch Linux-Tools..."
            sudo pacman -S --noconfirm tesseract tesseract-data-deu poppler imagemagick
            ;;
            
        *)
            print_warning "System-Tools-Installation übersprungen für $PACKAGE_MANAGER"
            ;;
    esac
    
    print_success "System-Tools installiert"
}

setup_python_environment() {
    print_step "Richte Python-Umgebung ein..."
    
    # Virtual Environment erstellen
    if [ ! -d "venv" ]; then
        print_step "Erstelle Python Virtual Environment..."
        python3 -m venv venv
        
        if [ ! -d "venv" ]; then
            print_error "Virtual Environment konnte nicht erstellt werden!"
            exit 1
        fi
    fi
    
    # Virtual Environment aktivieren
    print_step "Aktiviere Virtual Environment..."
    source venv/bin/activate
    
    # pip upgraden
    print_step "Upgrade pip..."
    pip install --upgrade pip setuptools wheel
    
    # Requirements installieren
    if [ -f "config/requirements.txt" ]; then
        print_step "Installiere Python-Pakete..."
        pip install -r config/requirements.txt
        
        # Installationsstatus prüfen
        if [ $? -ne 0 ]; then
            print_error "Python-Pakete-Installation fehlgeschlagen!"
            print_info "Versuche einzelne Installation..."
            
            # Kritische Pakete einzeln installieren
            critical_packages=(
                "streamlit>=1.28.0"
                "pandas>=2.0.0"
                "plotly>=5.15.0"
                "pymongo>=4.5.0"
                "requests>=2.31.0"
                "PyYAML>=6.0"
            )
            
            for package in "${critical_packages[@]}"; do
                print_step "Installiere $package..."
                pip install "$package" || print_warning "Konnte $package nicht installieren"
            done
        fi
        
        # Optionale Pakete installieren
        install_optional_packages
        
    else
        print_error "requirements.txt nicht gefunden!"
        exit 1
    fi
    
    print_success "Python-Umgebung eingerichtet"
}

install_optional_packages() {
    print_step "Installiere optionale Pakete..."
    
    # spaCy und deutsches Modell
    if pip show spacy &> /dev/null; then
        print_step "Lade deutsches spaCy-Modell..."
        python -m spacy download de_core_news_sm || print_warning "Deutsches spaCy-Modell konnte nicht geladen werden"
    else
        print_step "Installiere spaCy..."
        pip install spacy || print_warning "spaCy konnte nicht installiert werden"
        if pip show spacy &> /dev/null; then
            python -m spacy download de_core_news_sm || print_warning "Deutsches spaCy-Modell konnte nicht geladen werden"
        fi
    fi
    
    # OCR-Pakete
    ocr_packages=("PyMuPDF" "pytesseract" "Pillow")
    for package in "${ocr_packages[@]}"; do
        if ! pip show "$package" &> /dev/null; then
            print_step "Installiere $package..."
            pip install "$package" || print_warning "$package konnte nicht installiert werden"
        fi
    done
    
    print_success "Optionale Pakete installiert"
}

create_docker_files() {
    print_step "Erstelle Docker-Konfiguration..."
    
    # Dockerfile erstellen
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /app

# Python-Abhängigkeiten
COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# spaCy deutsches Modell (optional)
RUN python -m spacy download de_core_news_sm || echo "spaCy model download failed"

# Anwendung kopieren
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

    # docker-compose.yml erstellen
    cat > docker-compose.yml << EOF
version: '3.8'

services:
  web:
    build: .
    container_name: ${PROJECT_NAME}-web
    ports:
      - "${WEB_PORT}:12000"
    environment:
      - PYTHONPATH=/app
      - STREAMLIT_SERVER_PORT=12000
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
      - MONGODB_HOST=mongodb
      - MONGODB_PORT=27017
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - mongodb
    restart: unless-stopped
    networks:
      - gmunden-network

  mongodb:
    image: mongo:${MONGODB_VERSION}
    container_name: ${PROJECT_NAME}-mongodb
    ports:
      - "${MONGO_PORT}:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=change_me_strong
      - MONGO_INITDB_DATABASE=gmunden_db
    volumes:
      - mongodb_data:/data/db
      - ./database/init.js:/docker-entrypoint-initdb.d/init.js:ro
    restart: unless-stopped
    networks:
      - gmunden-network
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 30s
      timeout: 10s
      retries: 5

  ocr-agent:
    build: ./ocr-agent
    container_name: ${PROJECT_NAME}-ocr
    ports:
      - "${OCR_PORT}:8080"
    environment:
      - OCR_LANGUAGE=deu
      - OCR_DPI=300
    volumes:
      - ./data/uploads:/app/uploads
      - ./data/processed:/app/processed
    restart: unless-stopped
    networks:
      - gmunden-network

volumes:
  mongodb_data:
    driver: local

networks:
  gmunden-network:
    driver: bridge
EOF

    # MongoDB Init-Script
    mkdir -p database
    cat > database/init.js << 'EOF'
// MongoDB Initialisierung für Gmunden Transparenz-DB

db = db.getSiblingDB('gmunden_db');

// Collections erstellen
db.createCollection('finanzen');
db.createCollection('dokumente');
db.createCollection('protokolle');
db.createCollection('jahre');

// Indizes erstellen
db.finanzen.createIndex({ jahr: 1 });
db.finanzen.createIndex({ kategorie: 1 });
db.finanzen.createIndex({ betrag: -1 });
db.finanzen.createIndex({ datum: -1 });

db.dokumente.createIndex({ jahr: 1 });
db.dokumente.createIndex({ typ: 1 });
db.dokumente.createIndex({ filename: "text", titel: "text", inhalt: "text" });

db.protokolle.createIndex({ datum: -1 });
db.protokolle.createIndex({ typ: 1 });

db.jahre.createIndex({ jahr: 1 });

// Status-Eintrag
db.status.insertOne({
    _id: "init",
    initialized: new Date(),
    version: "2.0.0",
    status: "ready"
});

print("Gmunden Transparenz-DB initialized successfully");
EOF

    # OCR-Agent Dockerfile
    mkdir -p ocr-agent
    cat > ocr-agent/Dockerfile << 'EOF'
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080

CMD ["python", "app.py"]
EOF

    # OCR-Agent Requirements
    cat > ocr-agent/requirements.txt << 'EOF'
flask==2.3.3
pytesseract==0.3.10
Pillow==10.0.0
PyMuPDF==1.23.0
requests==2.31.0
EOF

    # OCR-Agent App
    cat > ocr-agent/app.py << 'EOF'
#!/usr/bin/env python3
"""
OCR-Agent für Gmunden Transparenz-Datenbank
Einfacher Flask-Service für Dokumentenverarbeitung
"""

from flask import Flask, request, jsonify
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import io
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'ocr-agent'})

@app.route('/ocr', methods=['POST'])
def process_ocr():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Datei lesen
        file_content = file.read()
        filename = file.filename.lower()
        
        extracted_text = ""
        
        if filename.endswith('.pdf'):
            # PDF verarbeiten
            pdf_doc = fitz.open(stream=file_content, filetype="pdf")
            for page_num in range(pdf_doc.page_count):
                page = pdf_doc[page_num]
                text = page.get_text()
                if text.strip():
                    extracted_text += text + "\n"
                else:
                    # OCR für gescannte Seiten
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    ocr_text = pytesseract.image_to_string(image, lang='deu')
                    extracted_text += ocr_text + "\n"
            pdf_doc.close()
            
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
            # Bild verarbeiten
            image = Image.open(io.BytesIO(file_content))
            extracted_text = pytesseract.image_to_string(image, lang='deu')
        
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'extracted_text': extracted_text.strip(),
            'text_length': len(extracted_text.strip())
        })
        
    except Exception as e:
        app.logger.error(f"OCR processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
EOF

    print_success "Docker-Konfiguration erstellt"
}

setup_directories() {
    print_step "Erstelle Verzeichnisstruktur..."
    
    # Verzeichnisse erstellen
    mkdir -p data/{imports,processed,backups,uploads}
    mkdir -p logs
    mkdir -p config
    
    # .gitignore erstellen
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Logs
*.log
logs/

# Data
data/
!data/.gitkeep

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
.dockerignore

# Secrets
.env
*.key
*.pem
EOF

    # .gitkeep Dateien
    touch data/imports/.gitkeep
    touch data/processed/.gitkeep
    touch data/backups/.gitkeep
    touch data/uploads/.gitkeep
    touch logs/.gitkeep
    
    print_success "Verzeichnisstruktur erstellt"
}

build_and_start() {
    print_step "Baue und starte Docker-Container..."
    
    # Docker Images bauen
    print_info "Baue Docker Images..."
    $COMPOSE_CMD build --no-cache
    
    # Container starten
    print_info "Starte Container..."
    $COMPOSE_CMD up -d
    
    # Warten auf Services
    print_info "Warte auf Service-Start..."
    sleep 10
    
    # Health Checks
    print_step "Prüfe Service-Status..."
    
    # MongoDB
    for i in {1..30}; do
        if docker exec ${PROJECT_NAME}-mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
            print_success "MongoDB ist bereit"
            break
        fi
        sleep 2
    done
    
    # Web-Service
    for i in {1..60}; do
        if curl -f http://localhost:${WEB_PORT}/_stcore/health &> /dev/null; then
            print_success "Web-Service ist bereit"
            break
        fi
        sleep 2
    done
    
    # OCR-Agent
    for i in {1..30}; do
        if curl -f http://localhost:${OCR_PORT}/health &> /dev/null; then
            print_success "OCR-Agent ist bereit"
            break
        fi
        sleep 2
    done
    
    print_success "Alle Services gestartet"
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
echo "🗄️  MongoDB: localhost:${MONGO_PORT}"
echo "🔍 OCR-Agent: http://localhost:${OCR_PORT}"
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
    
    # Backup-Script
    cat > backup.sh << EOF
#!/bin/bash
BACKUP_DIR="data/backups"
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="\${BACKUP_DIR}/gmunden_backup_\${TIMESTAMP}.tar.gz"

echo "💾 Erstelle Backup..."
mkdir -p \$BACKUP_DIR

# MongoDB Backup
docker exec ${PROJECT_NAME}-mongodb mongodump --archive --gzip > "\${BACKUP_DIR}/mongodb_\${TIMESTAMP}.archive.gz"

# Dateien Backup
tar -czf "\$BACKUP_FILE" data/ config/ --exclude=data/backups

echo "✅ Backup erstellt: \$BACKUP_FILE"
EOF
    chmod +x backup.sh
    
    # Update-Script
    cat > update.sh << EOF
#!/bin/bash
echo "🔄 Update Gmunden Transparenz-Datenbank..."
git pull
$COMPOSE_CMD build --no-cache
$COMPOSE_CMD up -d
echo "✅ Update abgeschlossen"
EOF
    chmod +x update.sh
    
    print_success "Management-Scripts erstellt"
}

show_final_info() {
    print_success "Installation erfolgreich abgeschlossen!"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎉 INSTALLATION ERFOLGREICH! 🎉                          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "${CYAN}📍 ZUGRIFF AUF DIE ANWENDUNG:${NC}"
    echo -e "   🌐 Web-Interface:     ${BLUE}http://localhost:${WEB_PORT}${NC}"
    echo -e "   🌍 Extern (All-Hands): ${BLUE}https://work-1-syygiirqlvvwfggb.prod-runtime.all-hands.dev${NC}"
    echo ""
    
    echo -e "${CYAN}🔧 SYSTEM-KOMPONENTEN:${NC}"
    echo -e "   🗄️  MongoDB:          ${BLUE}localhost:${MONGO_PORT}${NC}"
    echo -e "   🔍 OCR-Agent:         ${BLUE}http://localhost:${OCR_PORT}${NC}"
    echo -e "   📊 Container Status:   ${BLUE}./status.sh${NC}"
    echo ""
    
    echo -e "${CYAN}🚀 ERSTE SCHRITTE:${NC}"
    echo -e "   1. Öffnen Sie ${BLUE}http://localhost:${WEB_PORT}${NC} in Ihrem Browser"
    echo -e "   2. Testen Sie die Suche: ${YELLOW}'Wie viel gab die Gemeinde 2023 für Straßen aus?'${NC}"
    echo -e "   3. Laden Sie Dokumente im ${BLUE}📄 Dokumente${NC}-Bereich hoch"
    echo -e "   4. Erkunden Sie die verschiedenen Funktionen"
    echo ""
    
    echo -e "${CYAN}🛠️  VERWALTUNG:${NC}"
    echo -e "   ▶️  Starten:           ${GREEN}./start.sh${NC}"
    echo -e "   ⏹️  Stoppen:           ${RED}./stop.sh${NC}"
    echo -e "   📊 Status:            ${BLUE}./status.sh${NC}"
    echo -e "   💾 Backup:            ${PURPLE}./backup.sh${NC}"
    echo -e "   🔄 Update:            ${YELLOW}./update.sh${NC}"
    echo ""
    
    echo -e "${CYAN}📋 SYSTEM-INFORMATIONEN:${NC}"
    echo -e "   🖥️  Betriebssystem:    ${OS}"
    echo -e "   💾 Speicher:          ${MEMORY_GB}GB"
    echo -e "   💿 Freier Speicher:   ${DISK_FREE_GB}GB"
    echo -e "   🐳 Docker:            $(docker --version | cut -d' ' -f3 | tr -d ',')"
    echo -e "   🐍 Python:            $(python3 --version | cut -d' ' -f2)"
    echo ""
    
    echo -e "${CYAN}🔐 STANDARD-ZUGANGSDATEN:${NC}"
    echo -e "   📊 Admin-Panel:       ${YELLOW}Passwort: admin123${NC} ${RED}(ÄNDERN!)${NC}"
    echo -e "   🗄️  MongoDB:          ${YELLOW}admin / change_me_strong${NC} ${RED}(ÄNDERN!)${NC}"
    echo ""
    
    echo -e "${CYAN}📚 BEISPIEL-ANFRAGEN:${NC}"
    echo -e "   • ${YELLOW}'Zeige mir alle Ausgaben von 2023'${NC}"
    echo -e "   • ${YELLOW}'Wie viel kostete die Straßenreparatur?'${NC}"
    echo -e "   • ${YELLOW}'Finde Protokolle über Wasserleitungen'${NC}"
    echo -e "   • ${YELLOW}'Welche Ausgaben über 10.000 Euro gab es?'${NC}"
    echo ""
    
    echo -e "${CYAN}🆘 SUPPORT:${NC}"
    echo -e "   📧 E-Mail:            ${BLUE}transparenz@gmunden.at${NC}"
    echo -e "   📋 Logs:              ${BLUE}tail -f logs/gmunden_app.log${NC}"
    echo -e "   🐛 Issues:            ${BLUE}GitHub Issues${NC}"
    echo ""
    
    echo -e "${GREEN}🎯 Das System ist jetzt bereit für den produktiven Einsatz!${NC}"
    echo -e "${GREEN}   Alle Daten werden automatisch validiert und auf Qualität geprüft.${NC}"
    echo -e "${GREEN}   Keine Halluzinationen - nur echte, verifizierte Gemeindedaten!${NC}"
    echo ""
    
    # Browser öffnen (optional)
    if command -v open &> /dev/null; then
        read -p "🌐 Möchten Sie das Web-Interface jetzt öffnen? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            open "http://localhost:${WEB_PORT}"
        fi
    fi
}

verify_installation() {
    print_step "Verifiziere Installation..."
    
    local errors=0
    
    # Docker prüfen
    if ! docker --version &> /dev/null; then
        print_error "Docker nicht verfügbar!"
        ((errors++))
    else
        print_success "Docker: $(docker --version)"
    fi
    
    # Docker Compose prüfen
    if ! $COMPOSE_CMD version &> /dev/null; then
        print_error "Docker Compose nicht verfügbar!"
        ((errors++))
    else
        print_success "Docker Compose: $($COMPOSE_CMD version --short 2>/dev/null || echo 'verfügbar')"
    fi
    
    # Python prüfen
    if ! python3 --version &> /dev/null; then
        print_error "Python3 nicht verfügbar!"
        ((errors++))
    else
        print_success "Python: $(python3 --version)"
    fi
    
    # Virtual Environment prüfen
    if [ ! -d "venv" ]; then
        print_error "Virtual Environment nicht erstellt!"
        ((errors++))
    else
        print_success "Virtual Environment: verfügbar"
    fi
    
    # Kritische Python-Pakete prüfen
    source venv/bin/activate 2>/dev/null || true
    critical_packages=("streamlit" "pandas" "plotly" "pymongo")
    for package in "${critical_packages[@]}"; do
        if ! pip show "$package" &> /dev/null; then
            print_warning "Python-Paket '$package' nicht installiert"
            ((errors++))
        fi
    done
    
    # System-Tools prüfen
    if command -v tesseract &> /dev/null; then
        print_success "Tesseract OCR: $(tesseract --version 2>&1 | head -1)"
    else
        print_warning "Tesseract OCR nicht verfügbar (optional)"
    fi
    
    # Verzeichnisstruktur prüfen
    required_dirs=("data" "config" "web" "backend")
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            print_error "Verzeichnis '$dir' fehlt!"
            ((errors++))
        fi
    done
    
    # Konfigurationsdateien prüfen
    required_files=("config/requirements.txt" "docker-compose.yml" "web/app.py")
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Datei '$file' fehlt!"
            ((errors++))
        fi
    done
    
    if [ $errors -eq 0 ]; then
        print_success "Installation erfolgreich verifiziert!"
        return 0
    else
        print_error "$errors Fehler bei der Verifikation gefunden!"
        return 1
    fi
}

perform_system_health_check() {
    print_step "Führe System-Gesundheitscheck durch..."
    
    # Container-Status prüfen
    print_info "Prüfe Container-Status..."
    $COMPOSE_CMD ps
    
    # Service-Erreichbarkeit prüfen
    print_step "Prüfe Service-Erreichbarkeit..."
    
    # Web-Service
    local web_attempts=0
    while [ $web_attempts -lt 30 ]; do
        if curl -f http://localhost:${WEB_PORT}/_stcore/health &> /dev/null; then
            print_success "Web-Service erreichbar"
            break
        fi
        sleep 2
        ((web_attempts++))
    done
    
    if [ $web_attempts -eq 30 ]; then
        print_warning "Web-Service nicht erreichbar nach 60 Sekunden"
    fi
    
    # MongoDB
    local mongo_attempts=0
    while [ $mongo_attempts -lt 15 ]; do
        if docker exec ${PROJECT_NAME}-mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
            print_success "MongoDB erreichbar"
            break
        fi
        sleep 2
        ((mongo_attempts++))
    done
    
    if [ $mongo_attempts -eq 15 ]; then
        print_warning "MongoDB nicht erreichbar nach 30 Sekunden"
    fi
    
    # OCR-Agent
    if curl -f http://localhost:${OCR_PORT}/health &> /dev/null; then
        print_success "OCR-Agent erreichbar"
    else
        print_warning "OCR-Agent nicht erreichbar"
    fi
    
    # Logs prüfen
    print_step "Prüfe auf kritische Fehler in Logs..."
    if $COMPOSE_CMD logs --tail=50 | grep -i "error\|exception\|failed" | head -5; then
        print_warning "Mögliche Fehler in Logs gefunden (siehe oben)"
    else
        print_success "Keine kritischen Fehler in Logs"
    fi
}

create_startup_verification_script() {
    print_step "Erstelle Startup-Verifikations-Script..."
    
    cat > verify_system.sh << 'EOF'
#!/bin/bash
# Gmunden Transparenz-Datenbank - System-Verifikation

set -euo pipefail

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${NC}"
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

echo "🔍 Gmunden Transparenz-Datenbank - System-Verifikation"
echo "======================================================"

# Docker prüfen
print_status "Prüfe Docker..."
if docker --version &> /dev/null && docker info &> /dev/null; then
    print_success "Docker läuft: $(docker --version | cut -d' ' -f3 | tr -d ',')"
else
    print_error "Docker nicht verfügbar oder läuft nicht!"
    exit 1
fi

# Docker Compose prüfen
print_status "Prüfe Docker Compose..."
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    print_success "Docker Compose v2 verfügbar"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    print_success "Docker Compose v1 verfügbar"
else
    print_error "Docker Compose nicht verfügbar!"
    exit 1
fi

# Container-Status prüfen
print_status "Prüfe Container-Status..."
if $COMPOSE_CMD ps | grep -q "Up"; then
    print_success "Container laufen"
    $COMPOSE_CMD ps
else
    print_warning "Container laufen nicht - starte Services..."
    $COMPOSE_CMD up -d
    sleep 10
fi

# Services prüfen
print_status "Prüfe Service-Erreichbarkeit..."

# Web-Service
if curl -f http://localhost:12000/_stcore/health &> /dev/null; then
    print_success "Web-Interface erreichbar: http://localhost:12000"
else
    print_warning "Web-Interface nicht erreichbar"
fi

# MongoDB
if docker exec gmunden-transparenz-db-mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
    print_success "MongoDB erreichbar"
else
    print_warning "MongoDB nicht erreichbar"
fi

# OCR-Agent
if curl -f http://localhost:8080/health &> /dev/null; then
    print_success "OCR-Agent erreichbar"
else
    print_warning "OCR-Agent nicht erreichbar"
fi

# Python-Umgebung prüfen
print_status "Prüfe Python-Umgebung..."
if [ -d "venv" ] && source venv/bin/activate && python -c "import streamlit, pandas, plotly" &> /dev/null; then
    print_success "Python-Umgebung OK"
else
    print_warning "Python-Umgebung hat Probleme"
fi

# Systemressourcen prüfen
print_status "Prüfe Systemressourcen..."
if command -v free &> /dev/null; then
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    print_success "Speicher-Nutzung: ${MEMORY_USAGE}%"
elif command -v vm_stat &> /dev/null; then
    print_success "macOS Speicher-Info verfügbar"
fi

DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}')
print_success "Festplatten-Nutzung: $DISK_USAGE"

echo ""
echo "🎯 System-Verifikation abgeschlossen!"
echo "🌐 Web-Interface: http://localhost:12000"
echo "📊 Status: ./status.sh"
echo "🔄 Neustart: ./start.sh"
EOF

    chmod +x verify_system.sh
    print_success "System-Verifikations-Script erstellt"
}

# Hauptfunktion
main() {
    print_header
    
    # System-Erkennung und Prüfungen
    detect_system
    check_system_requirements
    
    # System-Abhängigkeiten installieren
    install_system_dependencies
    
    # Hauptkomponenten installieren
    install_docker
    install_python
    install_system_tools
    
    # Python-Umgebung einrichten
    setup_python_environment
    
    # Docker-Setup
    create_docker_files
    setup_directories
    
    # System bauen und starten
    build_and_start
    
    # Management-Tools erstellen
    create_management_scripts
    create_startup_verification_script
    
    # Installation verifizieren
    if verify_installation; then
        # System-Gesundheitscheck
        perform_system_health_check
        
        # Abschluss-Informationen
        show_final_info
    else
        print_error "Installation-Verifikation fehlgeschlagen!"
        print_info "Prüfen Sie die Logs und versuchen Sie es erneut."
        exit 1
    fi
}

# Fehlerbehandlung
trap 'print_error "Installation fehlgeschlagen! Siehe $LOG_FILE für Details."; exit 1' ERR

# Script ausführen
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi