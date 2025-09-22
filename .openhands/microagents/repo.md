# Gmunden Transparenz-Datenbank - Repository Memory

## 1. Projekt-Übersicht
- **Projektname**: Gmunden Transparenz-Datenbank
- **Zweck**: KI-gestütztes Transparenz-System für Gemeindedaten mit deutscher NLP-Suche
- **Framework**: Streamlit mit natürlicher deutscher Sprachverarbeitung
- **Zielgruppe**: Bürgerinnen und Bürger für transparenten Zugang zu Gemeindedaten
- **Besonderheit**: Realitätsbasierte Antworten ohne Halluzinationen

## 2. Repository-Struktur
```
/workspace/project/
├── web/                           # Web-Interface
│   ├── app_simple.py             # Hauptanwendung (ohne spaCy-Abhängigkeit)
│   └── app.py                    # Erweiterte Version (mit spaCy)
├── ai/                           # KI-Module
│   ├── nlp_processor.py          # Deutsche NLP-Verarbeitung
│   └── fact_checker.py           # Realitätsprüfung/Halluzinations-Prävention
├── data/                         # Datenintegration
│   └── data_manager.py           # Universeller Datenmanager
├── tools/                        # Verwaltungstools
│   └── data_import_tool.py       # CLI-Tool für Datenimport
├── config/                       # Konfigurationsdateien
│   ├── all_hands_metadata.json   # All-Hands.dev Metadaten
│   ├── system_settings.yaml      # System-Einstellungen
│   └── import_config_example.yaml # Import-Konfiguration
├── monitoring/                   # Qualitätssicherung
│   └── quality_monitor.py        # Realzeit-Monitoring
├── .streamlit/                   # Streamlit-Konfiguration
│   └── config.toml               # All-Hands.dev optimierte Einstellungen
├── requirements.txt              # Python-Abhängigkeiten
├── start_system.sh              # Automatischer Starter
└── All-Hands.dev Dateien:
    ├── all-hands-dev-metadata.json
    ├── all-hands-dev-system-settings.yaml
    ├── Dockerfile.all-hands-dev
    ├── docker-compose.all-hands-dev.yml
    └── HOW_TO_ADD_TO_ALL_HANDS_DEV.md
```

## 3. All-Hands.dev Konfiguration
- **Primärer Port**: 12000
- **Backup-Port**: 12001
- **Host-Binding**: 0.0.0.0 (wichtig für All-Hands.dev)
- **CORS**: Vollständig aktiviert für externe Zugriffe
- **iFrame-Support**: Aktiviert für Einbettung
- **Metadaten-Datei**: `all-hands-dev-metadata.json` (vollständige Konfiguration)
- **System-Einstellungen**: `all-hands-dev-system-settings.yaml` (detaillierte Parameter)
- **URLs nach Deployment**: 
  - `https://work-1-{workspace-id}.prod-runtime.all-hands.dev`
  - `https://work-2-{workspace-id}.prod-runtime.all-hands.dev`

## 4. Startup-Befehle
### Lokale Entwicklung
```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Einfache Version starten (empfohlen)
streamlit run web/app_simple.py --server.port 12000 --server.address 0.0.0.0 --server.enableCORS true --server.enableXsrfProtection false --browser.gatherUsageStats false

# Erweiterte Version (benötigt spaCy)
pip install spacy
python -m spacy download de_core_news_sm
streamlit run web/app.py --server.port 12000 --server.address 0.0.0.0
```

### Container-Deployment
```bash
# Docker Build
docker build -f Dockerfile.all-hands-dev -t gmunden-transparenz .

# Docker Run
docker run -p 12000:12000 -p 12001:12001 gmunden-transparenz

# Docker Compose
docker-compose -f docker-compose.all-hands-dev.yml up -d
```

### Automatischer Start
```bash
./start_system.sh
```

## 5. Wichtige Features
- **Deutsche NLP-Suche**: Versteht natürliche Sprache ("Wie viel gab die Gemeinde 2023 für Straßen aus?")
- **Datenintegration**: Unterstützt PDF, Excel, CSV, Bilder (mit OCR), JSON, XML
- **Qualitätssicherung**: Fact-Checking verhindert Halluzinationen
- **Responsive Design**: Funktioniert auf Desktop, Tablet, Smartphone
- **Interaktive Visualisierungen**: Balken-, Linien-, Kreisdiagramme mit Plotly
- **Beispiel-Fragen**: Vordefinierte Fragen zum Ausprobieren
- **Suchhistorie**: Automatische Speicherung vorheriger Anfragen
- **Realzeit-Qualitätsmonitoring**: Kontinuierliche Datenvalidierung

## 6. Deployment-Informationen
### Umgebungsvariablen (Produktion)
```bash
STREAMLIT_SERVER_PORT=12000
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_ENABLE_CORS=true
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
APP_ENV=production
LOG_LEVEL=INFO
DATA_QUALITY_THRESHOLD=0.8
NLP_MODEL=de_core_news_sm
```

### Health-Check Endpoints
- **Hauptanwendung**: `http://localhost:12000/`
- **Status-Check**: Streamlit lädt automatisch Status-Indikatoren

### Performance-Ziele
- Startup-Zeit: < 30 Sekunden
- Antwortzeit: < 2 Sekunden
- Memory-Limit: 2GB
- CPU-Cores: 2

## 7. Entwicklungs-Workflow
### Lokale Entwicklung
- Hot-Reload aktiviert mit `--server.runOnSave true`
- Debug-Modus verfügbar
- Test-Daten in Demo-Modus verfügbar

### Container-Entwicklung
- Multi-Stage Dockerfile für optimale Performance
- Development und Production Profiles verfügbar
- Volume-Mounts für Live-Code-Updates

### Testing
- Demo-Daten für sofortiges Testen verfügbar
- Beispiel-Anfragen integriert
- Qualitäts-Indikatoren in Echtzeit

## 8. Troubleshooting-Hinweise
### Port-Konflikte
- **Problem**: Port 12000 bereits belegt
- **Lösung**: Backup-Port 12001 verwenden oder `STREAMLIT_SERVER_PORT=12001` setzen

### CORS-Probleme
- **Problem**: Cross-Origin-Fehler
- **Lösung**: `enableCORS = true` in `.streamlit/config.toml` prüfen

### Memory-Issues
- **Problem**: Anwendung läuft langsam oder stürzt ab
- **Lösung**: Resource-Limits in Docker erhöhen oder `docker run -m 4g`

### Startup-Probleme
- **Problem**: Anwendung startet nicht
- **Lösung**: 
  1. Abhängigkeiten prüfen: `pip install -r requirements.txt`
  2. Python-Version prüfen: Python 3.8+
  3. Port-Verfügbarkeit prüfen: `netstat -tulpn | grep :12000`

### NLP-Probleme
- **Problem**: Deutsche Suche funktioniert nicht
- **Lösung**: Fallback auf einfache Textsuche in `app_simple.py` verwenden

## 9. Wichtige Konfigurationsdateien
- **`.streamlit/config.toml`**: Streamlit-Einstellungen (Port, CORS, Theme)
- **`all-hands-dev-metadata.json`**: Vollständige All-Hands.dev Metadaten
- **`all-hands-dev-system-settings.yaml`**: Detaillierte System-Parameter
- **`requirements.txt`**: Python-Abhängigkeiten (Streamlit, Pandas, Plotly)
- **`Dockerfile.all-hands-dev`**: Container-Definition für All-Hands.dev

## 10. Datenquellen und Import
### Unterstützte Formate
- **Dokumente**: PDF (mit OCR), Word, TXT
- **Tabellen**: Excel, CSV, JSON
- **Bilder**: JPG, PNG, TIFF (mit OCR)
- **APIs**: REST, GraphQL, Web-Scraping

### Import-Tools
- **CLI-Tool**: `python tools/data_import_tool.py`
- **Web-Interface**: Drag & Drop Upload
- **Automatisch**: Geplante Imports, API-Polling

### Demo-Daten
- Finanzdaten 2022-2023 verfügbar
- Beispiel-Dokumente und Protokolle
- Sofort testbar ohne zusätzliche Daten