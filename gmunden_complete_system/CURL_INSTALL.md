# 🚀 Ein-Befehl Installation mit curl

## 🎯 **Sofort-Installation (1 Befehl)**

### **Docker-Version (Empfohlen für alle Unix-Systeme)**
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/install.sh | bash
```

### **Oder manuell Schritt für Schritt:**

#### **1. System herunterladen**
```bash
# Arbeitsverzeichnis erstellen
mkdir -p ~/gmunden-transparenz && cd ~/gmunden-transparenz

# Komplettes System herunterladen
curl -L -o gmunden_system.tar.gz "https://github.com/YOUR_USERNAME/gmunden-transparenz-system/archive/main.tar.gz"

# Entpacken
tar -xzf gmunden_system.tar.gz
cd gmunden-transparenz-system-main

# Berechtigungen setzen
chmod +x *.sh
```

#### **2. Installation starten**
```bash
# Docker-Installation (alle Unix-Systeme)
./install_docker.sh

# Oder native Installation
# macOS M3 Silicon:
./start_m3_silicon.sh

# Linux:
./install_linux.sh
```

---

## 🐳 **Docker-Installation (Universell)**

### **Alle Unix-Systeme (Linux, macOS, FreeBSD)**
```bash
# Ein-Befehl-Installation
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/quick_install.sh | bash -s -- --docker

# Oder manuell:
mkdir -p ~/gmunden-docker && cd ~/gmunden-docker
curl -L -o install.tar.gz "https://github.com/YOUR_USERNAME/gmunden-transparenz-system/archive/main.tar.gz"
tar -xzf install.tar.gz --strip-components=1
chmod +x *.sh
./install_docker.sh
```

### **Was passiert automatisch:**
- ✅ Docker wird installiert (falls nicht vorhanden)
- ✅ Docker Compose wird eingerichtet
- ✅ MongoDB Container wird gestartet
- ✅ Redis Cache wird eingerichtet
- ✅ Backup-System wird aktiviert
- ✅ Nginx Reverse Proxy wird konfiguriert
- ✅ System startet auf Port 12000

---

## 🌐 **Remote-Deployment**

### **Auf Remote-Server installieren**
```bash
# Auf einzelnem Server
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/deploy.sh | bash -s -- --remote user@server.com

# Auf mehreren Servern (hosts.txt mit einem Host pro Zeile)
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/deploy.sh | bash -s -- --replicate hosts.txt
```

### **Hosts-Datei Beispiel (hosts.txt)**
```
user@server1.example.com
user@server2.example.com
admin@backup-server.com
```

---

## 🔧 **System-spezifische Installation**

### **Ubuntu/Debian**
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/install_ubuntu.sh | sudo bash
```

### **CentOS/RHEL/Fedora**
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/install_centos.sh | sudo bash
```

### **macOS (M1/M2/M3 Silicon)**
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/install_macos.sh | bash
```

### **Arch Linux**
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/install_arch.sh | bash
```

---

## 📦 **Vollständiges System herunterladen**

### **ZIP-Archiv**
```bash
curl -L -o gmunden_complete.zip "https://github.com/YOUR_USERNAME/gmunden-transparenz-system/archive/main.zip"
unzip gmunden_complete.zip
cd gmunden-transparenz-system-main
```

### **TAR.GZ-Archiv**
```bash
curl -L -o gmunden_complete.tar.gz "https://github.com/YOUR_USERNAME/gmunden-transparenz-system/archive/main.tar.gz"
tar -xzf gmunden_complete.tar.gz
cd gmunden-transparenz-system-main
```

---

## 🎯 **Ihre 16 PDF-Protokolle**

Nach der Installation:

### **1. System öffnen**
```
URL: http://localhost:12000
Admin-Passwort: admin123
```

### **2. Bulk-Import konfigurieren**
- **Admin-Bereich** → **Datei-Import** → **Mehrere Dateien**
- **Max. Dateigröße**: 50MB
- **Timeout**: 120s
- **Chunks**: 3 Dateien
- **Wiederholungen**: 3x

### **3. PDFs hochladen**
- Alle 16 Protokolle gleichzeitig
- Kategorie: "Protokolle"
- Jahr: 2022
- OCR aktivieren: ✅

---

## 🔧 **Erweiterte Optionen**

### **Mit benutzerdefinierten Einstellungen**
```bash
# Port ändern
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/install.sh | bash -s -- --port 8080

# Mit SSL
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/install.sh | bash -s -- --ssl

# Produktions-Modus
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/install.sh | bash -s -- --production
```

### **Nur bestimmte Komponenten**
```bash
# Nur Web-Interface (ohne Datenbank)
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/install.sh | bash -s -- --minimal

# Mit externer MongoDB
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/gmunden-transparenz-system/main/install.sh | bash -s -- --external-db mongodb://your-server:27017
```

---

## 🛠️ **Nach der Installation**

### **System-Status prüfen**
```bash
# Docker-Version
docker compose ps
docker compose logs -f

# Native Version
ps aux | grep streamlit
curl http://localhost:12000
```

### **System verwalten**
```bash
# Stoppen
docker compose down

# Starten
docker compose up -d

# Neustarten
docker compose restart

# Logs anzeigen
docker compose logs -f gmunden-app
```

### **Backup erstellen**
```bash
# Automatisches Backup (läuft täglich)
ls -la backups/

# Manuelles Backup
docker compose exec backup sh -c "tar -czf /backup/output/manual_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /backup data mongo"
```

---

## 🎉 **Fertig!**

Nach der Installation haben Sie:

- ✅ **Vollständiges Transparenz-System** auf http://localhost:12000
- ✅ **Admin-Bereich** mit Passwort `admin123`
- ✅ **Bulk-Import** für Ihre 16 PDF-Protokolle
- ✅ **MongoDB-Datenbank** für persistente Speicherung
- ✅ **Redis-Cache** für bessere Performance
- ✅ **Automatische Backups** täglich
- ✅ **Nginx Reverse Proxy** für Produktions-Einsatz
- ✅ **Docker-Container** für einfache Verwaltung

**Das System ist sofort einsatzbereit für Ihre Gemeinderat-Protokolle!** 🏛️🚀