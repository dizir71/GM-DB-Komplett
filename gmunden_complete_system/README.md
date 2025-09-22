# 🏛️ Gmunden Transparenz-Datenbank v2.0

**Vollständiges Transparenz-System für Gemeindedaten mit KI-gestützter deutscher Sprachsuche**

## 🚀 Schnellstart

### Automatische Installation (Empfohlen)

```bash
# Repository klonen oder ZIP extrahieren
cd gmunden_complete_system

# Install-Script ausführen
./install.sh
```

Das Script erstellt automatisch:
- ✅ Docker-VM mit allen Services
- ✅ MongoDB-Datenbank mit Demo-Daten
- ✅ Web-Interface auf Port 12000
- ✅ OCR-Agent für Dokumentverarbeitung
- ✅ Alle notwendigen Konfigurationen

### Manuelle Installation

```bash
# 1. Abhängigkeiten installieren
python3 -m venv venv
source venv/bin/activate
pip install -r config/requirements.txt

# 2. Docker-Services starten
docker-compose up -d

# 3. Web-Interface starten
streamlit run web/app.py --server.port 12000 --server.address 0.0.0.0
```

## 🌐 Zugriff

- **Web-Interface**: http://localhost:12000
- **All-Hands.dev**: https://work-1-syygiirqlvvwfggb.prod-runtime.all-hands.dev
- **MongoDB**: localhost:27017
- **OCR-Agent**: http://localhost:8080

## 🎯 Hauptfunktionen

### 🔍 Intelligente Suche
- **Deutsche Sprachverarbeitung**: Verstehen Sie natürliche Fragen
- **Beispiele**:
  - *"Wie viel gab die Gemeinde 2023 für Straßen aus?"*
  - *"Zeige mir alle Protokolle von 2022"*
  - *"Welche Ausgaben über 10.000 Euro gab es?"*

### 📊 Datenvisualisierung
- **Interaktive Diagramme**: Balken-, Linien- und Kreisdiagramme
- **Export-Funktionen**: CSV, JSON, PDF
- **Responsive Design**: Desktop, Tablet, Smartphone

### 📄 Dokumentenverarbeitung
- **OCR-Texterkennung**: Automatische Extraktion aus PDFs und Bildern
- **Unterstützte Formate**: PDF, Word, Excel, CSV, Bilder
- **Intelligente Kategorisierung**: Automatische Zuordnung

### 🛡️ Qualitätssicherung
- **Fact-Checking**: Verhindert Halluzinationen
- **Datenvalidierung**: Automatische Qualitätsprüfung
- **Nur echte Daten**: Keine erfundenen Informationen

## 📁 Systemarchitektur

```
gmunden_complete_system/
├── 🌐 web/                    # Web-Interface (Streamlit)
│   ├── app.py                 # Hauptanwendung
│   └── ...
├── 🧠 backend/                # Backend-Services
│   ├── data_manager.py        # Datenmanagement
│   ├── nlp_processor.py       # Deutsche NLP
│   ├── quality_monitor.py     # Qualitätskontrolle
│   └── fact_checker.py        # Fact-Checking
├── ⚙️ config/                 # Konfiguration
│   ├── system_config.yaml     # Hauptkonfiguration
│   ├── requirements.txt       # Python-Abhängigkeiten
│   └── ...
├── 🐳 Docker-Files            # Container-Setup
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── ...
├── 🛠️ Management-Scripts      # Verwaltung
│   ├── install.sh             # Automatische Installation
│   ├── start.sh               # System starten
│   ├── stop.sh                # System stoppen
│   └── ...
└── 📚 README.md               # Diese Dokumentation
```

## 🛠️ Verwaltung

### System-Kontrolle
```bash
./start.sh      # System starten
./stop.sh       # System stoppen
./status.sh     # Status anzeigen
./backup.sh     # Backup erstellen
./update.sh     # System aktualisieren
```

### Docker-Befehle
```bash
# Services anzeigen
docker-compose ps

# Logs anzeigen
docker-compose logs -f web
docker-compose logs -f mongodb

# Container neu starten
docker-compose restart web
```

### Datenbank-Zugriff
```bash
# MongoDB Shell
docker exec -it gmunden-transparenz-db-mongodb mongosh

# Datenbank-Backup
docker exec gmunden-transparenz-db-mongodb mongodump --archive --gzip > backup.gz
```

## 📊 Datenquellen

### Automatische Integration
- **OÖ Open Data API**: Automatischer Import von data.gv.at
- **Lokale Dateien**: Import aus Verzeichnis `data/imports/`
- **Manual Upload**: Über Web-Interface

### Unterstützte Formate
- **Finanzdaten**: CSV, Excel, JSON
- **Dokumente**: PDF, Word, Text
- **Bilder**: PNG, JPG, TIFF (mit OCR)
- **Protokolle**: PDF, Word

## 🔐 Admin-Bereich

### Zugang
- **Web-Interface**: http://localhost:12000
- **Seite**: "🔧 System-Verwaltung"
- **Passwort**: `admin123` ⚠️ (In Produktion ändern!)

### Admin-Funktionen
- **📊 System-Überwachung**: Status, Performance, Logs
- **📥 Daten-Import**: Upload, Bulk-Import, API-Integration
- **🔧 Wartung**: Backup, Cache, Datenbank-Optimierung
- **📋 Protokollierung**: System-, Fehler- und Zugriffs-Logs

### Dokumentation
- **Vollständige Anleitung**: [ADMIN_GUIDE.md](ADMIN_GUIDE.md)
- **Schnellreferenz**: [ADMIN_QUICK_REFERENCE.md](ADMIN_QUICK_REFERENCE.md)

## 🔧 Konfiguration

### Hauptkonfiguration
Bearbeiten Sie `config/system_config.yaml` für:
- Datenbank-Einstellungen
- NLP-Konfiguration
- Qualitätsschwellenwerte
- Web-Interface-Optionen

### Streamlit-Konfiguration
Anpassungen in `.streamlit/config.toml`:
- Port-Einstellungen
- Theme-Anpassungen
- Performance-Optionen

### Docker-Konfiguration
Anpassungen in `docker-compose.yml`:
- Service-Ports
- Umgebungsvariablen
- Volume-Mappings

## 🔐 Sicherheit

### Standard-Zugangsdaten (ÄNDERN!)
- **Admin-Panel**: `admin123`
- **MongoDB**: `admin / change_me_strong`

### Sicherheitsmaßnahmen
- Input-Validierung
- SQL-Injection-Schutz
- XSS-Schutz
- Datei-Upload-Beschränkungen

## 📈 Performance-Optimierung

### Empfohlene Systemanforderungen
- **RAM**: Mindestens 4GB, empfohlen 8GB
- **CPU**: 2+ Kerne
- **Speicher**: 10GB+ frei
- **Docker**: Version 20.10+

### Optimierungen
- **Caching**: Aktiviert für häufige Anfragen
- **Indizierung**: Optimierte Datenbank-Indizes
- **Lazy Loading**: Nur bei Bedarf laden
- **Kompression**: Reduzierte Datenübertragung

## 🆘 Fehlerbehebung

### Häufige Probleme

#### Web-Interface startet nicht
```bash
# Port prüfen
lsof -i :12000

# Container-Status
docker-compose ps

# Logs prüfen
docker-compose logs web
```

#### MongoDB-Verbindung fehlschlägt
```bash
# Container prüfen
docker-compose ps mongodb

# MongoDB-Logs
docker-compose logs mongodb

# Verbindung testen
docker exec gmunden-transparenz-db-mongodb mongosh --eval "db.adminCommand('ping')"
```

#### OCR funktioniert nicht
```bash
# OCR-Agent Status
curl http://localhost:8080/health

# OCR-Agent Logs
docker-compose logs ocr-agent
```

### Log-Dateien
- **Anwendung**: `logs/gmunden_app.log`
- **Fehler**: `logs/gmunden_errors.log`
- **Installation**: `install.log`

## 🔄 Updates

### Automatisches Update
```bash
./update.sh
```

### Manuelles Update
```bash
git pull
docker-compose build --no-cache
docker-compose up -d
```

## 📞 Support

### Kontakt
- **E-Mail**: transparenz@gmunden.at
- **Telefon**: +43 7612 794-0
- **Website**: www.gmunden.at

### Technischer Support
- **GitHub Issues**: Für Bug-Reports
- **Logs**: `tail -f logs/gmunden_app.log`
- **System-Diagnose**: Web-Interface → Verwaltung → System-Diagnose

## 📄 Lizenz

MIT License - Siehe LICENSE-Datei für Details.

## 🙏 Danksagungen

Entwickelt für die **Gemeinde Gmunden** zur Förderung von Transparenz und Bürgerbeteiligung.

Basiert auf Open-Source-Technologien:
- **Streamlit** - Web-Framework
- **MongoDB** - Datenbank
- **Docker** - Containerisierung
- **spaCy** - NLP-Framework
- **Plotly** - Visualisierungen

---

## 🎯 Schnellstart-Zusammenfassung

1. **Installation**: `./install.sh`
2. **Zugriff**: http://localhost:12000
3. **Erste Suche**: *"Zeige mir die Ausgaben von 2023"*
4. **Dokumente hochladen**: Web-Interface → Dokumente
5. **Verwaltung**: `./start.sh`, `./stop.sh`, `./status.sh`

**Das System ist jetzt bereit für den produktiven Einsatz! 🎉**