#!/usr/bin/env python3
"""
Gemeinde Gmunden Transparenz-System
Optimiert für All-Hands.dev

Hauptanwendung für das Bürger-Web-Interface mit deutscher NLP-Suche
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yaml
import json
import os
import sys
from pathlib import Path

# Pfad-Konfiguration
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import der eigenen Module
from ai.nlp_processor import GermanNLPProcessor
from ai.fact_checker import FactChecker
from data.data_manager import DataManager
from monitoring.quality_monitor import QualityMonitor

# All-Hands.dev optimierte Streamlit-Konfiguration
st.set_page_config(
    page_title="Gemeinde Gmunden - Transparenz-Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/gmunden/transparenz-system',
        'Report a bug': 'https://github.com/gmunden/transparenz-system/issues',
        'About': "Gemeinde Gmunden Transparenz-System - Vollständige Transparenz für alle Bürger"
    }
)

# CSS für All-Hands.dev Optimierung
st.markdown("""
<style>
    /* All-Hands.dev optimierte Styles */
    .main > div {
        padding-top: 2rem;
    }
    
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp {
        margin: 0;
        padding: 0;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    
    /* Qualitäts-Indikator */
    .quality-indicator {
        position: fixed;
        top: 10px;
        right: 10px;
        background: #28a745;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
        z-index: 1000;
    }
    
    .quality-indicator.warning {
        background: #ffc107;
        color: #000;
    }
    
    .quality-indicator.error {
        background: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

class GmundenTransparenzApp:
    """Hauptanwendungsklasse für das Transparenz-System"""
    
    def __init__(self):
        self.load_config()
        self.init_components()
        self.setup_session_state()
    
    def load_config(self):
        """Lade Konfigurationsdateien"""
        try:
            config_path = PROJECT_ROOT / "config" / "system_settings.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            st.error(f"Konfiguration konnte nicht geladen werden: {e}")
            self.config = {}
    
    def init_components(self):
        """Initialisiere alle System-Komponenten"""
        try:
            self.nlp_processor = GermanNLPProcessor()
            self.fact_checker = FactChecker()
            self.data_manager = DataManager()
            self.quality_monitor = QualityMonitor()
        except Exception as e:
            st.error(f"Komponenten konnten nicht initialisiert werden: {e}")
    
    def setup_session_state(self):
        """Setup Session State für Streamlit"""
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        if 'quality_score' not in st.session_state:
            st.session_state.quality_score = 100
        if 'last_search' not in st.session_state:
            st.session_state.last_search = None
    
    def render_header(self):
        """Render Header mit Qualitäts-Indikator"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.image("https://via.placeholder.com/100x60/1f77b4/ffffff?text=GMUNDEN", width=100)
        
        with col2:
            st.title("🏛️ Gemeinde Gmunden")
            st.subheader("Transparenz-Portal für alle Bürger")
        
        with col3:
            quality_score = st.session_state.quality_score
            if quality_score >= 90:
                quality_class = "quality-indicator"
                quality_text = "✅ Hohe Datenqualität"
            elif quality_score >= 70:
                quality_class = "quality-indicator warning"
                quality_text = "⚠️ Mittlere Datenqualität"
            else:
                quality_class = "quality-indicator error"
                quality_text = "❌ Niedrige Datenqualität"
            
            st.markdown(f'<div class="{quality_class}">{quality_text}</div>', 
                       unsafe_allow_html=True)
    
    def render_search_interface(self):
        """Render die Haupt-Suchoberfläche"""
        st.markdown("---")
        st.markdown("### 🔍 Stellen Sie Ihre Frage in normaler deutscher Sprache")
        
        # Beispiel-Fragen
        with st.expander("💡 Beispiel-Fragen"):
            st.markdown("""
            - *"Wie viel gab die Gemeinde 2023 für Straßenreparaturen aus?"*
            - *"Zeige mir alle Gemeinderatsprotokolle von 2022"*
            - *"Welche Ausgaben über 10.000 Euro gab es im letzten Jahr?"*
            - *"Finde Dokumente über Wasserleitungsprojekte"*
            - *"Wie entwickelten sich die Personalkosten zwischen 2020 und 2023?"*
            """)
        
        # Haupt-Suchfeld
        user_query = st.text_input(
            "Ihre Frage:",
            placeholder="z.B. 'Zeige mir die Ausgaben für Infrastruktur in 2023'",
            key="main_search"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            search_button = st.button("🔍 Suchen", type="primary")
        
        with col2:
            if st.button("🎲 Zufällige Frage"):
                user_query = self.get_random_question()
                st.rerun()
        
        if search_button and user_query:
            self.process_search_query(user_query)
    
    def get_random_question(self):
        """Generiere eine zufällige Beispiel-Frage"""
        questions = [
            "Zeige mir die Ausgaben von 2023",
            "Welche Projekte wurden 2022 durchgeführt?",
            "Wie hoch waren die Personalkosten im letzten Jahr?",
            "Finde alle Protokolle über Straßenbau",
            "Zeige mir die größten Ausgaben der letzten 5 Jahre"
        ]
        import random
        return random.choice(questions)
    
    def process_search_query(self, query):
        """Verarbeite Suchanfrage mit NLP und Qualitätskontrolle"""
        with st.spinner("🤖 Analysiere Ihre Anfrage..."):
            try:
                # NLP-Verarbeitung
                nlp_result = self.nlp_processor.analyze_query(query)
                
                # Datensuche
                search_results = self.data_manager.search(nlp_result)
                
                # Qualitätsprüfung
                quality_check = self.fact_checker.verify_results(search_results)
                
                # Ergebnisse anzeigen
                self.display_search_results(query, search_results, quality_check)
                
                # Suchhistorie aktualisieren
                st.session_state.search_history.append({
                    'query': query,
                    'timestamp': datetime.now(),
                    'results_count': len(search_results),
                    'quality_score': quality_check.get('score', 0)
                })
                
            except Exception as e:
                st.error(f"Fehler bei der Suche: {e}")
                st.info("Bitte versuchen Sie eine andere Formulierung.")
    
    def display_search_results(self, query, results, quality_check):
        """Zeige Suchergebnisse mit Visualisierungen"""
        st.markdown("---")
        st.markdown(f"### 📊 Ergebnisse für: *'{query}'*")
        
        # Qualitäts-Warnung
        if quality_check.get('score', 100) < 80:
            st.warning(f"⚠️ Datenqualität: {quality_check.get('score', 0)}% - "
                      f"Einige Ergebnisse könnten unvollständig sein.")
        
        if not results:
            st.info("🔍 Keine Ergebnisse gefunden. Versuchen Sie andere Suchbegriffe.")
            return
        
        # Tabs für verschiedene Ansichten
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Übersicht", "📋 Details", "📈 Diagramme", "📄 Dokumente"])
        
        with tab1:
            self.render_overview_tab(results)
        
        with tab2:
            self.render_details_tab(results)
        
        with tab3:
            self.render_charts_tab(results)
        
        with tab4:
            self.render_documents_tab(results)
    
    def render_overview_tab(self, results):
        """Render Übersichts-Tab"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Gefundene Einträge", len(results))
        
        with col2:
            total_amount = sum(r.get('betrag', 0) for r in results if 'betrag' in r)
            st.metric("Gesamtsumme", f"€ {total_amount:,.2f}")
        
        with col3:
            years = set(r.get('jahr') for r in results if 'jahr' in r)
            st.metric("Betroffene Jahre", len(years))
        
        with col4:
            categories = set(r.get('kategorie') for r in results if 'kategorie' in r)
            st.metric("Kategorien", len(categories))
        
        # Top-Ergebnisse
        if results:
            st.markdown("#### 🔝 Top-Ergebnisse")
            df = pd.DataFrame(results[:10])
            st.dataframe(df, use_container_width=True)
    
    def render_details_tab(self, results):
        """Render Details-Tab"""
        st.markdown("#### 📋 Detaillierte Ergebnisse")
        
        for i, result in enumerate(results[:20]):  # Limitiere auf 20 Ergebnisse
            with st.expander(f"Eintrag {i+1}: {result.get('beschreibung', 'Unbekannt')[:50]}..."):
                col1, col2 = st.columns(2)
                
                with col1:
                    for key, value in result.items():
                        if key not in ['_id', 'ocr_text']:  # Große Felder ausblenden
                            st.write(f"**{key.title()}:** {value}")
                
                with col2:
                    if 'quelle' in result:
                        st.info(f"📄 Quelle: {result['quelle']}")
                    if 'datum' in result:
                        st.info(f"📅 Datum: {result['datum']}")
    
    def render_charts_tab(self, results):
        """Render Diagramme-Tab"""
        st.markdown("#### 📈 Visualisierungen")
        
        # Nur wenn numerische Daten vorhanden
        numeric_results = [r for r in results if 'betrag' in r and 'jahr' in r]
        
        if numeric_results:
            df = pd.DataFrame(numeric_results)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Ausgaben nach Jahr
                yearly_data = df.groupby('jahr')['betrag'].sum().reset_index()
                fig1 = px.bar(yearly_data, x='jahr', y='betrag', 
                             title="Ausgaben nach Jahr")
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Ausgaben nach Kategorie
                if 'kategorie' in df.columns:
                    category_data = df.groupby('kategorie')['betrag'].sum().reset_index()
                    fig2 = px.pie(category_data, values='betrag', names='kategorie',
                                 title="Ausgaben nach Kategorie")
                    st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("📊 Keine numerischen Daten für Diagramme verfügbar.")
    
    def render_documents_tab(self, results):
        """Render Dokumente-Tab"""
        st.markdown("#### 📄 Gefundene Dokumente")
        
        doc_results = [r for r in results if 'filename' in r or 'dokument' in r]
        
        if doc_results:
            for doc in doc_results[:10]:
                with st.expander(f"📄 {doc.get('filename', 'Unbekanntes Dokument')}"):
                    if 'pdf_title' in doc:
                        st.write(f"**Titel:** {doc['pdf_title']}")
                    if 'typ' in doc:
                        st.write(f"**Typ:** {doc['typ']}")
                    if 'ocr_text' in doc:
                        st.write("**Inhalt (Auszug):**")
                        st.text(doc['ocr_text'][:500] + "..." if len(doc['ocr_text']) > 500 else doc['ocr_text'])
        else:
            st.info("📄 Keine Dokumente in den Ergebnissen gefunden.")
    
    def render_sidebar(self):
        """Render Sidebar mit zusätzlichen Funktionen"""
        with st.sidebar:
            st.markdown("### 🛠️ Erweiterte Funktionen")
            
            # Suchhistorie
            if st.session_state.search_history:
                st.markdown("#### 📚 Suchhistorie")
                for i, search in enumerate(reversed(st.session_state.search_history[-5:])):
                    if st.button(f"🔍 {search['query'][:30]}...", key=f"history_{i}"):
                        st.session_state.main_search = search['query']
                        st.rerun()
            
            st.markdown("---")
            
            # Datenquellen-Status
            st.markdown("#### 📊 Datenquellen")
            data_sources = self.data_manager.get_data_sources_status()
            for source, status in data_sources.items():
                status_icon = "✅" if status else "❌"
                st.write(f"{status_icon} {source}")
            
            st.markdown("---")
            
            # System-Info
            st.markdown("#### ℹ️ System-Information")
            st.write(f"**Version:** 2.0.0")
            st.write(f"**Letzte Aktualisierung:** {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            st.write(f"**Datenqualität:** {st.session_state.quality_score}%")
    
    def run(self):
        """Hauptfunktion der Anwendung"""
        try:
            self.render_header()
            self.render_search_interface()
            self.render_sidebar()
            
            # Footer
            st.markdown("---")
            st.markdown("""
            <div style='text-align: center; color: #666; padding: 20px;'>
                🏛️ Gemeinde Gmunden Transparenz-Portal<br>
                Optimiert für All-Hands.dev | Alle Daten sind öffentlich zugänglich
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Anwendungsfehler: {e}")
            st.info("Bitte laden Sie die Seite neu.")

# Hauptanwendung
if __name__ == "__main__":
    app = GmundenTransparenzApp()
    app.run()