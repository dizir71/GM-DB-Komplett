# 🔐 Admin-Bereich - Anleitung

## Zugang zum Admin-Bereich

### Standard-Zugangsdaten
- **Passwort**: `admin123`

### Zugang aktivieren
1. Öffnen Sie das Web-Interface: http://localhost:12000
2. Gehen Sie zur Seite **"🔧 System-Verwaltung"**
3. Aktivieren Sie das Kontrollkästchen **"🔐 Admin-Modus aktivieren"**
4. Geben Sie das Passwort ein: `admin123`
5. Der Admin-Bereich wird freigeschaltet

## Admin-Funktionen

### 📊 System-Tab
- **System-Status**: Übersicht über alle Services
- **Datenbank-Statistiken**: Anzahl Dokumente, Speicherverbrauch
- **Performance-Metriken**: Antwortzeiten, Fehlerrate
- **Speicher-Nutzung**: RAM und Festplatte

### 📥 Import-Tab
- **Datei-Upload**: Einzelne Dokumente hochladen
- **Bulk-Import**: Mehrere Dateien gleichzeitig
- **CSV-Import**: Strukturierte Daten importieren
- **API-Import**: Daten von externen Quellen
- **Import-Verlauf**: Übersicht aller Importe

### 🔧 Wartung-Tab
- **Datenbank-Wartung**: Indizes optimieren, Bereinigung
- **Cache leeren**: System-Cache zurücksetzen
- **Backup erstellen**: Vollständige Datensicherung
- **System-Neustart**: Services neu starten
- **Konfiguration**: System-Einstellungen ändern

### 📋 Logs-Tab
- **System-Logs**: Alle System-Ereignisse
- **Fehler-Logs**: Nur Fehlermeldungen
- **Zugriffs-Logs**: Benutzer-Aktivitäten
- **Import-Logs**: Import-Protokolle
- **Performance-Logs**: Leistungsdaten

## Sicherheitshinweise

### ⚠️ Wichtige Sicherheitsmaßnahmen

1. **Passwort ändern** (Produktion):
   ```python
   # In web/app.py, Zeile 509:
   if password == "IHR_SICHERES_PASSWORT":
   ```

2. **Erweiterte Authentifizierung** implementieren:
   ```python
   # Beispiel für sichere Authentifizierung
   import bcrypt
   import secrets
   
   # Passwort-Hash verwenden statt Klartext
   password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
   ```

3. **Session-Management**:
   - Admin-Sessions automatisch ablaufen lassen
   - Mehrfach-Anmeldungen protokollieren
   - IP-Adressen-Beschränkungen

4. **Audit-Logging**:
   - Alle Admin-Aktionen protokollieren
   - Zeitstempel und Benutzer-IDs speichern
   - Kritische Änderungen extra markieren

## Häufige Admin-Aufgaben

### Datenbank-Wartung
```bash
# MongoDB-Indizes optimieren
./tools/optimize_database.sh

# Alte Daten archivieren
./tools/archive_old_data.sh

# Backup erstellen
./tools/backup.sh
```

### System-Überwachung
```bash
# System-Status prüfen
./status.sh

# Logs anzeigen
tail -f logs/web.log
tail -f logs/system.log

# Performance überwachen
docker stats
```

### Daten-Import
```bash
# CSV-Dateien importieren
./tools/import_csv.sh data/imports/finanzen_2023.csv

# PDF-Dokumente verarbeiten
./tools/import_pdf.sh data/imports/protokoll_2023.pdf

# Bulk-Import
./tools/bulk_import.sh data/imports/
```

## Konfiguration

### System-Konfiguration
Datei: `config/system_config.yaml`

```yaml
# Admin-Einstellungen
admin:
  password_hash: "bcrypt_hash_hier"
  session_timeout: 3600  # 1 Stunde
  max_login_attempts: 3
  
# Datenbank-Einstellungen
database:
  host: "localhost"
  port: 27017
  name: "gmunden_db"
  
# Import-Einstellungen
import:
  max_file_size: 100MB
  allowed_types: ["pdf", "csv", "xlsx", "docx"]
  auto_ocr: true
```

### Web-Interface-Konfiguration
Datei: `.streamlit/config.toml`

```toml
[server]
port = 12000
address = "0.0.0.0"
enableCORS = true
enableXsrfProtection = true

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

## Backup & Wiederherstellung

### Automatisches Backup
```bash
# Tägliches Backup einrichten
crontab -e

# Folgende Zeile hinzufügen:
0 2 * * * /pfad/zum/projekt/tools/backup.sh
```

### Manuelles Backup
```bash
# Vollständiges Backup
./tools/backup.sh --full

# Nur Datenbank
./tools/backup.sh --db-only

# Nur Dateien
./tools/backup.sh --files-only
```

### Wiederherstellung
```bash
# Aus Backup wiederherstellen
./tools/restore.sh /pfad/zum/backup.tar.gz

# Nur Datenbank wiederherstellen
./tools/restore.sh --db-only /pfad/zum/db_backup.sql
```

## Monitoring & Alerts

### System-Überwachung
- **CPU-Auslastung**: > 80% für > 5 Min
- **Speicher-Verbrauch**: > 90% verfügbarer RAM
- **Festplatte**: > 85% belegt
- **Datenbank-Verbindungen**: > 100 gleichzeitig

### Performance-Metriken
- **Antwortzeit Web-Interface**: < 2 Sekunden
- **Datenbank-Abfragen**: < 500ms
- **Suchanfragen**: < 1 Sekunde
- **Dokument-Upload**: < 30 Sekunden

### Fehler-Behandlung
- **Automatischer Neustart** bei kritischen Fehlern
- **E-Mail-Benachrichtigungen** bei Systemausfällen
- **Log-Rotation** zur Speicherplatz-Verwaltung

## Troubleshooting

### Häufige Probleme

#### Web-Interface reagiert nicht
```bash
# Service-Status prüfen
./status.sh

# Logs prüfen
tail -f logs/web.log

# Service neu starten
./stop.sh && ./start.sh
```

#### Datenbank-Verbindung fehlgeschlagen
```bash
# MongoDB-Status prüfen
docker ps | grep mongodb

# MongoDB-Logs
docker logs gmunden-transparenz-mongodb

# MongoDB neu starten
docker restart gmunden-transparenz-mongodb
```

#### Import-Fehler
```bash
# Import-Logs prüfen
tail -f logs/import.log

# Datei-Berechtigungen prüfen
ls -la data/imports/

# OCR-Service prüfen
curl http://localhost:8080/health
```

## Support-Kontakte

### Technischer Support
- **System-Logs**: `logs/system.log`
- **Fehler-Logs**: `logs/error.log`
- **Admin-Logs**: `logs/admin.log`

### Notfall-Kontakte
- **System-Administrator**: admin@gmunden.at
- **Technischer Support**: support@gmunden.at
- **Datenschutz-Beauftragter**: datenschutz@gmunden.at

---

## ⚠️ Sicherheitswarnung

**Das Standard-Passwort `admin123` ist nur für Tests geeignet!**

Für den produktiven Einsatz:
1. Ändern Sie das Passwort sofort
2. Implementieren Sie sichere Authentifizierung
3. Aktivieren Sie HTTPS
4. Beschränken Sie Admin-Zugang auf vertrauenswürdige IP-Adressen
5. Aktivieren Sie Audit-Logging für alle Admin-Aktionen

---

**Letzte Aktualisierung**: $(date '+%Y-%m-%d %H:%M:%S')