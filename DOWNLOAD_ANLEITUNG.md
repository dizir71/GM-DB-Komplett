## 🚀 **Schnellstart (2 Minuten)**

### **Option 1: Direkter Download**
```bash
# Terminal öffnen und eingeben:
gmunden_system.zip
unzip gmunden_system.zip
cd gmunden_complete_system
./start_m3_silicon.sh

### **Option 2: Browser-Download**
1. **Download**: [gmunden_complete_system_final.zip]
2. **Entpacken**: Doppelklick auf ZIP-Datei
3. **Terminal**: `cd ~/Downloads/gmunden_complete_system`
4. **Starten**: `./start_m3_silicon.sh`

---

## 🍎 **M3 Silicon Installation**

### **Schritt 1: System herunterladen**
```bash
# Arbeitsverzeichnis erstellen
mkdir -p ~/Projects/gmunden-transparenz
cd ~/Projects/gmunden-transparenz

# System herunterladen
gmunden_complete_system_final.zip

# Entpacken
unzip gmunden_system.zip
cd gmunden_complete_system

# Berechtigungen setzen
chmod +x *.sh
```

### **Schritt 2: Automatische Installation**
```bash
# M3 Silicon optimiertes Start-Script
./start_m3_silicon.sh
```

**Das Script macht automatisch:**
- ✅ Python Virtual Environment erstellen
- ✅ Alle Abhängigkeiten installieren
- ✅ M3 Silicon Optimierungen aktivieren
- ✅ Streamlit konfigurieren
- ✅ System starten
- ✅ Browser öffnen

### **Schritt 3: System nutzen**
- **URL**: http://localhost:12000
- **Admin-Login**: Passwort `admin123`
- **Bulk-Import**: Admin → Datei-Import → Mehrere Dateien

---

## 🔧 **Manuelle Installation (falls gewünscht)**

### **Voraussetzungen installieren**
```bash
# Homebrew (falls nicht vorhanden)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 3.11 für M3 Silicon
brew install python@3.11

# PATH setzen
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### **System einrichten**
```bash
# Virtual Environment
python3 -m venv venv_gmunden
source venv_gmunden/bin/activate

# Abhängigkeiten
pip install -r requirements.txt

# Starten
streamlit run web/app.py --server.port 12000
```

---

## 📊 **Was Sie bekommen**

### **Vollständiges System (97KB ZIP)**
- ✅ **Admin-Bereich**: Vollständig funktional
- ✅ **Bulk-Import**: Robuste PDF-Verarbeitung
- ✅ **Öffentliche Datenquellen**: API-Integration
- ✅ **Bürger-Interface**: Suchfunktion
- ✅ **M3 Silicon**: Optimiert für Apple Silicon

### **Sofort verfügbare Features**
- 📥 **Datei-Upload**: PDF, CSV, Excel, Word
- 🔍 **OCR-Verarbeitung**: Automatische Texterkennung
- 📊 **Visualisierungen**: Interaktive Diagramme
- 🌐 **API-Import**: data.gv.at, Statistik Austria
- 💾 **Backup-System**: Automatische Datensicherung

---

## 🎯 **Ihre 16 PDF-Protokolle**

### **Bulk-Import-Einstellungen für Ihre Dateien**
```
⚙️ Empfohlene Einstellungen:
├── Max. Dateigröße: 50MB
├── Verarbeitungs-Chunks: 3 Dateien
├── Timeout pro Datei: 120s
├── Wiederholungsversuche: 3x
├── Fehler überspringen: ✅
└── OCR aktivieren: ✅
```

### **Verarbeitung**
1. **Admin-Login**: http://localhost:12000 → Passwort `admin123`
2. **Tab**: "📥 Datei-Import"
3. **Auswählen**: "📁 Mehrere Dateien"
4. **Upload**: Alle 16 PDF-Dateien
5. **Kategorie**: "Protokolle"
6. **Jahr**: 2022
7. **Import starten**: Mit Live-Progress

---

## 🆘 **Hilfe & Support**

### **Häufige Probleme**
```bash
# Port bereits belegt
lsof -ti:12000 | xargs kill -9

# Python-Module fehlen
pip install -r requirements.txt

# Berechtigungen
chmod +x start_m3_silicon.sh

# Virtual Environment neu
rm -rf venv_gmunden
python3 -m venv venv_gmunden
```

### **System-Check**
```bash
# Alles prüfen
python3 -c "import streamlit, plotly, pandas; print('✅ OK')"

# Logs anzeigen
tail -f logs/streamlit_*.log

# Status prüfen
curl http://localhost:12000
```

---

## 🎉 **Fertig!**

**Nach der Installation haben Sie:**
- 🏠 **Lokales System** auf Ihrem M3 Mac
- 🚀 **Optimierte Performance** für Apple Silicon
- 📁 **Bulk-Import** für Ihre PDF-Protokolle
- 🔐 **Admin-Zugang** mit vollem Funktionsumfang
- 💾 **Lokale Datenspeicherung** (keine Cloud)

### **Nächste Schritte:**
1. ✅ System herunterladen und starten
2. ✅ Admin-Bereich testen
3. ✅ Ihre 16 PDF-Protokolle importieren
4. ✅ Bürger-Interface anpassen
5. ✅ Backup einrichten

**Viel Erfolg mit Ihrem lokalen Transparenz-System! 🍎🚀**
