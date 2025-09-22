# 🏛️ Gmunden Transparenz-Datenbank - Schnellstart-Anleitung

## 📦 Was Sie erhalten haben

**Vollständiges System-Paket**: `gmunden_complete_system_final.zip` (42KB)

Enthält:
- ✅ **Vollständige Web-Anwendung** mit deutscher NLP-Suche
- ✅ **Docker-VM Setup** mit automatischer Installation
- ✅ **MongoDB-Datenbank** mit Demo-Daten
- ✅ **OCR-Agent** für Dokumentverarbeitung
- ✅ **Qualitätssicherung** gegen Halluzinationen
- ✅ **Management-Tools** für einfache Verwaltung

## 🚀 Installation in 3 Schritten

### Schritt 1: Entpacken
```bash
# ZIP-Datei entpacken
unzip gmunden_complete_system_final.zip
cd gmunden_complete_system
```

### Schritt 2: Installation starten

**Option A: Vereinfachte Installation (Empfohlen)**
```bash
# Robustes, vereinfachtes Script
./install_simple.sh
```

**Option B: macOS-optimierte Installation**
```bash
# Speziell für macOS optimiert
./install_macos_optimized.sh
```

**Option C: Vollständige Installation**
```bash
# Umfassendes Script mit allen Features
./install.sh
```

**Das Script installiert automatisch:**
- 🔍 **System-Erkennung**: Automatische Erkennung von OS und Architektur
- 🛠️ **System-Abhängigkeiten**: curl, wget, git, unzip, etc.
- 🐳 **Docker-Umgebung**: Docker Engine + Docker Compose (alle Plattformen)
- 🐍 **Python-Stack**: Python 3.11 + pip + venv + alle Abhängigkeiten
- 🔧 **System-Tools**: Tesseract OCR, Poppler, ImageMagick, LibreOffice
- 🗄️ **MongoDB 7.0**: Vollständige Datenbank mit Demo-Daten
- 🔍 **OCR-Agent**: Dokumentverarbeitung mit deutscher Spracherkennung
- 🌐 **Web-Interface**: Streamlit-App auf Port 12000
- ✅ **Verifikation**: Vollständige System-Prüfung nach Installation

### Schritt 3: System nutzen
```bash
# System-Status prüfen
./verify_system.sh

# Browser öffnen:
# http://localhost:12000
```

## 🎯 Sofort verfügbare Features

### 🔍 Deutsche Sprachsuche
Testen Sie diese Beispiel-Anfragen:
- *"Wie viel gab die Gemeinde 2023 für Straßen aus?"*
- *"Zeige mir alle Ausgaben über 10.000 Euro"*
- *"Finde Dokumente über Wasserleitungen"*
- *"Welche Personalkosten gab es 2022?"*

### 📊 Interaktive Visualisierungen
- **Balkendiagramme**: Ausgaben nach Kategorien
- **Zeitverläufe**: Entwicklung über Jahre
- **Kreisdiagramme**: Verteilungen
- **Export**: CSV, JSON, PDF

### 📄 Dokumenten-Upload
- **Unterstützte Formate**: PDF, Word, Excel, Bilder
- **Automatische OCR**: Texterkennung aus gescannten Dokumenten
- **Intelligente Kategorisierung**: Automatische Zuordnung

## 🛠️ System-Verwaltung

Nach der Installation stehen Ihnen diese Tools zur Verfügung:

```bash
./start.sh         # ▶️  System starten
./stop.sh          # ⏹️  System stoppen  
./status.sh        # 📊 Status anzeigen
./verify_system.sh # 🔍 System-Verifikation
./backup.sh        # 💾 Backup erstellen
./update.sh        # 🔄 System aktualisieren
```

## 🌐 Zugriffspunkte

- **🌐 Web-Interface**: http://localhost:12000
- **🌍 All-Hands.dev**: https://work-1-syygiirqlvvwfggb.prod-runtime.all-hands.dev
- **🗄️ MongoDB**: localhost:27017
- **🔍 OCR-Agent**: http://localhost:8080

## 📋 System-Anforderungen

### Minimum
- **OS**: macOS 10.15+ oder Linux
- **RAM**: 4GB
- **Speicher**: 10GB frei
- **Docker**: Wird automatisch installiert

### Empfohlen
- **RAM**: 8GB+
- **CPU**: 4+ Kerne
- **Speicher**: 20GB+ frei

## 🔐 Standard-Zugangsdaten

**⚠️ WICHTIG: Nach Installation ändern!**
- **Admin-Panel**: Passwort `admin123`
- **MongoDB**: `admin` / `change_me_strong`

## 🎯 Erste Schritte nach Installation

### 1. System testen
```bash
# Status prüfen
./status.sh

# Web-Interface öffnen
open http://localhost:12000
```

### 2. Demo-Daten erkunden
- Öffnen Sie das Web-Interface
- Testen Sie die Beispiel-Anfragen
- Erkunden Sie die verschiedenen Bereiche

### 3. Eigene Daten hinzufügen
- **Dokumente hochladen**: Web-Interface → 📄 Dokumente
- **Finanzdaten importieren**: Web-Interface → 🔧 Verwaltung
- **API-Integration**: Automatischer Import von data.gv.at

### 4. System anpassen
- **Konfiguration**: `config/system_config.yaml`
- **Streamlit-Settings**: `.streamlit/config.toml`
- **Docker-Services**: `docker-compose.yml`

## 🛡️ Qualitätssicherung

Das System verhindert automatisch Halluzinationen durch:
- ✅ **Fact-Checking**: Alle Antworten werden verifiziert
- ✅ **Datenvalidierung**: Automatische Qualitätsprüfung
- ✅ **Konsistenz-Checks**: Plausibilitätsprüfungen
- ✅ **Quellen-Tracking**: Nachverfolgbare Datenherkunft

## 🆘 Fehlerbehebung

### Installation schlägt fehl
```bash
# Logs prüfen
cat install.log

# Docker-Status
docker --version
docker info
```

### Web-Interface nicht erreichbar
```bash
# Container-Status
docker-compose ps

# Logs anzeigen
docker-compose logs web
```

### MongoDB-Probleme
```bash
# MongoDB-Status
docker-compose logs mongodb

# Verbindung testen
docker exec gmunden-transparenz-db-mongodb mongosh --eval "db.adminCommand('ping')"
```

## 📞 Support

- **📧 E-Mail**: transparenz@gmunden.at
- **📋 Logs**: `tail -f logs/gmunden_app.log`
- **🐛 Issues**: GitHub Repository

## 🎉 Erfolgsmeldung

Nach erfolgreicher Installation sehen Sie:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🎉 INSTALLATION ERFOLGREICH! 🎉                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

📍 ZUGRIFF AUF DIE ANWENDUNG:
   🌐 Web-Interface:     http://localhost:12000
   🌍 Extern:            https://work-1-syygiirqlvvwfggb.prod-runtime.all-hands.dev

🚀 ERSTE SCHRITTE:
   1. Öffnen Sie http://localhost:12000 in Ihrem Browser
   2. Testen Sie die Suche: 'Wie viel gab die Gemeinde 2023 für Straßen aus?'
   3. Laden Sie Dokumente im 📄 Dokumente-Bereich hoch
   4. Erkunden Sie die verschiedenen Funktionen

🎯 Das System ist jetzt bereit für den produktiven Einsatz!
   Alle Daten werden automatisch validiert und auf Qualität geprüft.
   Keine Halluzinationen - nur echte, verifizierte Gemeindedaten!
```

## 🔄 Nächste Schritte

1. **✅ Installation abgeschlossen** - System läuft
2. **🔍 Demo-Daten testen** - Funktionalität prüfen
3. **📄 Eigene Daten hochladen** - Produktive Nutzung
4. **👥 Benutzer schulen** - Team einweisen
5. **🔐 Sicherheit härten** - Passwörter ändern
6. **📊 Monitoring einrichten** - Überwachung aktivieren

---

**🏛️ Willkommen bei der Gmunden Transparenz-Datenbank!**
*Vollständige Transparenz für alle Bürgerinnen und Bürger.*