#!/bin/bash
# Gemeinde Gmunden Transparenz-System Starter
# Optimiert für All-Hands.dev

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktionen
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                🏛️  GEMEINDE GMUNDEN                          ║"
echo "║              TRANSPARENZ-SYSTEM v2.0                        ║"
echo "║                                                              ║"
echo "║              Optimiert für All-Hands.dev                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Projekt-Verzeichnis
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

log_info "Projekt-Verzeichnis: $PROJECT_DIR"

# Prüfe Python-Installation
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 ist nicht installiert!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
log_info "Python Version: $PYTHON_VERSION"

# Erstelle Virtual Environment falls nicht vorhanden
if [ ! -d "venv" ]; then
    log_info "Erstelle Virtual Environment..."
    python3 -m venv venv
    log_success "Virtual Environment erstellt"
fi

# Aktiviere Virtual Environment
log_info "Aktiviere Virtual Environment..."
source venv/bin/activate

# Installiere/Update Dependencies
log_info "Installiere Python-Abhängigkeiten..."
pip install --upgrade pip
pip install -r requirements.txt

# Installiere deutsches spaCy-Modell
log_info "Installiere deutsches NLP-Modell..."
python -m spacy download de_core_news_sm || log_warning "Deutsches spaCy-Modell konnte nicht installiert werden"

# Erstelle notwendige Verzeichnisse
log_info "Erstelle Verzeichnisstruktur..."
mkdir -p {data/uploads,data/exports,logs,temp}

# Prüfe All-Hands.dev Konfiguration
log_info "Prüfe All-Hands.dev Konfiguration..."

# Prüfe verfügbare Ports
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port belegt
    else
        return 0  # Port frei
    fi
}

PRIMARY_PORT=12000
SECONDARY_PORT=12001

if check_port $PRIMARY_PORT; then
    SELECTED_PORT=$PRIMARY_PORT
    log_success "Port $PRIMARY_PORT ist verfügbar"
elif check_port $SECONDARY_PORT; then
    SELECTED_PORT=$SECONDARY_PORT
    log_warning "Port $PRIMARY_PORT belegt, verwende Port $SECONDARY_PORT"
else
    log_error "Beide Ports ($PRIMARY_PORT, $SECONDARY_PORT) sind belegt!"
    exit 1
fi

# Setze Umgebungsvariablen für All-Hands.dev
export STREAMLIT_SERVER_PORT=$SELECTED_PORT
export STREAMLIT_SERVER_ADDRESS="0.0.0.0"
export STREAMLIT_SERVER_ENABLE_CORS=true
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Erstelle .streamlit Konfiguration
mkdir -p .streamlit
cat > .streamlit/config.toml << EOF
[server]
port = $SELECTED_PORT
address = "0.0.0.0"
enableCORS = true
enableXsrfProtection = false
allowedOrigins = ["*"]

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
EOF

log_success "Streamlit-Konfiguration erstellt"

# Prüfe System-Gesundheit
log_info "Führe System-Diagnose durch..."

# Prüfe verfügbaren Speicher
AVAILABLE_MEMORY=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}' 2>/dev/null || echo "N/A")
log_info "Verfügbarer Speicher: ${AVAILABLE_MEMORY}GB"

# Prüfe Festplattenspeicher
AVAILABLE_DISK=$(df -h . | awk 'NR==2{print $4}' 2>/dev/null || echo "N/A")
log_info "Verfügbarer Festplattenspeicher: $AVAILABLE_DISK"

# Erstelle Startup-Log
LOG_FILE="logs/startup_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs

# Starte Anwendung
log_info "Starte Gemeinde Gmunden Transparenz-System..."
log_info "Web-Interface wird verfügbar sein unter:"
log_success "  🌐 Lokal: http://localhost:$SELECTED_PORT"

if [ "$SELECTED_PORT" = "12000" ]; then
    log_success "  🌍 Extern: https://work-1-syygiirqlvvwfggb.prod-runtime.all-hands.dev"
else
    log_success "  🌍 Extern: https://work-2-syygiirqlvvwfggb.prod-runtime.all-hands.dev"
fi

echo ""
log_info "Drücken Sie Ctrl+C zum Beenden"
echo ""

# Starte Streamlit mit Logging
exec streamlit run web/app.py \
    --server.port $SELECTED_PORT \
    --server.address 0.0.0.0 \
    --server.enableCORS true \
    --server.enableXsrfProtection false \
    --browser.gatherUsageStats false \
    2>&1 | tee "$LOG_FILE"