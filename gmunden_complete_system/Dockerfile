# 🐳 Gmunden Transparenz-System - Docker Container
# Optimiert für alle Unix-Systeme (Linux, macOS, FreeBSD)

FROM python:3.11-slim

# Metadaten
LABEL maintainer="Gmunden Transparenz Team"
LABEL version="2.2.0"
LABEL description="Gmunden Gemeinde Transparenz-System mit Bulk-Import"

# Umgebungsvariablen
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=12000
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200

# System-Updates und Abhängigkeiten (mit Fehlerbehandlung)
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    sqlite3 \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-eng \
    poppler-utils \
    libmagic1 \
    file \
    && rm -rf /var/lib/apt/lists/*

# ImageMagick optional installieren (falls verfügbar)
RUN apt-get update && \
    (apt-get install -y imagemagick ghostscript || echo "ImageMagick installation skipped") && \
    rm -rf /var/lib/apt/lists/*

# ImageMagick Policy für PDF-Verarbeitung anpassen (falls vorhanden)
RUN find /etc -name "policy.xml" -type f 2>/dev/null | \
    xargs -r sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' || \
    echo "ImageMagick policy not found, skipping PDF policy adjustment"

# Arbeitsverzeichnis
WORKDIR /app

# Python-Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Anwendung kopieren
COPY . .

# Verzeichnisse erstellen
RUN mkdir -p data/{cache,backup,uploads,exports} \
    && mkdir -p logs \
    && mkdir -p .streamlit

# Berechtigungen setzen
RUN chmod +x *.sh
RUN chmod 755 data/ logs/

# Streamlit-Konfiguration
COPY .streamlit/config.toml .streamlit/

# Gesundheitscheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:12000/_stcore/health || exit 1

# Port freigeben
EXPOSE 12000

# Volumes für persistente Daten
VOLUME ["/app/data", "/app/logs"]

# Startup-Script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Benutzer erstellen (Sicherheit)
RUN useradd -m -u 1000 gmunden && \
    chown -R gmunden:gmunden /app
USER gmunden

# Entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["streamlit", "run", "web/app.py", "--server.port", "12000", "--server.address", "0.0.0.0"]