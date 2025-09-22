#!/bin/bash
# 🍎 Gmunden Transparenz-System - M3 Silicon Optimiert
# Automatischer Start mit Performance-Optimierungen

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🍎 Gmunden Transparenz-System für M3 Silicon${NC}"
echo -e "${BLUE}================================================${NC}"

# System-Info
echo -e "${YELLOW}📊 System-Information:${NC}"
echo "   macOS: $(sw_vers -productVersion)"
echo "   Chip: $(sysctl -n machdep.cpu.brand_string)"
echo "   Python: $(python3 --version 2>/dev/null || echo 'Nicht gefunden')"
echo "   Arbeitsverzeichnis: $(pwd)"
echo ""

# Voraussetzungen prüfen
echo -e "${YELLOW}🔍 Voraussetzungen prüfen...${NC}"

# Python prüfen
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 nicht gefunden!${NC}"
    echo "   Installieren Sie Python mit: brew install python@3.11"
    exit 1
fi

# Virtual Environment prüfen/erstellen
if [ ! -d "venv_gmunden" ]; then
    echo -e "${YELLOW}📦 Erstelle Virtual Environment...${NC}"
    python3 -m venv venv_gmunden
fi

# Virtual Environment aktivieren
echo -e "${YELLOW}🔧 Aktiviere Virtual Environment...${NC}"
source venv_gmunden/bin/activate

# Pip upgraden
echo -e "${YELLOW}⬆️ Upgrade pip...${NC}"
pip install --upgrade pip setuptools wheel --quiet

# Abhängigkeiten prüfen/installieren
echo -e "${YELLOW}📚 Prüfe Abhängigkeiten...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
else
    echo -e "${YELLOW}📦 Installiere Core-Abhängigkeiten...${NC}"
    pip install streamlit plotly pandas numpy pyyaml requests python-dateutil pillow --quiet
fi

# M3 Silicon Optimierungen
echo -e "${YELLOW}🚀 M3 Silicon Optimierungen...${NC}"
export OPENBLAS_NUM_THREADS=8
export MKL_NUM_THREADS=8
export OMP_NUM_THREADS=8
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200

# Verzeichnisse erstellen
echo -e "${YELLOW}📁 Erstelle Verzeichnisse...${NC}"
mkdir -p data/{cache,backup,uploads,exports}
mkdir -p logs
mkdir -p .streamlit

# Streamlit-Konfiguration für M3
echo -e "${YELLOW}⚙️ Konfiguriere Streamlit...${NC}"
cat > .streamlit/config.toml << 'EOF'
[server]
port = 12000
address = "localhost"
maxUploadSize = 200
headless = false
enableCORS = true
enableXsrfProtection = false

[browser]
gatherUsageStats = false
serverAddress = "localhost"
serverPort = 12000

[runner]
fastReruns = true
postScriptGC = true
magicEnabled = true

[client]
caching = true
displayEnabled = true

[theme]
primaryColor = "#2e7d32"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[global]
developmentMode = false
logLevel = "info"
EOF

# Port prüfen
echo -e "${YELLOW}🔌 Prüfe Port 12000...${NC}"
if lsof -Pi :12000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}⚠️ Port 12000 ist bereits belegt!${NC}"
    echo "   Beende bestehende Prozesse..."
    lsof -ti:12000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# System-Check
echo -e "${YELLOW}🧪 System-Test...${NC}"
python3 -c "
try:
    import streamlit, plotly, pandas, numpy, yaml, requests
    print('✅ Alle Module verfügbar')
except ImportError as e:
    print(f'❌ Modul fehlt: {e}')
    exit(1)
" || exit 1

# Logs-Setup
LOG_FILE="logs/streamlit_$(date +%Y%m%d_%H%M%S).log"
echo -e "${YELLOW}📝 Logs: ${LOG_FILE}${NC}"

# System starten
echo -e "${GREEN}🚀 Starte Gmunden Transparenz-System...${NC}"
echo ""
echo -e "${BLUE}📊 System-URLs:${NC}"
echo "   🌐 Haupt-Interface: http://localhost:12000"
echo "   🔐 Admin-Bereich: http://localhost:12000 (Passwort: admin123)"
echo "   📋 Logs: tail -f ${LOG_FILE}"
echo ""
echo -e "${YELLOW}💡 Tipps:${NC}"
echo "   • Strg+C zum Beenden"
echo "   • Browser öffnet automatisch"
echo "   • Admin-Passwort: admin123"
echo ""

# Streamlit starten
streamlit run web/app.py \
    --server.port 12000 \
    --server.address localhost \
    --server.headless false \
    --browser.gatherUsageStats false \
    --logger.level info \
    2>&1 | tee "${LOG_FILE}" &

STREAMLIT_PID=$!

# Warten bis Server bereit ist
echo -e "${YELLOW}⏳ Warte auf Server-Start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:12000 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Server ist bereit!${NC}"
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

# Browser öffnen (optional)
if command -v open &> /dev/null; then
    echo -e "${YELLOW}🌐 Öffne Browser...${NC}"
    sleep 2
    open http://localhost:12000
fi

# Status-Monitoring
echo -e "${GREEN}🎉 System läuft erfolgreich!${NC}"
echo ""
echo -e "${BLUE}📊 System-Status:${NC}"
echo "   PID: ${STREAMLIT_PID}"
echo "   Port: 12000"
echo "   URL: http://localhost:12000"
echo "   Logs: ${LOG_FILE}"
echo ""

# Cleanup-Funktion
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Beende System...${NC}"
    kill $STREAMLIT_PID 2>/dev/null || true
    echo -e "${GREEN}✅ System beendet.${NC}"
    exit 0
}

# Signal-Handler
trap cleanup SIGINT SIGTERM

# Warten auf Beendigung
echo -e "${YELLOW}💡 Drücken Sie Strg+C zum Beenden${NC}"
wait $STREAMLIT_PID

echo -e "${GREEN}✅ System beendet.${NC}"