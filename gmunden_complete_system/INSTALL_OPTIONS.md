# 🛠️ Installations-Optionen

## Verfügbare Install-Scripts

### 1. `install_simple.sh` (⭐ Empfohlen)

**Für wen**: Alle Benutzer, die eine stabile Installation wollen

**Vorteile**:
- ✅ Robuste Fehlerbehandlung
- ✅ Minimale Abhängigkeiten
- ✅ Funktioniert auf macOS und Linux
- ✅ Schnelle Installation
- ✅ Weniger Fehlerquellen

**Was wird installiert**:
- Docker (Desktop für macOS, Engine für Linux)
- Python 3.8+ mit Virtual Environment
- Kritische Python-Pakete
- MongoDB via Docker
- Web-Interface (Streamlit)

```bash
./install_simple.sh
```

### 2. `install_macos_fixed.sh` (⭐ Für macOS-Probleme)

**Für wen**: macOS-Benutzer mit sqlite3-Fehlern oder anderen Problemen

**Vorteile**:
- ✅ Behebt sqlite3-Installationsfehler
- ✅ Robuste Fehlerbehandlung
- ✅ Apple Silicon (M1/M2) Support
- ✅ Einzelpaket-Installation (sicherer)
- ✅ Web-Service läuft lokal (nicht in Docker)

**Besonderheiten**:
- Installiert nur externe Python-Pakete
- Überspringt problematische Pakete automatisch
- MongoDB in Docker, Web-Service lokal
- Umfassende macOS-Optimierungen

```bash
./install_macos_fixed.sh
```

### 3. `install_macos_optimized.sh`

**Für wen**: macOS-Benutzer, die alle Features wollen (nach Fix)

**Vorteile**:
- ✅ Speziell für macOS optimiert
- ✅ Homebrew-Integration
- ✅ Apple Silicon (M1/M2) Support
- ✅ OCR-Tools (Tesseract, ImageMagick)
- ✅ Umfassende Systemprüfungen

**Was wird zusätzlich installiert**:
- Homebrew (falls nicht vorhanden)
- Tesseract OCR mit deutscher Sprache
- Poppler (PDF-Verarbeitung)
- ImageMagick (Bildverarbeitung)
- Xcode Command Line Tools (falls nötig)

```bash
./install_macos_optimized.sh
```

### 4. `install.sh` (Vollständig)

**Für wen**: Erfahrene Benutzer, Entwickler

**Vorteile**:
- ✅ Alle Features und Tools
- ✅ Umfassende Systemprüfungen
- ✅ Unterstützt viele Linux-Distributionen
- ✅ Erweiterte Konfigurationsoptionen
- ✅ Vollständige Verifikation

**Was wird zusätzlich installiert**:
- Alle System-Tools
- spaCy mit deutschem Modell
- LibreOffice (für Dokumentkonvertierung)
- Erweiterte OCR-Funktionen
- Monitoring und Logging

```bash
./install.sh
```

## Empfehlungen nach System

### macOS (alle Versionen)
```bash
# Bei sqlite3-Fehlern (Empfohlen):
./install_macos_fixed.sh

# Für einfache Installation:
./install_simple.sh

# Wenn Sie alle OCR-Features brauchen:
./install_macos_optimized.sh
```

### Ubuntu/Debian
```bash
# Erste Wahl:
./install_simple.sh

# Für Server-Installation:
./install.sh
```

### CentOS/RHEL/Fedora
```bash
# Erste Wahl:
./install_simple.sh

# Für vollständige Features:
./install.sh
```

### Arch Linux
```bash
# Empfohlen:
./install.sh
```

## Fehlerbehebung

### Wenn `install_simple.sh` fehlschlägt:

1. **Docker-Problem**:
   ```bash
   # Docker manuell installieren
   # macOS: Docker Desktop von docker.com
   # Linux: curl -fsSL https://get.docker.com | sh
   ```

2. **Python-Problem**:
   ```bash
   # Python 3.8+ installieren
   # macOS: brew install python3
   # Ubuntu: sudo apt install python3 python3-pip
   ```

3. **Berechtigungen**:
   ```bash
   # Linux: Benutzer zur docker-Gruppe hinzufügen
   sudo usermod -aG docker $USER
   newgrp docker
   ```

### Wenn `install_macos_optimized.sh` fehlschlägt:

1. **Homebrew-Problem**:
   ```bash
   # Homebrew manuell installieren
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Xcode Command Line Tools**:
   ```bash
   xcode-select --install
   ```

3. **Docker Desktop**:
   ```bash
   # Manuell von docker.com herunterladen
   open https://www.docker.com/products/docker-desktop/
   ```

### Wenn `install.sh` fehlschlägt:

1. **System nicht erkannt**:
   ```bash
   # Verwenden Sie install_simple.sh als Alternative
   ./install_simple.sh
   ```

2. **Paketmanager-Probleme**:
   ```bash
   # Pakete manuell installieren
   # Siehe INSTALLATION_TROUBLESHOOTING.md
   ```

## Nach der Installation

### Verifikation
```bash
# System-Status prüfen
./status.sh

# Services testen
curl http://localhost:12000/_stcore/health
```

### Erste Schritte
1. Browser öffnen: http://localhost:12000
2. Testsuche: "Zeige mir alle Daten"
3. Dokument hochladen im Web-Interface

### Management
```bash
./start.sh    # Services starten
./stop.sh     # Services stoppen
./status.sh   # Status anzeigen
```

## Unterschiede im Detail

| Feature | Simple | macOS Optimized | Vollständig |
|---------|--------|-----------------|-------------|
| Docker | ✅ | ✅ | ✅ |
| Python + Streamlit | ✅ | ✅ | ✅ |
| MongoDB | ✅ | ✅ | ✅ |
| Web-Interface | ✅ | ✅ | ✅ |
| OCR (Tesseract) | ❌ | ✅ | ✅ |
| spaCy Deutsch | ❌ | ✅ | ✅ |
| ImageMagick | ❌ | ✅ | ✅ |
| LibreOffice | ❌ | ❌ | ✅ |
| System-Verifikation | Basic | Erweitert | Vollständig |
| Multi-OS Support | ✅ | macOS only | ✅ |
| Installationszeit | ~5 Min | ~10 Min | ~15 Min |

## Empfehlung

**Für die meisten Benutzer**: Starten Sie mit `install_simple.sh`

- Schnell und zuverlässig
- Alle Kernfunktionen verfügbar
- Weniger Fehlerquellen
- Einfache Fehlerbehebung

**Upgrade später möglich**: Sie können jederzeit zusätzliche Tools nachinstallieren:

```bash
# OCR-Tools nachinstallieren (macOS)
brew install tesseract tesseract-lang poppler imagemagick

# OCR-Tools nachinstallieren (Ubuntu)
sudo apt install tesseract-ocr tesseract-ocr-deu poppler-utils imagemagick

# spaCy Deutsch nachinstallieren
source venv/bin/activate
pip install spacy
python -m spacy download de_core_news_sm
```