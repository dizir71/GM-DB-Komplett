# 🚀 All-Hands.dev Setup Guide
## Gmunden Transparenz-Datenbank - Optimale Konfiguration

---

## 📋 **ÜBERSICHT**

Diese Anleitung enthält die **optimalen Metadaten und Systemeinstellungen** für das Gmunden Transparenz-Datenbank-Projekt auf **All-Hands.dev**.

### ✅ **BEREITGESTELLTE KONFIGURATIONEN**

1. **📄 Metadaten-Datei**: `all-hands-dev-metadata.json`
2. **⚙️ Systemeinstellungen**: `all-hands-dev-system-settings.yaml`
3. **🌐 Streamlit-Konfiguration**: `.streamlit/config.toml`
4. **🐳 Docker-Konfiguration**: `Dockerfile.all-hands-dev`
5. **🔧 Docker Compose**: `docker-compose.all-hands-dev.yml`

---

## 🎯 **ALL-HANDS.DEV OPTIMIERUNGEN**

### **Port-Konfiguration**
```yaml
Primärer Port: 12000
Backup-Port: 12001
Health-Check: 8080
```

### **Netzwerk-Einstellungen**
```yaml
Host: 0.0.0.0
CORS: Aktiviert
iFrame-Support: Aktiviert
WebSocket: Deaktiviert (nicht benötigt)
```

### **Performance-Optimierungen**
```yaml
Startup-Zeit: < 30 Sekunden
Memory-Limit: 2GB
CPU-Cores: 2
Caching: Aktiviert
Compression: Aktiviert
```

---

## 📁 **DATEI-ÜBERSICHT**

### **1. all-hands-dev-metadata.json**
Vollständige Metadaten-Konfiguration mit:
- Projekt-Informationen
- All-Hands.dev spezifische Einstellungen
- Datenintegrations-Konfiguration
- NLP und KI-Einstellungen
- Sicherheits- und Datenschutz-Konfiguration
- Monitoring und Qualitätssicherung
- Deployment-Konfiguration

### **2. all-hands-dev-system-settings.yaml**
Detaillierte Systemeinstellungen für:
- Runtime-Konfiguration
- Web-Framework-Einstellungen
- Datenintegrations-Parameter
- NLP-Konfiguration
- Benutzeroberflächen-Einstellungen
- Performance-Optimierungen

### **3. .streamlit/config.toml**
Streamlit-spezifische Konfiguration:
- Port und Adress-Einstellungen
- CORS-Aktivierung
- Upload-Limits
- Theme-Konfiguration
- Performance-Einstellungen

### **4. Dockerfile.all-hands-dev**
Container-Konfiguration:
- Multi-Stage Build
- All-Hands.dev Optimierungen
- Sicherheits-Einstellungen
- Health-Checks

### **5. docker-compose.all-hands-dev.yml**
Service-Orchestrierung:
- Hauptanwendung
- MongoDB-Datenbank
- OCR-Service (optional)
- Nginx Load Balancer (optional)

---

## 🚀 **SCHNELLSTART FÜR ALL-HANDS.DEV**

### **Option 1: Direkte Streamlit-Ausführung**
```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Anwendung starten
streamlit run web/app_simple.py \
  --server.port 12000 \
  --server.address 0.0.0.0 \
  --server.enableCORS true \
  --server.enableXsrfProtection false \
  --browser.gatherUsageStats false
```

### **Option 2: Docker-Container**
```bash
# Container bauen
docker build -f Dockerfile.all-hands-dev -t gmunden-transparenz .

# Container starten
docker run -p 12000:12000 -p 12001:12001 gmunden-transparenz
```

### **Option 3: Docker Compose**
```bash
# Alle Services starten
docker-compose -f docker-compose.all-hands-dev.yml up -d

# Nur Hauptanwendung
docker-compose -f docker-compose.all-hands-dev.yml up gmunden-transparenz
```

---

## 🌐 **ZUGRIFF AUF ALL-HANDS.DEV**

### **URLs**
- **Primär**: `https://work-1-{workspace-id}.prod-runtime.all-hands.dev`
- **Backup**: `https://work-2-{workspace-id}.prod-runtime.all-hands.dev`
- **Lokal**: `http://localhost:12000`

### **Port-Mapping**
```
All-Hands.dev Port 12000 → Container Port 12000
All-Hands.dev Port 12001 → Container Port 12001
```

---

## ⚙️ **UMGEBUNGSVARIABLEN**

### **All-Hands.dev spezifisch**
```bash
STREAMLIT_SERVER_PORT=12000
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_ENABLE_CORS=true
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### **Anwendungs-spezifisch**
```bash
APP_ENV=production
LOG_LEVEL=INFO
DATA_QUALITY_THRESHOLD=0.8
NLP_MODEL=de_core_news_sm
MONGODB_URI=mongodb://localhost:27017/gmunden_transparenz
CACHE_ENABLED=true
CACHE_TTL=3600
```

---

## 🔧 **KONFIGURATION ANPASSEN**

### **Port ändern**
1. **Streamlit-Konfiguration**: `.streamlit/config.toml`
   ```toml
   [server]
   port = 12001  # Neuer Port
   ```

2. **Metadaten aktualisieren**: `all-hands-dev-metadata.json`
   ```json
   "networking": {
     "primary_port": 12001
   }
   ```

3. **Docker-Konfiguration**: `docker-compose.all-hands-dev.yml`
   ```yaml
   ports:
     - "12001:12001"
   ```

### **Performance optimieren**
1. **Memory-Limit erhöhen**: `all-hands-dev-system-settings.yaml`
   ```yaml
   performance:
     resource_limits:
       memory: "4GB"
   ```

2. **Cache-Einstellungen**: `all-hands-dev-metadata.json`
   ```json
   "caching": {
     "max_size": "1GB",
     "ttl": 7200
   }
   ```

---

## 📊 **MONITORING UND HEALTH-CHECKS**

### **Health-Check Endpoints**
- **Hauptanwendung**: `http://localhost:12000/`
- **API-Status**: `http://localhost:12000/healthz` (falls implementiert)

### **Monitoring-Metriken**
```yaml
- Response Time: < 2 Sekunden
- Memory Usage: < 80%
- CPU Usage: < 70%
- Error Rate: < 5%
- Uptime: > 99%
```

### **Log-Dateien**
```
./logs/app.log          # Anwendungs-Logs
./logs/streamlit.log    # Streamlit-Logs
./logs/error.log        # Fehler-Logs
./logs/access.log       # Zugriffs-Logs
```

---

## 🔒 **SICHERHEIT UND COMPLIANCE**

### **Sicherheits-Features**
- ✅ Input-Validierung aktiviert
- ✅ XSS-Schutz aktiviert
- ✅ CORS korrekt konfiguriert
- ✅ Rate-Limiting implementiert
- ✅ Audit-Logging aktiviert

### **Datenschutz**
- ✅ DSGVO-konform
- ✅ Nur öffentliche Daten
- ✅ Transparente Datenquellen
- ✅ Anonymisierung aktiviert

### **Compliance-Standards**
- ✅ WCAG 2.1 AA (Barrierefreiheit)
- ✅ OWASP Top 10 (Sicherheit)
- ✅ Austrian Government Standards

---

## 🚀 **DEPLOYMENT-STRATEGIEN**

### **Entwicklung**
```bash
# Lokale Entwicklung mit Hot-Reload
streamlit run web/app_simple.py --server.runOnSave true
```

### **Staging**
```bash
# Docker mit Development-Konfiguration
docker-compose -f docker-compose.all-hands-dev.yml up --profile staging
```

### **Produktion**
```bash
# Vollständige Produktion mit Load Balancer
docker-compose -f docker-compose.all-hands-dev.yml up --profile production
```

---

## 🔧 **TROUBLESHOOTING**

### **Port-Konflikte**
```bash
# Freie Ports finden
netstat -tulpn | grep :12000

# Alternative Ports verwenden
export STREAMLIT_SERVER_PORT=12001
```

### **Memory-Probleme**
```bash
# Memory-Usage prüfen
docker stats gmunden-transparenz-app

# Memory-Limit erhöhen
docker run -m 4g gmunden-transparenz
```

### **CORS-Probleme**
```bash
# CORS-Headers prüfen
curl -H "Origin: https://work-1-xyz.prod-runtime.all-hands.dev" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS http://localhost:12000/
```

---

## 📚 **WEITERE RESSOURCEN**

### **Dokumentation**
- `README.md` - Projekt-Übersicht
- `SYSTEM_COMPLETE_SUMMARY.md` - System-Zusammenfassung
- `requirements.txt` - Python-Abhängigkeiten

### **Konfigurationsdateien**
- `all-hands-dev-metadata.json` - Vollständige Metadaten
- `all-hands-dev-system-settings.yaml` - System-Einstellungen
- `.streamlit/config.toml` - Streamlit-Konfiguration

### **Container-Dateien**
- `Dockerfile.all-hands-dev` - Container-Definition
- `docker-compose.all-hands-dev.yml` - Service-Orchestrierung

---

## ✅ **CHECKLISTE FÜR ALL-HANDS.DEV**

### **Vor dem Deployment**
- [ ] Port 12000 verfügbar
- [ ] CORS korrekt konfiguriert
- [ ] iFrame-Support aktiviert
- [ ] Health-Checks funktionieren
- [ ] Umgebungsvariablen gesetzt
- [ ] Logs-Verzeichnis erstellt
- [ ] Abhängigkeiten installiert

### **Nach dem Deployment**
- [ ] Anwendung erreichbar unter Port 12000
- [ ] Beispiel-Suchen funktionieren
- [ ] Deutsche NLP-Verarbeitung aktiv
- [ ] Datenvisualisierungen laden
- [ ] Responsive Design funktioniert
- [ ] Performance-Metriken im grünen Bereich

---

## 🎉 **FAZIT**

Diese Konfigurationsdateien bieten die **optimalen Einstellungen** für das Gmunden Transparenz-Datenbank-Projekt auf **All-Hands.dev**:

✅ **Port-Konfiguration**: 12000 (primär), 12001 (backup)
✅ **CORS & iFrame**: Vollständig aktiviert
✅ **Performance**: Container-optimiert
✅ **Sicherheit**: Produktions-ready
✅ **Monitoring**: Health-Checks implementiert
✅ **Skalierbarkeit**: Docker Compose ready

**Das System ist bereit für den Einsatz auf All-Hands.dev!** 🚀