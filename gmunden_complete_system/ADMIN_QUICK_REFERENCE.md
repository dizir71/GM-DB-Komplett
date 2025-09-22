# 🔐 Admin-Schnellreferenz

## Sofortiger Zugang

### 🚀 Admin-Bereich öffnen
1. **Web-Interface**: http://localhost:12000
2. **Seite**: "🔧 System-Verwaltung"
3. **Checkbox**: "🔐 Admin-Modus aktivieren" ✅
4. **Passwort**: `admin123`

---

## 📋 Wichtige Befehle

### System-Management
```bash
./start.sh          # Services starten
./stop.sh           # Services stoppen  
./status.sh         # Status anzeigen
```

### Logs anzeigen
```bash
tail -f logs/web.log        # Web-Service
tail -f logs/system.log     # System
tail -f install_*.log       # Installation
```

### Docker-Container
```bash
docker ps                           # Laufende Container
docker logs gmunden-transparenz-*   # Container-Logs
docker restart gmunden-transparenz-mongodb  # MongoDB neu starten
```

---

## 🔧 Häufige Admin-Aufgaben

### ✅ System-Check
- **Web-Interface**: http://localhost:12000 erreichbar?
- **MongoDB**: `docker ps | grep mongodb`
- **Speicher**: `df -h` (< 85% belegt?)
- **Logs**: Keine ERROR-Meldungen?

### 📥 Daten importieren
1. **Admin-Bereich** → **📥 Import-Tab**
2. **Datei auswählen** (PDF, CSV, XLSX)
3. **Upload starten**
4. **Status überwachen**

### 🔄 System neu starten
```bash
./stop.sh
sleep 5
./start.sh
```

### 💾 Backup erstellen
```bash
# Über Admin-Interface: 🔧 Wartung → Backup
# Oder per Kommandozeile:
./tools/backup.sh
```

---

## ⚠️ Notfall-Aktionen

### 🚨 System hängt
```bash
# Alle Services stoppen
./stop.sh

# Docker aufräumen
docker system prune -f

# Neu starten
./start.sh
```

### 🚨 Datenbank-Probleme
```bash
# MongoDB-Container neu starten
docker restart gmunden-transparenz-mongodb

# MongoDB-Logs prüfen
docker logs gmunden-transparenz-mongodb
```

### 🚨 Web-Interface nicht erreichbar
```bash
# Port prüfen
lsof -i :12000

# Service-Status
./status.sh

# Manuell starten
source venv/bin/activate
streamlit run web/app.py --server.port 12000
```

---

## 📊 Monitoring-Dashboard

### System-Metriken (Admin-Interface)
- **📊 System-Tab**: CPU, RAM, Festplatte
- **📈 Performance**: Antwortzeiten, Fehlerrate
- **📋 Logs**: Letzte Ereignisse
- **🔍 Suchen**: Aktive Anfragen

### Kritische Werte
- **CPU**: > 80% = ⚠️ Warnung
- **RAM**: > 90% = 🚨 Kritisch  
- **Festplatte**: > 85% = ⚠️ Warnung
- **Antwortzeit**: > 5s = 🚨 Kritisch

---

## 🔒 Sicherheit

### Standard-Passwort ändern
```python
# In web/app.py, Zeile 509:
if password == "IHR_NEUES_PASSWORT":
```

### Admin-Aktivitäten prüfen
```bash
# Admin-Logs anzeigen
tail -f logs/admin.log

# Letzte Logins
grep "Admin login" logs/web.log
```

---

## 📞 Support

### Logs sammeln
```bash
# Alle wichtigen Logs in eine Datei
{
  echo "=== SYSTEM STATUS ==="
  ./status.sh
  echo -e "\n=== DOCKER STATUS ==="
  docker ps -a
  echo -e "\n=== RECENT LOGS ==="
  tail -50 logs/web.log
  echo -e "\n=== ERROR LOGS ==="
  tail -20 logs/error.log 2>/dev/null || echo "Keine Fehler-Logs"
} > support_info.txt
```

### System-Informationen
```bash
# System-Details
uname -a > system_info.txt
docker --version >> system_info.txt
python3 --version >> system_info.txt
```

---

## 🎯 Checkliste für Admins

### Täglich ✅
- [ ] Web-Interface erreichbar (http://localhost:12000)
- [ ] Keine kritischen Fehler in Logs
- [ ] Speicherplatz < 85%
- [ ] Backup erfolgreich

### Wöchentlich ✅
- [ ] System-Updates prüfen
- [ ] Alte Logs archivieren
- [ ] Performance-Metriken überprüfen
- [ ] Benutzer-Feedback sammeln

### Monatlich ✅
- [ ] Vollständiges System-Backup
- [ ] Sicherheits-Updates installieren
- [ ] Datenbank-Optimierung
- [ ] Kapazitäts-Planung

---

**💡 Tipp**: Bookmarken Sie diese Seite für schnellen Zugriff auf Admin-Funktionen!