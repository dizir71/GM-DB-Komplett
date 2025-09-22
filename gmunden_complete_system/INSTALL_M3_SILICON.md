# 🍎 Installation auf M3 Silicon Mac

## 🚀 Schnellstart (5 Minuten)

### 1. **System herunterladen**
```bash
# Download des kompletten Systems
curl -O https://work-1-syygiirqlvvwfggb.prod-runtime.all-hands.dev/gmunden_complete_system_final.zip

# Oder manuell herunterladen und dann:
unzip gmunden_complete_system_final.zip
cd gmunden_complete_system
```

### 2. **Python-Umgebung einrichten**
```bash
# Python 3.11+ prüfen (M3 optimiert)
python3 --version

# Virtual Environment erstellen
python3 -m venv venv_gmunden
source venv_gmunden/bin/activate

# Abhängigkeiten installieren (M3 optimiert)
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. **System starten**
```bash
# Streamlit-App starten
streamlit run web/app.py --server.port 12000

# Oder mit dem Start-Script
chmod +x install_macos_optimized.sh
./install_macos_optimized.sh
```

### 4. **Öffnen**
- **Browser**: http://localhost:12000
- **Admin-Login**: Passwort `admin123`

---

## 🔧 Detaillierte Installation

### **Voraussetzungen prüfen**
```bash
# macOS Version (sollte 12.0+)
sw_vers

# Python Version (sollte 3.9+)
python3 --version

# Homebrew installiert?
brew --version
```

### **Falls Homebrew fehlt:**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### **Python 3.11 installieren (M3 optimiert):**
```bash
# Python 3.11 für M3 Silicon
brew install python@3.11

# Als Standard setzen
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## 📦 **Vollständige Installation**

### **Schritt 1: Projekt-Setup**
```bash
# Arbeitsverzeichnis erstellen
mkdir -p ~/Projects/gmunden-transparenz
cd ~/Projects/gmunden-transparenz

# System herunterladen
curl -O [DOWNLOAD_URL]/gmunden_complete_system_final.zip
unzip gmunden_complete_system_final.zip
cd gmunden_complete_system

# Berechtigungen setzen
chmod +x *.sh
chmod +x install/*.sh
```

### **Schritt 2: Python-Umgebung**
```bash
# Virtual Environment (M3 optimiert)
python3.11 -m venv venv_gmunden
source venv_gmunden/bin/activate

# Pip upgraden
pip install --upgrade pip setuptools wheel

# Core-Abhängigkeiten
pip install streamlit==1.49.1
pip install plotly==6.3.0
pip install pandas==2.3.2
pip install numpy==2.3.3
pip install pyyaml==6.0.2
pip install requests==2.32.5
pip install python-dateutil==2.9.0
pip install pillow==11.3.0

# Oder alle auf einmal
pip install -r requirements.txt
```

### **Schritt 3: System-Konfiguration**
```bash
# Verzeichnisse erstellen
mkdir -p data/{cache,backup,uploads,exports}
mkdir -p logs

# Konfiguration anpassen
cp config/config_local.yaml config/config.yaml

# Berechtigungen
chmod 755 data/
chmod 755 logs/
```

### **Schritt 4: Erste Tests**
```bash
# System-Check
python3 -c "import streamlit, plotly, pandas; print('✅ Alle Module verfügbar')"

# Streamlit-Test
streamlit hello

# Unser System testen
streamlit run web/app.py --server.port 12000 --server.address localhost
```

---

## 🛠️ **M3 Silicon Optimierungen**

### **Performance-Tuning**
```bash
# .streamlit/config.toml anpassen
cat > .streamlit/config.toml << 'EOF'
[server]
port = 12000
address = "localhost"
maxUploadSize = 200
headless = false

[runner]
fastReruns = true
postScriptGC = true

[client]
caching = true

[theme]
primaryColor = "#2e7d32"
backgroundColor = "#ffffff"
EOF
```

### **Memory-Optimierung für M3**
```bash
# Umgebungsvariablen setzen
echo 'export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200' >> ~/.zshrc
echo 'export PYTHONPATH="${PYTHONPATH}:$(pwd)"' >> ~/.zshrc
source ~/.zshrc
```

---

## 🚀 **Start-Scripts**

### **Einfacher Start**
```bash
#!/bin/bash
# start_local.sh

echo "🍎 Starte Gmunden Transparenz-System auf M3 Silicon..."

# Virtual Environment aktivieren
source venv_gmunden/bin/activate

# System starten
streamlit run web/app.py \
  --server.port 12000 \
  --server.address localhost \
  --server.headless false \
  --browser.gatherUsageStats false

echo "✅ System läuft auf: http://localhost:12000"
```

### **Erweiteter Start mit Monitoring**
```bash
#!/bin/bash
# start_advanced.sh

echo "🚀 Erweiteter Start für M3 Silicon..."

# Systemcheck
python3 -c "
import sys, platform
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
print(f'Processor: {platform.processor()}')
"

# Virtual Environment
source venv_gmunden/bin/activate

# Logs-Verzeichnis
mkdir -p logs

# Mit Logging starten
streamlit run web/app.py \
  --server.port 12000 \
  --server.address localhost \
  --logger.level info \
  2>&1 | tee logs/streamlit.log &

echo "✅ System gestartet mit PID: $!"
echo "📊 Logs: tail -f logs/streamlit.log"
echo "🌐 URL: http://localhost:12000"
```

---

## 🔧 **Troubleshooting M3 Silicon**

### **Problem: Module nicht gefunden**
```bash
# Lösung: Virtual Environment neu erstellen
rm -rf venv_gmunden
python3.11 -m venv venv_gmunden
source venv_gmunden/bin/activate
pip install -r requirements.txt
```

### **Problem: Streamlit startet nicht**
```bash
# Port prüfen
lsof -i :12000

# Alternativen Port
streamlit run web/app.py --server.port 12001

# Oder Port freigeben
sudo lsof -ti:12000 | xargs sudo kill -9
```

### **Problem: Upload-Fehler**
```bash
# Upload-Größe erhöhen
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=500

# Oder in config.toml:
echo "maxUploadSize = 500" >> .streamlit/config.toml
```

### **Problem: Performance**
```bash
# M3 Optimierungen aktivieren
export OPENBLAS_NUM_THREADS=8
export MKL_NUM_THREADS=8
export OMP_NUM_THREADS=8

# Memory-Limit setzen
ulimit -m 8388608  # 8GB
```

---

## 📊 **Lokale Datenbank-Setup**

### **MongoDB (Optional)**
```bash
# MongoDB für M3 Silicon
brew tap mongodb/brew
brew install mongodb-community

# Starten
brew services start mongodb/brew/mongodb-community

# Testen
mongosh --eval "db.runCommand('ismaster')"
```

### **SQLite (Einfacher)**
```bash
# SQLite ist bereits installiert
sqlite3 --version

# Datenbank erstellen
mkdir -p data/db
sqlite3 data/db/gmunden.db ".databases"
```

---

## 🎯 **Produktions-Setup**

### **Automatischer Start beim Boot**
```bash
# LaunchAgent erstellen
mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.gmunden.transparenz.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gmunden.transparenz</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/$(whoami)/Projects/gmunden-transparenz/gmunden_complete_system/start_local.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Aktivieren
launchctl load ~/Library/LaunchAgents/com.gmunden.transparenz.plist
```

### **Backup-Script**
```bash
#!/bin/bash
# backup_local.sh

BACKUP_DIR="$HOME/Backups/gmunden-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Daten sichern
cp -r data/ "$BACKUP_DIR/"
cp -r logs/ "$BACKUP_DIR/"

# Komprimieren
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "✅ Backup erstellt: $BACKUP_DIR.tar.gz"
```

---

## 🌐 **Netzwerk-Zugriff**

### **Lokales Netzwerk freigeben**
```bash
# Für andere Geräte im Netzwerk
streamlit run web/app.py \
  --server.port 12000 \
  --server.address 0.0.0.0

# Firewall-Regel (falls nötig)
sudo pfctl -f /etc/pf.conf
```

### **Reverse Proxy (Nginx)**
```bash
# Nginx installieren
brew install nginx

# Konfiguration
cat > /opt/homebrew/etc/nginx/servers/gmunden.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://127.0.0.1:12000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Nginx starten
brew services start nginx
```

---

## ✅ **Installations-Checkliste**

- [ ] **macOS 12.0+** installiert
- [ ] **Homebrew** installiert
- [ ] **Python 3.11+** installiert
- [ ] **Projekt heruntergeladen** und entpackt
- [ ] **Virtual Environment** erstellt
- [ ] **Abhängigkeiten** installiert
- [ ] **Berechtigungen** gesetzt
- [ ] **System gestartet** (http://localhost:12000)
- [ ] **Admin-Login** getestet (admin123)
- [ ] **Bulk-Import** getestet
- [ ] **Backup-Script** eingerichtet

---

## 🎉 **Fertig!**

**Ihr Gmunden Transparenz-System läuft jetzt lokal auf Ihrem M3 Silicon Mac!**

### **Nächste Schritte:**
1. **Testen**: Admin-Bereich → Bulk-Import
2. **Daten importieren**: Ihre 16 PDF-Protokolle
3. **Anpassen**: Konfiguration nach Bedarf
4. **Backup**: Automatisches Backup einrichten

### **Support:**
- **Logs**: `tail -f logs/streamlit.log`
- **Status**: http://localhost:12000
- **Admin**: Passwort `admin123`

**Viel Erfolg mit Ihrem lokalen Transparenz-System! 🚀**