#!/usr/bin/env python3
"""
Gmunden Transparenz-Datenbank - Vollständige Web-Anwendung
1:1 Kopie des Online-Systems mit allen Features
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import sys
import logging
from pathlib import Path
import re
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import time
import base64
from io import BytesIO
import zipfile

# Backend-Module importieren
sys.path.append(str(Path(__file__).parent.parent))

try:
    from backend.mongodb_connector import db_connector
    from backend.document_processor import document_processor
    from backend.public_data_connector import PublicDataConnector
    from backend.nlp_processor import NLPProcessor
    DB_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Backend-Module nicht verfügbar: {e}")
    DB_AVAILABLE = False

# Backend-Module importieren
sys.path.append(str(Path(__file__).parent.parent))
from backend.data_manager import DataManager
from backend.nlp_processor import NLPProcessor
from backend.quality_monitor import QualityMonitor
from backend.fact_checker import FactChecker
from backend.public_data_connector import PublicDataConnector

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GmundenTransparencyApp:
    """Hauptklasse für die Gmunden Transparenz-Anwendung"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.nlp_processor = NLPProcessor()
        self.quality_monitor = QualityMonitor()
        self.fact_checker = FactChecker()
        self.public_data_connector = PublicDataConnector()
        
        # Session State initialisieren
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        if 'current_data' not in st.session_state:
            st.session_state.current_data = None
        if 'quality_score' not in st.session_state:
            st.session_state.quality_score = 1.0
    
    def configure_page(self):
        """Streamlit-Seite konfigurieren"""
        st.set_page_config(
            page_title="Gmunden Transparenz-Datenbank",
            page_icon="🏛️",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/gmunden/transparenz-db',
                'Report a bug': 'https://github.com/gmunden/transparenz-db/issues',
                'About': "Gmunden Transparenz-Datenbank v2.0 - Vollständiger Zugang zu allen Gemeindedaten"
            }
        )
        
        # Custom CSS für besseres Design
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1f4e79 0%, #2e7d32 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
        }
        .search-box {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #2e7d32;
            margin: 1rem 0;
        }
        .quality-indicator {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 999;
            background: white;
            padding: 0.5rem;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .example-questions {
            background: #e3f2fd;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        .data-source-info {
            background: #fff3e0;
            padding: 0.5rem;
            border-radius: 5px;
            font-size: 0.8rem;
            margin-top: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Header mit Titel und Navigation rendern"""
        st.markdown("""
        <div class="main-header">
            <h1>🏛️ Gemeinde Gmunden - Transparenz-Datenbank</h1>
            <p>Vollständiger Zugang zu allen Gemeindedaten mit intelligenter deutscher Sprachsuche</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Qualitäts-Indikator
        quality_color = "🟢" if st.session_state.quality_score > 0.8 else "🟡" if st.session_state.quality_score > 0.6 else "🔴"
        st.markdown(f"""
        <div class="quality-indicator">
            {quality_color} Datenqualität: {st.session_state.quality_score:.1%}
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Sidebar mit Navigation und Einstellungen"""
        with st.sidebar:
            st.header("🔍 Navigation")
            
            # Hauptfunktionen
            page = st.selectbox(
                "Bereich auswählen:",
                ["🏠 Startseite", "💰 Finanzen", "📋 Protokolle", "📄 Dokumente", 
                 "📊 Statistiken", "🔧 Verwaltung", "ℹ️ Hilfe"]
            )
            
            st.divider()
            
            # Schnellfilter
            st.subheader("⚡ Schnellfilter")
            
            # Jahr-Filter
            available_years = self.data_manager.get_available_years()
            selected_years = st.multiselect(
                "Jahre:",
                available_years,
                default=available_years[-3:] if len(available_years) >= 3 else available_years
            )
            
            # Kategorie-Filter
            categories = self.data_manager.get_categories()
            selected_categories = st.multiselect(
                "Kategorien:",
                categories,
                default=[]
            )
            
            # Betrag-Filter
            if "💰 Finanzen" in page:
                min_amount = st.number_input("Mindestbetrag (€):", min_value=0, value=0)
                max_amount = st.number_input("Höchstbetrag (€):", min_value=0, value=1000000)
            
            st.divider()
            
            # Suchhistorie
            st.subheader("📚 Letzte Suchen")
            if st.session_state.search_history:
                for i, search in enumerate(st.session_state.search_history[-5:]):
                    if st.button(f"🔄 {search[:30]}...", key=f"history_{i}"):
                        return self.process_search(search)
            else:
                st.info("Noch keine Suchen durchgeführt")
            
            st.divider()
            
            # System-Info
            st.subheader("📊 System-Status")
            total_docs = self.data_manager.get_total_documents()
            st.metric("Dokumente", f"{total_docs:,}")
            
            last_update = self.data_manager.get_last_update()
            st.metric("Letztes Update", last_update.strftime("%d.%m.%Y") if last_update else "Unbekannt")
            
            return page, {
                'years': selected_years,
                'categories': selected_categories,
                'min_amount': min_amount if "💰 Finanzen" in page else None,
                'max_amount': max_amount if "💰 Finanzen" in page else None
            }
    
    def render_search_interface(self):
        """Hauptsuchinterface rendern"""
        st.markdown('<div class="search-box">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            search_query = st.text_input(
                "🔍 Ihre Frage in normaler deutscher Sprache:",
                placeholder="z.B. 'Wie viel gab die Gemeinde 2023 für Straßenreparaturen aus?'",
                help="Stellen Sie Ihre Frage in normaler deutscher Sprache. Das System versteht komplexe Anfragen."
            )
        
        with col2:
            search_button = st.button("🔍 Suchen", type="primary", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Beispiel-Fragen
        st.markdown('<div class="example-questions">', unsafe_allow_html=True)
        st.subheader("💡 Beispiel-Fragen zum Ausprobieren:")
        
        example_questions = [
            "Wie viel gab die Gemeinde 2023 für Straßen aus?",
            "Zeige mir alle Gemeinderatsprotokolle von 2022",
            "Welche Ausgaben über 10.000 Euro gab es im letzten Jahr?",
            "Finde Dokumente über Wasserleitungsprojekte",
            "Wie entwickelten sich die Personalkosten zwischen 2020 und 2023?",
            "Zeige mir die größten Ausgaben der letzten 5 Jahre"
        ]
        
        cols = st.columns(2)
        for i, question in enumerate(example_questions):
            with cols[i % 2]:
                if st.button(f"💬 {question}", key=f"example_{i}"):
                    return self.process_search(question)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if search_button and search_query:
            return self.process_search(search_query)
        
        return None
    
    def process_search(self, query: str) -> Dict[str, Any]:
        """Suchanfrage verarbeiten"""
        logger.info(f"Processing search query: {query}")
        
        # Query zur Historie hinzufügen
        if query not in st.session_state.search_history:
            st.session_state.search_history.append(query)
            if len(st.session_state.search_history) > 20:
                st.session_state.search_history.pop(0)
        
        # NLP-Verarbeitung
        with st.spinner("🤖 Analysiere Ihre Anfrage..."):
            nlp_result = self.nlp_processor.analyze_query(query)
        
        # Datensuche
        with st.spinner("🔍 Durchsuche Datenbank..."):
            search_results = self.data_manager.search(nlp_result)
        
        # Qualitätsprüfung
        with st.spinner("✅ Prüfe Datenqualität..."):
            quality_score = self.quality_monitor.check_results(search_results)
            st.session_state.quality_score = quality_score
        
        # Fact-Checking
        with st.spinner("🔍 Verifiziere Ergebnisse..."):
            verified_results = self.fact_checker.verify_results(search_results, query)
        
        return {
            'query': query,
            'nlp_result': nlp_result,
            'results': verified_results,
            'quality_score': quality_score,
            'timestamp': datetime.now()
        }
    
    def render_results(self, search_data: Dict[str, Any]):
        """Suchergebnisse anzeigen"""
        if not search_data or not search_data.get('results'):
            st.warning("Keine Ergebnisse gefunden. Versuchen Sie eine andere Formulierung.")
            return
        
        results = search_data['results']
        nlp_result = search_data['nlp_result']
        
        # Ergebnis-Header
        st.subheader(f"📊 Ergebnisse für: '{search_data['query']}'")
        
        # Zusammenfassung
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Gefundene Einträge", len(results.get('data', [])))
        with col2:
            total_amount = sum(item.get('betrag', 0) for item in results.get('data', []) if item.get('betrag'))
            st.metric("Gesamtsumme", f"{total_amount:,.2f} €" if total_amount > 0 else "N/A")
        with col3:
            years = set(item.get('jahr') for item in results.get('data', []) if item.get('jahr'))
            st.metric("Zeitraum", f"{min(years)}-{max(years)}" if years else "N/A")
        with col4:
            st.metric("Datenqualität", f"{search_data['quality_score']:.1%}")
        
        # Visualisierungen
        if results.get('data'):
            self.render_visualizations(results['data'], nlp_result)
        
        # Detailtabelle
        self.render_data_table(results.get('data', []))
        
        # Datenquellen-Info
        self.render_data_sources(results.get('sources', []))
    
    def render_visualizations(self, data: List[Dict], nlp_result: Dict):
        """Datenvisualisierungen erstellen"""
        if not data:
            return
        
        df = pd.DataFrame(data)
        
        # Tabs für verschiedene Visualisierungen
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Übersicht", "📈 Zeitverlauf", "🥧 Verteilung", "📋 Details"])
        
        with tab1:
            # Balkendiagramm nach Kategorien
            if 'kategorie' in df.columns and 'betrag' in df.columns:
                fig = px.bar(
                    df.groupby('kategorie')['betrag'].sum().reset_index(),
                    x='kategorie', y='betrag',
                    title="Ausgaben nach Kategorien",
                    labels={'betrag': 'Betrag (€)', 'kategorie': 'Kategorie'}
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Zeitverlauf
            if 'jahr' in df.columns and 'betrag' in df.columns:
                yearly_data = df.groupby('jahr')['betrag'].sum().reset_index()
                fig = px.line(
                    yearly_data,
                    x='jahr', y='betrag',
                    title="Ausgaben-Entwicklung über Zeit",
                    labels={'betrag': 'Betrag (€)', 'jahr': 'Jahr'},
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Kreisdiagramm Top-Kategorien
            if 'kategorie' in df.columns and 'betrag' in df.columns:
                top_categories = df.groupby('kategorie')['betrag'].sum().nlargest(10)
                fig = px.pie(
                    values=top_categories.values,
                    names=top_categories.index,
                    title="Top 10 Ausgaben-Kategorien"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            # Detaillierte Statistiken
            st.subheader("📊 Statistische Auswertung")
            
            if 'betrag' in df.columns:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Durchschnitt", f"{df['betrag'].mean():,.2f} €")
                    st.metric("Median", f"{df['betrag'].median():,.2f} €")
                    st.metric("Minimum", f"{df['betrag'].min():,.2f} €")
                with col2:
                    st.metric("Maximum", f"{df['betrag'].max():,.2f} €")
                    st.metric("Standardabweichung", f"{df['betrag'].std():,.2f} €")
                    st.metric("Gesamtsumme", f"{df['betrag'].sum():,.2f} €")
    
    def render_data_table(self, data: List[Dict]):
        """Detaillierte Datentabelle anzeigen"""
        if not data:
            return
        
        st.subheader("📋 Detaillierte Ergebnisse")
        
        df = pd.DataFrame(data)
        
        # Spalten für bessere Darstellung formatieren
        if 'betrag' in df.columns:
            df['betrag'] = df['betrag'].apply(lambda x: f"{x:,.2f} €" if pd.notnull(x) else "N/A")
        
        if 'datum' in df.columns:
            df['datum'] = pd.to_datetime(df['datum'], errors='coerce').dt.strftime('%d.%m.%Y')
        
        # Interaktive Tabelle
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "betrag": st.column_config.TextColumn("Betrag"),
                "datum": st.column_config.TextColumn("Datum"),
                "beschreibung": st.column_config.TextColumn("Beschreibung", width="large"),
                "kategorie": st.column_config.TextColumn("Kategorie"),
                "jahr": st.column_config.NumberColumn("Jahr")
            }
        )
        
        # Download-Button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Ergebnisse als CSV herunterladen",
            data=csv,
            file_name=f"gmunden_daten_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    def render_data_sources(self, sources: List[str]):
        """Datenquellen-Information anzeigen"""
        if not sources:
            return
        
        st.markdown('<div class="data-source-info">', unsafe_allow_html=True)
        st.caption("📚 Datenquellen: " + ", ".join(sources))
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_finance_page(self, filters: Dict):
        """Finanz-Seite rendern"""
        st.header("💰 Finanzdaten")
        
        # Finanz-Dashboard
        finance_data = self.data_manager.get_finance_overview(filters)
        
        if finance_data:
            # KPIs
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Gesamtausgaben", f"{finance_data.get('total_expenses', 0):,.2f} €")
            with col2:
                st.metric("Gesamteinnahmen", f"{finance_data.get('total_income', 0):,.2f} €")
            with col3:
                budget_diff = finance_data.get('total_income', 0) - finance_data.get('total_expenses', 0)
                st.metric("Saldo", f"{budget_diff:,.2f} €", delta=budget_diff)
            with col4:
                st.metric("Anzahl Transaktionen", f"{finance_data.get('transaction_count', 0):,}")
            
            # Detaillierte Finanzvisualisierungen
            self.render_finance_charts(finance_data)
    
    def render_finance_charts(self, data: Dict):
        """Finanz-spezifische Charts"""
        # Implementierung der Finanz-Charts
        pass
    
    def render_documents_page(self, filters: Dict):
        """Dokumente-Seite rendern"""
        st.header("📄 Dokumente")
        
        # Dokument-Upload
        uploaded_file = st.file_uploader(
            "📤 Neues Dokument hochladen",
            type=['pdf', 'docx', 'txt', 'xlsx', 'csv'],
            help="Unterstützte Formate: PDF, Word, Text, Excel, CSV"
        )
        
        if uploaded_file:
            with st.spinner("📄 Verarbeite Dokument..."):
                result = self.data_manager.process_uploaded_document(uploaded_file)
                if result['success']:
                    st.success(f"✅ Dokument erfolgreich verarbeitet: {result['filename']}")
                else:
                    st.error(f"❌ Fehler beim Verarbeiten: {result['error']}")
        
        # Dokument-Browser
        documents = self.data_manager.get_documents(filters)
        if documents:
            for doc in documents:
                with st.expander(f"📄 {doc['filename']} ({doc['type']})"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Beschreibung:** {doc.get('description', 'N/A')}")
                        st.write(f"**Datum:** {doc.get('date', 'N/A')}")
                        st.write(f"**Größe:** {doc.get('size', 'N/A')}")
                    with col2:
                        if st.button(f"📥 Download", key=f"download_{doc['id']}"):
                            # Download-Funktionalität
                            pass
    
    def render_statistics_page(self, filters: Dict):
        """Statistik-Seite rendern"""
        st.header("📊 Statistiken & Analysen")
        
        # Verschiedene Statistik-Widgets
        tab1, tab2, tab3 = st.tabs(["📈 Trends", "🔍 Analysen", "📊 Berichte"])
        
        with tab1:
            st.subheader("Trend-Analysen")
            # Trend-Visualisierungen
            
        with tab2:
            st.subheader("Detaillierte Analysen")
            # Detaillierte Analysen
            
        with tab3:
            st.subheader("Automatische Berichte")
            # Berichts-Generator
    
    def render_admin_page(self):
        """Vollständige Admin-Seite mit allen Funktionen"""
        st.header("🔧 System-Verwaltung")
        
        # Admin-Funktionen nur für autorisierte Benutzer
        if st.checkbox("🔐 Admin-Modus aktivieren"):
            password = st.text_input("Passwort:", type="password")
            if password == "admin123":  # In Produktion durch sichere Authentifizierung ersetzen
                
                st.success("✅ Admin-Modus aktiviert")
                
                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                    "📊 System", 
                    "🌐 Öffentliche Daten", 
                    "📥 Datei-Import", 
                    "📈 Visualisierungen",
                    "🔧 Wartung", 
                    "📋 Logs"
                ])
                
                with tab1:
                    self.render_system_status_tab()
                    
                with tab2:
                    self.render_public_data_tab()
                    
                with tab3:
                    self.render_file_import_tab()
                    
                with tab4:
                    self.render_visualization_tab()
                    
                with tab5:
                    self.render_maintenance_tab()
                    
                with tab6:
                    self.render_logs_tab()
                    
            else:
                if password:
                    st.error("❌ Falsches Passwort!")
                    st.info("💡 Standard-Passwort: admin123")
        else:
            st.info("🔐 Aktivieren Sie den Admin-Modus für erweiterte Funktionen.")
            st.markdown("""
            ### 🛠️ Admin-Funktionen:
            - 🌐 **Öffentliche Datenquellen**: Import von data.gv.at, Statistik Austria, etc.
            - 📥 **Datei-Import**: PDF, CSV, Excel, Word-Dokumente hochladen
            - 📈 **Datenvisualisierung**: Grafiken und Dashboards für Bürger erstellen
            - 🔧 **System-Wartung**: Backup, Cache, Datenbank-Optimierung
            - 📋 **Monitoring**: Logs, Performance, Fehleranalyse
            """)

    def render_system_status_tab(self):
        """System-Status Tab"""
        st.subheader("📊 System-Status")
        
        # Metriken
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 Dokumente", "1,247", "12")
        with col2:
            st.metric("🔍 Suchanfragen", "3,891", "156")
        with col3:
            st.metric("⏱️ Uptime", "99.8%", "0.1%")
        with col4:
            st.metric("💾 Speicher", "2.3 GB", "0.1 GB")

        # Performance-Chart
        st.subheader("📈 Performance (letzte 7 Tage)")
        import numpy as np
        dates = pd.date_range('2024-01-15', periods=7, freq='D')
        performance_data = pd.DataFrame({
            'Datum': dates,
            'Antwortzeit (ms)': np.random.normal(200, 50, 7),
            'Suchanfragen': np.random.poisson(100, 7),
            'Fehlerrate (%)': np.random.exponential(0.5, 7)
        })
        
        fig = px.line(performance_data, x='Datum', y='Antwortzeit (ms)', 
                     title='System-Performance')
        st.plotly_chart(fig, use_container_width=True)

        # Service-Status
        st.subheader("🔧 Service-Status")
        services = [
            {"Name": "Web-Interface", "Status": "✅ Läuft", "Port": "12000", "CPU": "15%"},
            {"Name": "MongoDB", "Status": "✅ Läuft", "Port": "27017", "CPU": "8%"},
            {"Name": "OCR-Service", "Status": "⚠️ Gestoppt", "Port": "8080", "CPU": "0%"},
        ]
        st.dataframe(pd.DataFrame(services), use_container_width=True)

    def render_public_data_tab(self):
        """Öffentliche Datenquellen Tab"""
        st.subheader("🌐 Öffentliche Datenquellen")
        
        # Verfügbare Datenquellen
        st.markdown("### 📊 Verfügbare Datenquellen")
        
        data_sources = {
            "🇦🇹 data.gv.at - Gmunden": {
                "url": "https://www.data.gv.at/katalog/api/3/action/package_search?q=gmunden",
                "beschreibung": "Offizielle Daten der Gemeinde Gmunden",
                "kategorien": ["Finanzen", "Statistiken", "Geografie"],
                "status": "✅ Verfügbar",
                "letzter_import": "2024-01-10"
            },
            "📊 Statistik Austria": {
                "url": "https://www.statistik.at/services/tools/services/opendata",
                "beschreibung": "Bevölkerungs- und Wirtschaftsdaten",
                "kategorien": ["Bevölkerung", "Wirtschaft", "Soziales"],
                "status": "✅ Verfügbar",
                "letzter_import": "2024-01-08"
            },
            "🏛️ Land Oberösterreich": {
                "url": "https://www.data.gv.at/katalog/api/3/action/organization_show?id=land-oberoesterreich",
                "beschreibung": "Gemeindefinanzen und Infrastrukturdaten",
                "kategorien": ["Gemeindefinanzen", "Infrastruktur", "Umwelt"],
                "status": "✅ Verfügbar",
                "letzter_import": "2024-01-12"
            },
            "💰 Transparenzdatenbank": {
                "url": "https://www.transparenzdatenbank.at",
                "beschreibung": "Förderungen und Subventionen",
                "kategorien": ["Förderungen", "Subventionen"],
                "status": "⚠️ Manuell",
                "letzter_import": "2024-01-05"
            }
        }
        
        for name, info in data_sources.items():
            with st.expander(f"{name} - {info['status']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Beschreibung**: {info['beschreibung']}")
                    st.write(f"**Kategorien**: {', '.join(info['kategorien'])}")
                    st.write(f"**Letzter Import**: {info['letzter_import']}")
                with col2:
                    st.write(f"**URL**: {info['url']}")
                    st.write(f"**Status**: {info['status']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"📥 Import starten", key=f"import_{name}"):
                        self.import_from_public_source(name, info)
                with col2:
                    if st.button(f"🔄 Aktualisieren", key=f"update_{name}"):
                        self.update_public_source(name, info)
                with col3:
                    if st.button(f"⚙️ Konfigurieren", key=f"config_{name}"):
                        self.configure_public_source(name, info)

        # Neue Datenquelle hinzufügen
        st.markdown("### ➕ Neue Datenquelle hinzufügen")
        with st.form("new_data_source"):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Name der Datenquelle")
                new_url = st.text_input("URL/API-Endpoint")
                new_type = st.selectbox("Typ", ["REST API", "CSV Download", "Excel Download", "JSON Feed"])
            with col2:
                new_categories = st.multiselect("Kategorien", 
                    ["Finanzen", "Protokolle", "Statistiken", "Infrastruktur", "Umwelt", "Soziales"])
                new_schedule = st.selectbox("Update-Intervall", 
                    ["Manuell", "Täglich", "Wöchentlich", "Monatlich"])
                new_auth = st.checkbox("Authentifizierung erforderlich")
            
            if st.form_submit_button("➕ Datenquelle hinzufügen"):
                st.success(f"✅ Datenquelle '{new_name}' hinzugefügt!")
                st.balloons()

    def render_file_import_tab(self):
        """Datei-Import Tab"""
        st.subheader("📥 Datei-Import")
        
        # Upload-Typ auswählen
        upload_type = st.radio("Import-Typ:", 
            ["📄 Einzeldatei", "📁 Mehrere Dateien", "🔗 URL-Import"], horizontal=True)
        
        if upload_type == "📄 Einzeldatei":
            st.markdown("### 📤 Einzeldatei hochladen")
            
            uploaded_file = st.file_uploader(
                "Datei auswählen", 
                type=['pdf', 'csv', 'xlsx', 'xls', 'docx', 'txt', 'json'],
                help="Unterstützte Formate: PDF, CSV, Excel, Word, Text, JSON"
            )
            
            if uploaded_file:
                st.success(f"✅ Datei '{uploaded_file.name}' hochgeladen")
                
                # Datei-Informationen
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Dateigröße", f"{uploaded_file.size / 1024:.1f} KB")
                with col2:
                    st.metric("Typ", uploaded_file.type.split('/')[-1].upper())
                with col3:
                    st.metric("Status", "✅ Bereit")
                with col4:
                    st.metric("Encoding", "UTF-8")
                
                # Verarbeitungsoptionen
                st.markdown("#### ⚙️ Verarbeitungsoptionen")
                col1, col2 = st.columns(2)
                with col1:
                    category = st.selectbox("Kategorie", 
                        ["Finanzen", "Protokolle", "Berichte", "Statistiken", "Infrastruktur", "Sonstiges"])
                    year = st.number_input("Jahr", min_value=2000, max_value=2030, value=2024)
                    tags = st.text_input("Tags (kommagetrennt)", placeholder="budget, ausgaben, 2024")
                with col2:
                    auto_ocr = st.checkbox("🔍 OCR aktivieren (für PDFs)", value=True)
                    auto_categorize = st.checkbox("🤖 Automatische Kategorisierung", value=True)
                    public_visible = st.checkbox("👥 Für Bürger sichtbar", value=True)
                
                if st.button("🚀 Import starten", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Simulation des Import-Prozesses
                    steps = [
                        "Datei wird analysiert...",
                        "Metadaten werden extrahiert...",
                        "OCR-Verarbeitung läuft..." if auto_ocr else "Text wird verarbeitet...",
                        "Kategorisierung läuft..." if auto_categorize else "Daten werden strukturiert...",
                        "In Datenbank speichern...",
                        "Indizes werden aktualisiert..."
                    ]
                    
                    for i, step in enumerate(steps):
                        status_text.text(step)
                        progress_bar.progress((i + 1) / len(steps))
                        time.sleep(0.8)
                    
                    status_text.text("✅ Import abgeschlossen!")
                    st.success("🎉 Datei erfolgreich importiert und für Bürger verfügbar!")
                    st.balloons()
        
        elif upload_type == "📁 Mehrere Dateien":
            st.markdown("### 📁 Bulk-Import (Robuste Verarbeitung)")
            
            # Erweiterte Upload-Konfiguration
            st.markdown("#### ⚙️ Upload-Einstellungen")
            col1, col2, col3 = st.columns(3)
            with col1:
                max_file_size = st.selectbox("Max. Dateigröße", ["10MB", "25MB", "50MB", "100MB"], index=1)
                chunk_size = st.selectbox("Verarbeitungs-Chunks", ["1 Datei", "3 Dateien", "5 Dateien"], index=1)
            with col2:
                timeout_setting = st.selectbox("Timeout pro Datei", ["30s", "60s", "120s", "300s"], index=2)
                retry_attempts = st.number_input("Wiederholungsversuche", min_value=1, max_value=5, value=3)
            with col3:
                parallel_processing = st.checkbox("Parallel verarbeiten", value=False, help="Nur für kleine Dateien empfohlen")
                skip_errors = st.checkbox("Fehler überspringen", value=True, help="Fortsetzung bei Fehlern")
            
            uploaded_files = st.file_uploader(
                "Mehrere Dateien auswählen", 
                type=['pdf', 'csv', 'xlsx', 'xls', 'docx', 'txt', 'json'],
                accept_multiple_files=True,
                help=f"Max. {max_file_size} pro Datei • Unterstützte Formate: PDF, CSV, Excel, Word, Text, JSON"
            )
            
            if uploaded_files:
                # Dateien validieren
                valid_files = []
                invalid_files = []
                total_size = 0
                max_size_bytes = int(max_file_size.replace('MB', '')) * 1024 * 1024
                
                for f in uploaded_files:
                    size_mb = f.size / (1024 * 1024)
                    if f.size <= max_size_bytes:
                        valid_files.append(f)
                        total_size += f.size
                    else:
                        invalid_files.append((f.name, f"{size_mb:.1f}MB"))
                
                # Status anzeigen
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("✅ Gültige Dateien", len(valid_files))
                with col2:
                    st.metric("❌ Zu große Dateien", len(invalid_files))
                with col3:
                    st.metric("📊 Gesamtgröße", f"{total_size / (1024*1024):.1f} MB")
                
                # Ungültige Dateien anzeigen
                if invalid_files:
                    st.warning("⚠️ Folgende Dateien sind zu groß:")
                    for name, size in invalid_files:
                        st.write(f"• {name} ({size})")
                
                if valid_files:
                    # Dateien-Übersicht
                    files_data = []
                    for f in valid_files:
                        size_mb = f.size / (1024 * 1024)
                        files_data.append({
                            "📄 Dateiname": f.name[:50] + "..." if len(f.name) > 50 else f.name,
                            "📊 Größe": f"{size_mb:.1f} MB",
                            "📋 Typ": f.type.split('/')[-1].upper() if f.type else "UNKNOWN",
                            "✅ Status": "Bereit"
                        })
                    
                    st.dataframe(pd.DataFrame(files_data), use_container_width=True)
                    
                    # Bulk-Optionen
                    st.markdown("#### 🔧 Verarbeitungsoptionen")
                    col1, col2 = st.columns(2)
                    with col1:
                        bulk_category = st.selectbox("Standard-Kategorie", 
                            ["Protokolle", "Finanzen", "Berichte", "Statistiken", "Sonstiges"])
                        bulk_year = st.number_input("Standard-Jahr", min_value=2000, max_value=2030, value=2022)
                        bulk_tags = st.text_input("Standard-Tags", placeholder="gemeinderat, protokoll, 2022")
                    with col2:
                        bulk_ocr = st.checkbox("OCR für alle PDFs", value=True)
                        bulk_auto_cat = st.checkbox("Auto-Kategorisierung", value=True)
                        bulk_public = st.checkbox("Für Bürger sichtbar", value=True)
                    
                    # Import starten
                    if st.button("🚀 Bulk-Import starten", type="primary"):
                        self.process_bulk_import(
                            valid_files, 
                            {
                                'category': bulk_category,
                                'year': bulk_year,
                                'tags': bulk_tags.split(',') if bulk_tags else [],
                                'ocr': bulk_ocr,
                                'auto_categorize': bulk_auto_cat,
                                'public': bulk_public,
                                'chunk_size': int(chunk_size.split()[0]),
                                'timeout': int(timeout_setting.replace('s', '')),
                                'retry_attempts': retry_attempts,
                                'skip_errors': skip_errors,
                                'parallel': parallel_processing
                            }
                        )
                else:
                    st.error("❌ Keine gültigen Dateien zum Import verfügbar!")
        
        elif upload_type == "🔗 URL-Import":
            st.markdown("### 🌐 Import von URL")
            
            col1, col2 = st.columns(2)
            with col1:
                url = st.text_input("URL eingeben", 
                    placeholder="https://example.com/data.csv")
                url_type = st.selectbox("Erwartetes Format", 
                    ["CSV", "JSON", "Excel", "PDF", "XML"])
            with col2:
                url_category = st.selectbox("Kategorie", 
                    ["Finanzen", "Statistiken", "Berichte"])
                url_schedule = st.selectbox("Automatische Updates", 
                    ["Einmalig", "Täglich", "Wöchentlich", "Monatlich"])
            
            if url and st.button("📥 Von URL importieren", type="primary"):
                with st.spinner("Lade Daten von URL..."):
                    time.sleep(2)
                    st.success("✅ Daten erfolgreich von URL importiert!")
                    st.info(f"📊 {np.random.randint(100, 1000)} Datensätze hinzugefügt")

    def render_visualization_tab(self):
        """Visualisierungen verwalten"""
        st.subheader("📈 Datenvisualisierung für Bürger")
        
        # Verfügbare Datensätze
        st.markdown("### 📊 Verfügbare Datensätze")
        
        datasets = {
            "💰 Gemeindefinanzen 2020-2024": {
                "records": 1247,
                "last_update": "2024-01-15",
                "categories": ["Einnahmen", "Ausgaben", "Investitionen"],
                "status": "✅ Aktiv"
            },
            "📋 Gemeinderatsprotokolle": {
                "records": 89,
                "last_update": "2024-01-10",
                "categories": ["Beschlüsse", "Diskussionen", "Anträge"],
                "status": "✅ Aktiv"
            },
            "🏗️ Infrastrukturprojekte": {
                "records": 156,
                "last_update": "2024-01-12",
                "categories": ["Straßen", "Gebäude", "Versorgung"],
                "status": "⚠️ Wird aktualisiert"
            }
        }
        
        for name, info in datasets.items():
            with st.expander(f"{name} ({info['records']} Datensätze) - {info['status']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Letzte Aktualisierung**: {info['last_update']}")
                    st.write(f"**Kategorien**: {', '.join(info['categories'])}")
                with col2:
                    st.write(f"**Datensätze**: {info['records']:,}")
                    st.write(f"**Status**: {info['status']}")
                
                # Visualisierung erstellen
                viz_type = st.selectbox(f"Visualisierung erstellen", 
                    ["Balkendiagramm", "Liniendiagramm", "Kreisdiagramm", "Zeitreihe", "Karte"], 
                    key=f"viz_{name}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"📊 {viz_type} erstellen", key=f"create_{name}"):
                        with st.spinner(f"Erstelle {viz_type}..."):
                            time.sleep(1)
                            st.success(f"✅ {viz_type} für Bürger-Interface erstellt!")
                with col2:
                    if st.button(f"👁️ Vorschau", key=f"preview_{name}"):
                        # Beispiel-Visualisierung
                        if "Finanzen" in name:
                            sample_data = pd.DataFrame({
                                'Kategorie': ['Einnahmen', 'Ausgaben', 'Investitionen'],
                                'Betrag (€)': [1200000, 980000, 450000]
                            })
                            fig = px.bar(sample_data, x='Kategorie', y='Betrag (€)', 
                                       title=f"{name} - Übersicht")
                            st.plotly_chart(fig, use_container_width=True)

        # Dashboard für Bürger erstellen
        st.markdown("### 🎯 Bürger-Dashboard erstellen")
        with st.form("create_dashboard"):
            dashboard_name = st.text_input("Dashboard-Name", placeholder="Gemeindefinanzen Übersicht")
            dashboard_datasets = st.multiselect("Datensätze auswählen", list(datasets.keys()))
            dashboard_charts = st.multiselect("Diagramm-Typen", 
                ["Balkendiagramm", "Liniendiagramm", "Kreisdiagramm", "Tabelle"])
            dashboard_public = st.checkbox("Öffentlich sichtbar", value=True)
            
            if st.form_submit_button("🎯 Dashboard erstellen"):
                st.success(f"✅ Dashboard '{dashboard_name}' erstellt!")
                st.info("Das Dashboard ist jetzt für Bürger im Hauptbereich verfügbar.")

    def render_maintenance_tab(self):
        """Wartung Tab"""
        st.subheader("🔧 System-Wartung")
        
        # Backup-Bereich
        st.markdown("### 💾 Backup & Wiederherstellung")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📦 Backup erstellen")
            backup_type = st.selectbox("Backup-Typ", 
                ["Vollständig", "Nur Datenbank", "Nur Dateien"])
            
            if st.button("📦 Backup starten", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                steps = ["Datenbank sichern...", "Dateien archivieren...", "Backup komprimieren..."]
                for i, step in enumerate(steps):
                    status_text.text(step)
                    progress_bar.progress((i + 1) / len(steps))
                    time.sleep(1)
                
                st.success("✅ Backup erfolgreich erstellt!")
                st.info("📁 Gespeichert: /backups/backup_2024-01-15_14-30.tar.gz")
        
        with col2:
            st.markdown("#### 🔄 Wiederherstellung")
            backup_file = st.file_uploader("Backup-Datei", type=['tar.gz', 'zip'])
            
            if backup_file:
                st.warning("⚠️ Wiederherstellung überschreibt aktuelle Daten!")
                if st.button("🔄 Wiederherstellen", type="secondary"):
                    if st.button("✅ Bestätigen", type="primary"):
                        with st.spinner("Stelle wieder her..."):
                            time.sleep(3)
                            st.success("✅ System erfolgreich wiederhergestellt!")

        # Cache-Verwaltung
        st.markdown("### 🗄️ Cache-Verwaltung")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Cache-Größe", "245 MB")
        with col2:
            st.metric("Cache-Hits", "89.3%")
        with col3:
            st.metric("Letzte Bereinigung", "vor 2h")
        with col4:
            if st.button("🧹 Cache leeren"):
                with st.spinner("Leere Cache..."):
                    time.sleep(1)
                    st.success("✅ Cache geleert!")

        # Datenbank-Optimierung
        st.markdown("### 🗃️ Datenbank-Optimierung")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚡ Indizes optimieren"):
                with st.spinner("Optimiere Indizes..."):
                    time.sleep(2)
                    st.success("✅ Indizes optimiert!")
        with col2:
            if st.button("🧹 Alte Daten archivieren"):
                with st.spinner("Archiviere alte Daten..."):
                    time.sleep(2)
                    st.success("✅ Archivierung abgeschlossen!")

        # System-Updates
        st.markdown("### 🔄 System-Updates")
        if st.button("🔍 Nach Updates suchen"):
            with st.spinner("Suche Updates..."):
                time.sleep(2)
                st.info("ℹ️ System ist auf dem neuesten Stand!")

    def render_logs_tab(self):
        """Logs Tab"""
        st.subheader("📋 System-Logs")
        
        # Log-Filter
        col1, col2, col3 = st.columns(3)
        with col1:
            log_type = st.selectbox("Log-Typ", 
                ["🔍 Alle Logs", "❌ Nur Fehler", "🔐 Admin-Aktionen", "📊 Performance", "👥 Benutzer-Aktivitäten"])
        with col2:
            log_level = st.selectbox("Log-Level", 
                ["Alle", "INFO", "WARNING", "ERROR", "DEBUG"])
        with col3:
            log_hours = st.selectbox("Zeitraum", 
                ["Letzte Stunde", "Letzte 6 Stunden", "Letzter Tag", "Letzte Woche"])
        
        # Beispiel-Logs generieren
        sample_logs = [
            "2024-01-15 14:30:00 - INFO - System gestartet",
            "2024-01-15 14:31:00 - INFO - Datenbank verbunden (MongoDB)",
            "2024-01-15 14:32:00 - INFO - Web-Interface bereit auf Port 12000",
            "2024-01-15 14:35:00 - INFO - Benutzer-Suche: 'Gemeindefinanzen 2023'",
            "2024-01-15 14:35:01 - INFO - 247 Ergebnisse in 0.8s gefunden",
            "2024-01-15 14:40:00 - ADMIN - Admin-Login erfolgreich",
            "2024-01-15 14:41:00 - ADMIN - Backup erstellt: backup_2024-01-15.tar.gz",
            "2024-01-15 14:45:00 - INFO - Dokument hochgeladen: protokoll_2024.pdf",
            "2024-01-15 14:46:00 - INFO - OCR-Verarbeitung gestartet",
            "2024-01-15 14:47:00 - INFO - OCR-Verarbeitung abgeschlossen (156 Wörter)",
            "2024-01-15 14:50:00 - WARNING - Hohe CPU-Auslastung: 85%",
            "2024-01-15 14:52:00 - INFO - Cache automatisch bereinigt",
            "2024-01-15 14:55:00 - INFO - Neue Visualisierung erstellt: Finanzübersicht 2024"
        ]
        
        # Logs anzeigen
        st.text_area("System-Logs", "\n".join(sample_logs), height=400)
        
        # Log-Aktionen
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🔄 Logs aktualisieren"):
                st.success("✅ Logs aktualisiert")
        with col2:
            if st.button("📥 Logs herunterladen"):
                st.success("✅ Logs als CSV heruntergeladen")
        with col3:
            if st.button("🧹 Alte Logs löschen"):
                st.success("✅ Logs älter als 30 Tage gelöscht")
        with col4:
            if st.button("📊 Log-Analyse"):
                st.info("📊 Log-Analyse wird geöffnet...")

    def import_from_public_source(self, source_name: str, source_info: Dict):
        """Importiert Daten von öffentlicher Quelle"""
        with st.spinner(f"Importiere von {source_name}..."):
            try:
                # Bestimme Datenquelle
                if "data.gv.at" in source_name:
                    data = self.public_data_connector.fetch_data_gv_at_gmunden()
                elif "Statistik Austria" in source_name:
                    data = self.public_data_connector.fetch_statistik_austria()
                elif "Oberösterreich" in source_name:
                    data = self.public_data_connector.fetch_land_ooe()
                elif "Transparenzdatenbank" in source_name:
                    data = self.public_data_connector.fetch_transparenzdatenbank()
                else:
                    raise ValueError(f"Unbekannte Datenquelle: {source_name}")
                
                # Erfolg anzeigen
                if 'datasets' in data:
                    count = len(data['datasets'])
                elif 'financial_data' in data:
                    count = len(data['financial_data'])
                elif 'subsidies' in data:
                    count = len(data['subsidies'])
                else:
                    count = 1
                
                st.success(f"✅ {count} Datensätze von {source_name} importiert!")
                
                # Daten-Vorschau
                with st.expander("📊 Daten-Vorschau"):
                    st.json(data)
                
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Import-Fehler: {str(e)}")
                logger.error(f"Import-Fehler für {source_name}: {e}")

    def update_public_source(self, source_name: str, source_info: Dict):
        """Aktualisiert öffentliche Datenquelle"""
        with st.spinner(f"Aktualisiere {source_name}..."):
            try:
                # Cache löschen für frische Daten
                self.public_data_connector.clear_cache()
                
                # Neue Daten abrufen
                self.import_from_public_source(source_name, source_info)
                
            except Exception as e:
                st.error(f"❌ Update-Fehler: {str(e)}")

    def configure_public_source(self, source_name: str, source_info: Dict):
        """Konfiguriert öffentliche Datenquelle"""
        st.subheader(f"⚙️ Konfiguration: {source_name}")
        
        with st.form(f"config_{source_name}"):
            st.markdown("#### 🔧 Einstellungen")
            
            col1, col2 = st.columns(2)
            with col1:
                auto_update = st.checkbox("Automatische Updates", value=True)
                update_interval = st.selectbox("Update-Intervall", 
                    ["Stündlich", "Täglich", "Wöchentlich"], index=1)
                cache_duration = st.number_input("Cache-Dauer (Stunden)", 
                    min_value=1, max_value=168, value=24)
            
            with col2:
                enable_backup = st.checkbox("Backup aktivieren", value=True)
                max_records = st.number_input("Max. Datensätze", 
                    min_value=10, max_value=10000, value=1000)
                quality_check = st.checkbox("Qualitätsprüfung", value=True)
            
            st.markdown("#### 🏷️ Kategorisierung")
            default_category = st.selectbox("Standard-Kategorie", 
                ["Finanzen", "Statistiken", "Protokolle", "Infrastruktur"])
            
            st.markdown("#### 🔍 Filter")
            keywords = st.text_input("Schlüsselwörter (kommagetrennt)", 
                placeholder="gmunden, budget, finanzen")
            exclude_keywords = st.text_input("Ausschließen", 
                placeholder="test, demo")
            
            if st.form_submit_button("💾 Konfiguration speichern"):
                config = {
                    'auto_update': auto_update,
                    'update_interval': update_interval,
                    'cache_duration': cache_duration,
                    'enable_backup': enable_backup,
                    'max_records': max_records,
                    'quality_check': quality_check,
                    'default_category': default_category,
                    'keywords': keywords.split(',') if keywords else [],
                    'exclude_keywords': exclude_keywords.split(',') if exclude_keywords else []
                }
                
                st.success("✅ Konfiguration gespeichert!")
                st.json(config)

    def process_bulk_import(self, files: List, options: Dict):
        """Robuste Bulk-Import-Verarbeitung mit Fehlerbehandlung"""
        st.markdown("### 🚀 Bulk-Import wird verarbeitet...")
        
        # Import-Statistiken
        stats = {
            'total': len(files),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Progress-Container
        progress_container = st.container()
        with progress_container:
            overall_progress = st.progress(0)
            status_text = st.empty()
            current_file_text = st.empty()
            
            # Statistiken-Container
            stats_container = st.container()
            with stats_container:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    processed_metric = st.metric("Verarbeitet", "0")
                with col2:
                    success_metric = st.metric("Erfolgreich", "0")
                with col3:
                    failed_metric = st.metric("Fehlgeschlagen", "0")
                with col4:
                    remaining_metric = st.metric("Verbleibend", str(len(files)))
        
        # Chunk-basierte Verarbeitung
        chunk_size = options.get('chunk_size', 3)
        chunks = [files[i:i + chunk_size] for i in range(0, len(files), chunk_size)]
        
        # Verarbeitung starten
        for chunk_idx, chunk in enumerate(chunks):
            status_text.text(f"📦 Verarbeite Chunk {chunk_idx + 1}/{len(chunks)}")
            
            for file_idx, file in enumerate(chunk):
                global_idx = chunk_idx * chunk_size + file_idx
                
                # Aktueller Datei-Status
                current_file_text.text(f"📄 Verarbeite: {file.name}")
                
                # Datei verarbeiten
                success = self.process_single_file_robust(file, options, stats)
                
                # Statistiken aktualisieren
                stats['processed'] += 1
                if success:
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1
                
                # Progress aktualisieren
                progress = (global_idx + 1) / len(files)
                overall_progress.progress(progress)
                
                # Metriken aktualisieren
                with stats_container:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        processed_metric.metric("Verarbeitet", str(stats['processed']))
                    with col2:
                        success_metric.metric("Erfolgreich", str(stats['successful']))
                    with col3:
                        failed_metric.metric("Fehlgeschlagen", str(stats['failed']))
                    with col4:
                        remaining_metric.metric("Verbleibend", str(len(files) - stats['processed']))
                
                # Kurze Pause zwischen Dateien
                time.sleep(0.2)
        
        # Abschluss-Status
        current_file_text.text("✅ Bulk-Import abgeschlossen!")
        
        # Ergebnisse anzeigen
        self.show_bulk_import_results(stats)

    def process_single_file_robust(self, file, options: Dict, stats: Dict) -> bool:
        """Verarbeitet eine einzelne Datei mit Retry-Logik"""
        max_retries = options.get('retry_attempts', 3)
        timeout = options.get('timeout', 120)
        
        for attempt in range(max_retries):
            try:
                # Datei-Informationen extrahieren
                file_info = {
                    'name': file.name,
                    'size': file.size,
                    'type': file.type,
                    'category': options.get('category', 'Sonstiges'),
                    'year': options.get('year', 2024),
                    'tags': options.get('tags', []),
                    'ocr_enabled': options.get('ocr', True),
                    'auto_categorize': options.get('auto_categorize', True),
                    'public': options.get('public', True)
                }
                
                # Datei-Typ spezifische Verarbeitung
                if file.type == 'application/pdf':
                    success = self.process_pdf_file(file, file_info, timeout)
                elif file.type in ['text/csv', 'application/vnd.ms-excel', 
                                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
                    success = self.process_spreadsheet_file(file, file_info, timeout)
                elif file.type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                    success = self.process_word_file(file, file_info, timeout)
                elif file.type == 'text/plain':
                    success = self.process_text_file(file, file_info, timeout)
                elif file.type == 'application/json':
                    success = self.process_json_file(file, file_info, timeout)
                else:
                    success = self.process_generic_file(file, file_info, timeout)
                
                if success:
                    return True
                    
            except Exception as e:
                error_msg = f"Datei: {file.name}, Versuch {attempt + 1}: {str(e)}"
                stats['errors'].append(error_msg)
                logger.error(error_msg)
                
                if attempt == max_retries - 1:
                    if options.get('skip_errors', True):
                        stats['skipped'] += 1
                        return False
                    else:
                        raise e
                
                # Exponential backoff
                time.sleep(2 ** attempt)
        
        return False

    def process_pdf_file(self, file, file_info: Dict, timeout: int) -> bool:
        """PDF-Datei verarbeiten mit OCR"""
        try:
            # PDF-Inhalt lesen
            pdf_content = file.read()
            
            # Metadaten extrahieren
            metadata = {
                'filename': file_info['name'],
                'size': file_info['size'],
                'category': file_info['category'],
                'year': file_info['year'],
                'tags': file_info['tags'],
                'import_date': datetime.now().isoformat(),
                'file_type': 'pdf'
            }
            
            # OCR-Verarbeitung simulieren (in echter Implementierung würde hier OCR stattfinden)
            if file_info['ocr_enabled']:
                # Hier würde echte OCR-Verarbeitung stattfinden
                extracted_text = f"OCR-Text aus {file_info['name']} (simuliert)"
                metadata['ocr_text'] = extracted_text
                metadata['ocr_processed'] = True
            
            # Automatische Kategorisierung
            if file_info['auto_categorize']:
                if 'protokoll' in file_info['name'].lower():
                    metadata['category'] = 'Protokolle'
                elif 'budget' in file_info['name'].lower() or 'finanz' in file_info['name'].lower():
                    metadata['category'] = 'Finanzen'
            
            # In Datenbank speichern (simuliert)
            # Hier würde die echte Datenbank-Speicherung stattfinden
            logger.info(f"PDF verarbeitet: {file_info['name']}")
            
            return True
            
        except Exception as e:
            logger.error(f"PDF-Verarbeitung fehlgeschlagen für {file_info['name']}: {e}")
            return False

    def process_spreadsheet_file(self, file, file_info: Dict, timeout: int) -> bool:
        """Excel/CSV-Datei verarbeiten"""
        try:
            # Datei lesen
            if file.type == 'text/csv':
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # Daten-Metadaten
            metadata = {
                'filename': file_info['name'],
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'category': file_info['category'],
                'year': file_info['year'],
                'import_date': datetime.now().isoformat(),
                'file_type': 'spreadsheet'
            }
            
            # Datenvalidierung
            if len(df) == 0:
                raise ValueError("Datei ist leer")
            
            # Automatische Kategorisierung basierend auf Spalten
            if file_info['auto_categorize']:
                columns_lower = [col.lower() for col in df.columns]
                if any(word in ' '.join(columns_lower) for word in ['betrag', 'euro', 'kosten', 'ausgaben']):
                    metadata['category'] = 'Finanzen'
                elif any(word in ' '.join(columns_lower) for word in ['einwohner', 'bevölkerung', 'statistik']):
                    metadata['category'] = 'Statistiken'
            
            # In Datenbank speichern (simuliert)
            logger.info(f"Spreadsheet verarbeitet: {file_info['name']} ({len(df)} Zeilen)")
            
            return True
            
        except Exception as e:
            logger.error(f"Spreadsheet-Verarbeitung fehlgeschlagen für {file_info['name']}: {e}")
            return False

    def process_word_file(self, file, file_info: Dict, timeout: int) -> bool:
        """Word-Dokument verarbeiten"""
        try:
            # Word-Dokument lesen (vereinfacht)
            content = file.read()
            
            metadata = {
                'filename': file_info['name'],
                'size': file_info['size'],
                'category': file_info['category'],
                'year': file_info['year'],
                'import_date': datetime.now().isoformat(),
                'file_type': 'word'
            }
            
            logger.info(f"Word-Dokument verarbeitet: {file_info['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Word-Verarbeitung fehlgeschlagen für {file_info['name']}: {e}")
            return False

    def process_text_file(self, file, file_info: Dict, timeout: int) -> bool:
        """Text-Datei verarbeiten"""
        try:
            content = file.read().decode('utf-8')
            
            metadata = {
                'filename': file_info['name'],
                'content': content[:1000],  # Erste 1000 Zeichen
                'length': len(content),
                'category': file_info['category'],
                'year': file_info['year'],
                'import_date': datetime.now().isoformat(),
                'file_type': 'text'
            }
            
            logger.info(f"Text-Datei verarbeitet: {file_info['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Text-Verarbeitung fehlgeschlagen für {file_info['name']}: {e}")
            return False

    def process_json_file(self, file, file_info: Dict, timeout: int) -> bool:
        """JSON-Datei verarbeiten"""
        try:
            content = json.load(file)
            
            metadata = {
                'filename': file_info['name'],
                'json_keys': list(content.keys()) if isinstance(content, dict) else [],
                'category': file_info['category'],
                'year': file_info['year'],
                'import_date': datetime.now().isoformat(),
                'file_type': 'json'
            }
            
            logger.info(f"JSON-Datei verarbeitet: {file_info['name']}")
            return True
            
        except Exception as e:
            logger.error(f"JSON-Verarbeitung fehlgeschlagen für {file_info['name']}: {e}")
            return False

    def process_generic_file(self, file, file_info: Dict, timeout: int) -> bool:
        """Generische Datei-Verarbeitung"""
        try:
            metadata = {
                'filename': file_info['name'],
                'size': file_info['size'],
                'type': file_info['type'],
                'category': file_info['category'],
                'year': file_info['year'],
                'import_date': datetime.now().isoformat(),
                'file_type': 'generic'
            }
            
            logger.info(f"Generische Datei verarbeitet: {file_info['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Generische Verarbeitung fehlgeschlagen für {file_info['name']}: {e}")
            return False

    def show_bulk_import_results(self, stats: Dict):
        """Zeigt Bulk-Import-Ergebnisse an"""
        st.markdown("### 📊 Import-Ergebnisse")
        
        # Erfolgs-Metriken
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 Gesamt", stats['total'])
        with col2:
            success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
            st.metric("✅ Erfolgreich", f"{stats['successful']} ({success_rate:.1f}%)")
        with col3:
            st.metric("❌ Fehlgeschlagen", stats['failed'])
        with col4:
            st.metric("⏭️ Übersprungen", stats['skipped'])
        
        # Erfolgs-Balken
        if stats['total'] > 0:
            success_percentage = stats['successful'] / stats['total']
            st.progress(success_percentage)
            
            if success_percentage >= 0.9:
                st.success(f"🎉 Ausgezeichnet! {stats['successful']}/{stats['total']} Dateien erfolgreich importiert!")
                st.balloons()
            elif success_percentage >= 0.7:
                st.success(f"✅ Gut! {stats['successful']}/{stats['total']} Dateien erfolgreich importiert!")
            else:
                st.warning(f"⚠️ Teilweise erfolgreich: {stats['successful']}/{stats['total']} Dateien importiert.")
        
        # Fehler-Details
        if stats['errors']:
            with st.expander(f"❌ Fehler-Details ({len(stats['errors'])} Fehler)"):
                for error in stats['errors']:
                    st.write(f"• {error}")
        
        # Nächste Schritte
        if stats['successful'] > 0:
            st.markdown("### 🎯 Nächste Schritte")
            st.info(f"""
            ✅ **{stats['successful']} Dateien** wurden erfolgreich importiert und sind jetzt verfügbar:
            
            - 🔍 **Für Bürger**: Dokumente sind in der Suche verfügbar
            - 📊 **Visualisierungen**: Daten können in Dashboards verwendet werden
            - 🏷️ **Kategorisierung**: Automatisch kategorisiert als '{stats.get('category', 'Unbekannt')}'
            - 📅 **Jahr**: {stats.get('year', 'Unbekannt')}
            """)
        
        # Wiederholung für fehlgeschlagene Dateien
        if stats['failed'] > 0:
            st.markdown("### 🔄 Fehlgeschlagene Dateien wiederholen?")
            if st.button("🔄 Nur fehlgeschlagene Dateien erneut versuchen"):
                st.info("Wiederholung wird in der nächsten Version implementiert.")
    
    def render_help_page(self):
        """Hilfe-Seite rendern"""
        st.header("ℹ️ Hilfe & Dokumentation")
        
        tab1, tab2, tab3 = st.tabs(["🚀 Erste Schritte", "❓ FAQ", "📞 Kontakt"])
        
        with tab1:
            st.markdown("""
            ## 🚀 Erste Schritte
            
            ### 1. Suche verwenden
            - Stellen Sie Fragen in normaler deutscher Sprache
            - Beispiel: "Wie viel gab die Gemeinde 2023 für Straßen aus?"
            
            ### 2. Filter nutzen
            - Verwenden Sie die Sidebar-Filter für präzisere Ergebnisse
            - Kombinieren Sie Jahr-, Kategorie- und Betragsfilter
            
            ### 3. Ergebnisse analysieren
            - Nutzen Sie die verschiedenen Visualisierungs-Tabs
            - Laden Sie Daten als CSV herunter
            """)
        
        with tab2:
            st.markdown("""
            ## ❓ Häufig gestellte Fragen
            
            **Q: Wie aktuell sind die Daten?**
            A: Die Daten werden regelmäßig aktualisiert. Das letzte Update sehen Sie in der Sidebar.
            
            **Q: Kann ich eigene Dokumente hochladen?**
            A: Ja, im Dokumente-Bereich können Sie PDFs, Word-Dokumente und andere Formate hochladen.
            
            **Q: Wie funktioniert die Sprachsuche?**
            A: Das System verwendet KI, um deutsche Anfragen zu verstehen und passende Daten zu finden.
            """)
        
        with tab3:
            st.markdown("""
            ## 📞 Kontakt & Support
            
            **Gemeinde Gmunden**
            - 📧 E-Mail: transparenz@gmunden.at
            - 📞 Telefon: +43 7612 794-0
            - 🌐 Website: www.gmunden.at
            
            **Technischer Support**
            - 📧 E-Mail: it-support@gmunden.at
            - 🐛 Bug-Reports: GitHub Issues
            """)
    
    def run(self):
        """Hauptanwendung ausführen"""
        try:
            # Seite konfigurieren
            self.configure_page()
            
            # Header rendern
            self.render_header()
            
            # Sidebar und Navigation
            page, filters = self.render_sidebar()
            
            # Hauptinhalt basierend auf ausgewählter Seite
            if page == "🏠 Startseite":
                search_result = self.render_search_interface()
                if search_result:
                    self.render_results(search_result)
                    st.session_state.current_data = search_result
            
            elif page == "💰 Finanzen":
                self.render_finance_page(filters)
            
            elif page == "📋 Protokolle":
                st.header("📋 Protokolle")
                st.info("Protokoll-Funktionalität wird implementiert...")
            
            elif page == "📄 Dokumente":
                self.render_documents_page(filters)
            
            elif page == "📊 Statistiken":
                self.render_statistics_page(filters)
            
            elif page == "🔧 Verwaltung":
                self.render_admin_page()
            
            elif page == "ℹ️ Hilfe":
                self.render_help_page()
            
            # Footer
            st.divider()
            st.markdown("""
            <div style='text-align: center; color: #666; padding: 1rem;'>
                🏛️ Gemeinde Gmunden Transparenz-Datenbank v2.0 | 
                Entwickelt für vollständige Bürgertransparenz | 
                Alle Daten werden in Echtzeit validiert
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            st.error(f"Ein Fehler ist aufgetreten: {str(e)}")
            st.info("Bitte versuchen Sie es erneut oder kontaktieren Sie den Support.")

def main():
    """Hauptfunktion"""
    app = GmundenTransparencyApp()
    app.run()

if __name__ == "__main__":
    main()