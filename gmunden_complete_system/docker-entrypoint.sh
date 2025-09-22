#!/bin/bash
# 🐳 Docker Entrypoint für Gmunden Transparenz-System

set -e

# Farben für Logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🐳 Gmunden Transparenz-System Docker Container${NC}"
echo -e "${BLUE}===============================================${NC}"

# System-Info
echo -e "${YELLOW}📊 Container-Information:${NC}"
echo "   OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "   Python: $(python --version)"
echo "   User: $(whoami)"
echo "   Working Dir: $(pwd)"
echo ""

# Verzeichnisse prüfen/erstellen
echo -e "${YELLOW}📁 Prüfe Verzeichnisse...${NC}"
mkdir -p data/{cache,backup,uploads,exports}
mkdir -p logs
mkdir -p .streamlit

# Berechtigungen setzen
chmod 755 data/ logs/
chmod 644 data/cache/ data/backup/ data/uploads/ data/exports/ 2>/dev/null || true

# Streamlit-Konfiguration prüfen
if [ ! -f ".streamlit/config.toml" ]; then
    echo -e "${YELLOW}⚙️ Erstelle Streamlit-Konfiguration...${NC}"
    cat > .streamlit/config.toml << 'EOF'
[server]
port = 12000
address = "0.0.0.0"
maxUploadSize = 200
headless = true
enableCORS = true
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#2e7d32"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[global]
developmentMode = false
logLevel = "info"
EOF
fi

# Gesundheitscheck-Endpoint erstellen
echo -e "${YELLOW}🏥 Erstelle Health-Check...${NC}"
mkdir -p /tmp/health
echo "OK" > /tmp/health/status

# Umgebungsvariablen setzen
export PYTHONPATH="${PYTHONPATH}:/app"
export STREAMLIT_SERVER_PORT=${STREAMLIT_SERVER_PORT:-12000}
export STREAMLIT_SERVER_ADDRESS=${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}

# System-Check
echo -e "${YELLOW}🧪 System-Test...${NC}"
python -c "
try:
    import streamlit, plotly, pandas, numpy, yaml, requests
    print('✅ Alle Python-Module verfügbar')
except ImportError as e:
    print(f'❌ Modul fehlt: {e}')
    exit(1)
" || exit 1

# OCR-Test
if command -v tesseract >/dev/null 2>&1; then
    echo "✅ OCR (Tesseract) verfügbar"
else
    echo "⚠️ OCR (Tesseract) nicht verfügbar"
fi

# Startup-Nachricht
echo -e "${GREEN}🚀 Starte Gmunden Transparenz-System...${NC}"
echo ""
echo -e "${BLUE}📊 Container-URLs:${NC}"
echo "   🌐 Haupt-Interface: http://localhost:12000"
echo "   🔐 Admin-Bereich: http://localhost:12000 (Passwort: admin123)"
echo "   🏥 Health-Check: http://localhost:12000/_stcore/health"
echo ""
echo -e "${YELLOW}💡 Container-Informationen:${NC}"
echo "   • Container läuft als User: $(whoami)"
echo "   • Daten-Volume: /app/data"
echo "   • Logs-Volume: /app/logs"
echo "   • Admin-Passwort: admin123"
echo ""

# Log-Datei erstellen
LOG_FILE="logs/container_$(date +%Y%m%d_%H%M%S).log"
touch "$LOG_FILE"

echo -e "${GREEN}✅ Container bereit!${NC}"
echo -e "${YELLOW}📝 Logs: ${LOG_FILE}${NC}"

# Kommando ausführen
exec "$@" 2>&1 | tee "$LOG_FILE"