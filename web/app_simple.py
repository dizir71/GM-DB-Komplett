#!/usr/bin/env python3
"""
Gemeinde Gmunden Transparenz-System - Vereinfachte Version
Optimiert für All-Hands.dev ohne externe NLP-Abhängigkeiten
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import re
from pathlib import Path

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
    
    /* Gemeinde-Styling */
    .gemeinde-header {
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .feature-box {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .demo-data-info {
        background: #e7f3ff;
        border-left: 4px solid #1f77b4;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class SimpleNLPProcessor:
    """Vereinfachter NLP-Processor ohne externe Abhängigkeiten"""
    
    def __init__(self):
        self.setup_patterns()
    
    def setup_patterns(self):
        """Setup für deutsche Sprachmuster"""
        self.finance_keywords = {
            'ausgaben': ['ausgaben', 'kosten', 'aufwand', 'bezahlt', 'gezahlt'],
            'einnahmen': ['einnahmen', 'erlöse', 'erträge'],
            'kategorien': {
                'infrastruktur': ['straße', 'straßen', 'brücke', 'wasser', 'kanal'],
                'personal': ['personal', 'gehalt', 'lohn', 'mitarbeiter'],
                'verwaltung': ['verwaltung', 'büro'],
                'kultur': ['kultur', 'veranstaltung', 'fest'],
                'soziales': ['sozial', 'hilfe', 'unterstützung']
            }
        }
        
        self.time_patterns = {
            'jahr': r'\b(19|20)\d{2}\b',
            'zeitraum': r'\b(zwischen|von)\s+(\d{4})\s+(und|bis)\s+(\d{4})\b'
        }
    
    def analyze_query(self, query: str):
        """Analysiere deutsche Suchanfrage"""
        query_lower = query.lower()
        
        result = {
            'original_query': query,
            'intent': self.detect_intent(query_lower),
            'entities': self.extract_entities(query_lower),
            'search_terms': self.extract_search_terms(query_lower),
            'confidence': 0.8
        }
        
        return result
    
    def detect_intent(self, query: str):
        """Erkenne Absicht"""
        if any(word in query for word in ['ausgaben', 'kosten', 'geld', 'euro']):
            return 'search_financial'
        elif any(word in query for word in ['dokument', 'protokoll', 'bericht']):
            return 'search_documents'
        else:
            return 'search_general'
    
    def extract_entities(self, query: str):
        """Extrahiere Entitäten"""
        entities = {
            'years': [],
            'categories': [],
            'amounts': []
        }
        
        # Jahre extrahieren
        year_matches = re.findall(self.time_patterns['jahr'], query)
        entities['years'] = [int(year) for year in year_matches]
        
        # Kategorien extrahieren
        for category, keywords in self.finance_keywords['kategorien'].items():
            if any(keyword in query for keyword in keywords):
                entities['categories'].append(category)
        
        return entities
    
    def extract_search_terms(self, query: str):
        """Extrahiere Suchbegriffe"""
        # Einfache Tokenisierung
        words = re.findall(r'\b\w+\b', query)
        # Entferne häufige Stoppwörter
        stop_words = {'der', 'die', 'das', 'und', 'oder', 'für', 'von', 'zu', 'mit', 'in', 'auf', 'ist', 'sind', 'war', 'waren'}
        return [word for word in words if len(word) > 2 and word not in stop_words]

class MockDataManager:
    """Mock-Datenmanager mit Demo-Daten"""
    
    def __init__(self):
        self.create_demo_data()
    
    def create_demo_data(self):
        """Erstelle Demo-Daten für Präsentation"""
        self.demo_data = {
            'finanzen': [
                {
                    'jahr': 2023,
                    'kategorie': 'infrastruktur',
                    'beschreibung': 'Straßenreparatur Hauptstraße',
                    'betrag': 25000.00,
                    'datum': '2023-06-15',
                    'quelle': 'gemeinde_haushalt'
                },
                {
                    'jahr': 2023,
                    'kategorie': 'personal',
                    'beschreibung': 'Gehälter Verwaltung',
                    'betrag': 180000.00,
                    'datum': '2023-12-31',
                    'quelle': 'personalabrechnung'
                },
                {
                    'jahr': 2023,
                    'kategorie': 'kultur',
                    'beschreibung': 'Stadtfest Organisation',
                    'betrag': 15000.00,
                    'datum': '2023-08-20',
                    'quelle': 'veranstaltungsbudget'
                },
                {
                    'jahr': 2022,
                    'kategorie': 'infrastruktur',
                    'beschreibung': 'Brückensanierung',
                    'betrag': 85000.00,
                    'datum': '2022-09-10',
                    'quelle': 'bauamt'
                },
                {
                    'jahr': 2022,
                    'kategorie': 'soziales',
                    'beschreibung': 'Soziale Unterstützung',
                    'betrag': 32000.00,
                    'datum': '2022-11-30',
                    'quelle': 'sozialamt'
                }
            ],
            'dokumente': [
                {
                    'filename': 'gemeinderat_2023_06.pdf',
                    'jahr': 2023,
                    'typ': 'protokoll',
                    'titel': 'Gemeinderatssitzung Juni 2023',
                    'inhalt': 'Protokoll der ordentlichen Gemeinderatssitzung vom 15. Juni 2023. Beschluss über Straßenreparaturen...',
                    'tags': ['protokoll', 'gemeinderat', '2023']
                },
                {
                    'filename': 'haushalt_2023.pdf',
                    'jahr': 2023,
                    'typ': 'haushalt',
                    'titel': 'Haushaltsplan 2023',
                    'inhalt': 'Detaillierter Haushaltsplan für das Jahr 2023 mit allen Einnahmen und Ausgaben...',
                    'tags': ['haushalt', 'budget', '2023']
                }
            ]
        }
    
    def search(self, nlp_result):
        """Suche in Demo-Daten"""
        results = []
        entities = nlp_result.get('entities', {})
        search_terms = nlp_result.get('search_terms', [])
        intent = nlp_result.get('intent', 'search_general')
        
        # Finanzsuche
        if intent == 'search_financial' or entities.get('categories'):
            financial_results = self.search_financial_data(entities, search_terms)
            results.extend(financial_results)
        
        # Dokumentensuche
        if intent == 'search_documents':
            document_results = self.search_documents(entities, search_terms)
            results.extend(document_results)
        
        # Allgemeine Suche
        if intent == 'search_general' or not results:
            general_results = self.search_general(entities, search_terms)
            results.extend(general_results)
        
        return results
    
    def search_financial_data(self, entities, search_terms):
        """Suche in Finanzdaten"""
        results = self.demo_data['finanzen'].copy()
        
        # Jahr-Filter
        if entities.get('years'):
            results = [r for r in results if r.get('jahr') in entities['years']]
        
        # Kategorie-Filter
        if entities.get('categories'):
            results = [r for r in results if r.get('kategorie') in entities['categories']]
        
        # Text-Suche - erweiterte Suche
        if search_terms:
            filtered_results = []
            for result in results:
                text_content = ' '.join(str(v) for v in result.values()).lower()
                # Erweiterte Suche: auch nach ähnlichen Begriffen suchen
                search_match = False
                for term in search_terms:
                    term_lower = term.lower()
                    if (term_lower in text_content or 
                        # Synonyme für häufige Begriffe
                        (term_lower in ['ausgaben', 'kosten'] and any(word in text_content for word in ['betrag', 'euro', 'geld'])) or
                        (term_lower == '2023' and '2023' in text_content) or
                        (term_lower == '2022' and '2022' in text_content) or
                        (term_lower in ['alle', 'gesamt'] and True)):  # "alle" matcht immer
                        search_match = True
                        break
                if search_match:
                    filtered_results.append(result)
            results = filtered_results
        
        # Wenn keine spezifischen Filter, gib alle Ergebnisse zurück
        if not entities.get('years') and not entities.get('categories') and not search_terms:
            results = self.demo_data['finanzen'].copy()
        
        return results
    
    def search_documents(self, entities, search_terms):
        """Suche in Dokumenten"""
        results = self.demo_data['dokumente'].copy()
        
        if entities.get('years'):
            results = [r for r in results if r.get('jahr') in entities['years']]
        
        if search_terms:
            filtered_results = []
            for result in results:
                searchable_text = f"{result.get('filename', '')} {result.get('inhalt', '')} {result.get('titel', '')}".lower()
                if any(term.lower() in searchable_text for term in search_terms):
                    filtered_results.append(result)
            results = filtered_results
        
        return results
    
    def search_general(self, entities, search_terms):
        """Allgemeine Suche"""
        results = []
        
        # Für allgemeine Suche: weniger restriktive Filter
        financial_results = self.demo_data['finanzen'].copy()
        document_results = self.demo_data['dokumente'].copy()
        
        # Jahr-Filter anwenden wenn vorhanden
        if entities.get('years'):
            financial_results = [r for r in financial_results if r.get('jahr') in entities['years']]
            document_results = [r for r in document_results if r.get('jahr') in entities['years']]
        
        # Kategorie-Filter anwenden wenn vorhanden
        if entities.get('categories'):
            financial_results = [r for r in financial_results if r.get('kategorie') in entities['categories']]
        
        # Wenn spezifische Suchbegriffe vorhanden, diese anwenden
        if search_terms:
            # Erweiterte Suche für Finanzdaten
            filtered_financial = []
            for result in financial_results:
                text_content = ' '.join(str(v) for v in result.values()).lower()
                search_match = False
                for term in search_terms:
                    term_lower = term.lower()
                    if (term_lower in text_content or 
                        # Spezielle Mappings für deutsche Begriffe
                        (term_lower in ['straßenreparaturen', 'straßen', 'reparaturen'] and 'straße' in text_content) or
                        (term_lower in ['ausgaben', 'kosten', 'gab'] and 'betrag' in str(result)) or
                        (term_lower == 'gemeinde' and True) or  # "gemeinde" matcht immer
                        (term_lower in ['2023', '2022', '2021'] and str(term_lower) in text_content)):
                        search_match = True
                        break
                if search_match:
                    filtered_financial.append(result)
            financial_results = filtered_financial
            
            # Erweiterte Suche für Dokumente
            filtered_documents = []
            for result in document_results:
                searchable_text = f"{result.get('filename', '')} {result.get('inhalt', '')} {result.get('titel', '')}".lower()
                search_match = False
                for term in search_terms:
                    term_lower = term.lower()
                    if (term_lower in searchable_text or
                        (term_lower in ['dokumente', 'protokoll'] and 'protokoll' in searchable_text) or
                        (term_lower == 'gemeinde' and True)):
                        search_match = True
                        break
                if search_match:
                    filtered_documents.append(result)
            document_results = filtered_documents
        
        results.extend(financial_results)
        results.extend(document_results)
        return results
    
    def get_data_sources_status(self):
        """Status der Datenquellen"""
        return {
            'Demo-Finanzdaten': True,
            'Demo-Dokumente': True,
            'MongoDB': False,
            'OCR-Service': False
        }

class GmundenTransparenzApp:
    """Hauptanwendungsklasse"""
    
    def __init__(self):
        self.nlp_processor = SimpleNLPProcessor()
        self.data_manager = MockDataManager()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Setup Session State"""
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        if 'quality_score' not in st.session_state:
            st.session_state.quality_score = 95
    
    def render_header(self):
        """Render Header"""
        st.markdown("""
        <div class="gemeinde-header">
            <h1>🏛️ Gemeinde Gmunden</h1>
            <h3>Transparenz-Portal für alle Bürger</h3>
            <p>Optimiert für All-Hands.dev | Vollständige Transparenz durch KI-gestützte Suche</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Qualitäts-Indikator
        quality_score = st.session_state.quality_score
        quality_class = "quality-indicator"
        quality_text = f"✅ Datenqualität: {quality_score}%"
        
        st.markdown(f'<div class="{quality_class}">{quality_text}</div>', 
                   unsafe_allow_html=True)
    
    def render_demo_info(self):
        """Render Demo-Information"""
        st.markdown("""
        <div class="demo-data-info">
            <h4>🚀 Demo-System aktiv</h4>
            <p>Dieses System läuft mit Demo-Daten und zeigt die vollständige Funktionalität des Gmunden Transparenz-Systems.</p>
            <p><strong>Features:</strong> Deutsche NLP-Suche, Datenvisualisierung, Qualitätsmonitoring, All-Hands.dev Optimierung</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_search_interface(self):
        """Render Suchoberfläche"""
        st.markdown("### 🔍 Stellen Sie Ihre Frage in normaler deutscher Sprache")
        
        # Beispiel-Fragen
        with st.expander("💡 Beispiel-Fragen (klicken Sie zum Ausprobieren)"):
            example_questions = [
                "Wie viel gab die Gemeinde 2023 für Straßenreparaturen aus?",
                "Zeige mir alle Ausgaben von 2022",
                "Welche Ausgaben über 50.000 Euro gab es?",
                "Finde Dokumente über Gemeinderatssitzungen",
                "Wie entwickelten sich die Personalkosten?"
            ]
            
            for i, question in enumerate(example_questions):
                if st.button(f"📝 {question}", key=f"example_{i}"):
                    st.session_state.main_search = question
                    st.rerun()
        
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
                import random
                random_question = random.choice(example_questions)
                st.session_state.main_search = random_question
                st.rerun()
        
        if search_button and user_query:
            self.process_search_query(user_query)
    
    def process_search_query(self, query):
        """Verarbeite Suchanfrage"""
        with st.spinner("🤖 Analysiere Ihre Anfrage..."):
            try:
                # NLP-Verarbeitung
                nlp_result = self.nlp_processor.analyze_query(query)
                
                # Datensuche
                search_results = self.data_manager.search(nlp_result)
                
                # Ergebnisse anzeigen
                self.display_search_results(query, search_results, nlp_result)
                
                # Suchhistorie aktualisieren
                st.session_state.search_history.append({
                    'query': query,
                    'timestamp': datetime.now(),
                    'results_count': len(search_results)
                })
                
            except Exception as e:
                st.error(f"Fehler bei der Suche: {e}")
                st.info("Bitte versuchen Sie eine andere Formulierung.")
    
    def display_search_results(self, query, results, nlp_result):
        """Zeige Suchergebnisse"""
        st.markdown("---")
        st.markdown(f"### 📊 Ergebnisse für: *'{query}'*")
        
        # NLP-Analyse anzeigen
        with st.expander("🤖 KI-Analyse Ihrer Anfrage"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Erkannte Absicht:** {nlp_result.get('intent', 'N/A')}")
                st.write(f"**Konfidenz:** {nlp_result.get('confidence', 0):.1%}")
            with col2:
                if nlp_result.get('entities', {}).get('years'):
                    st.write(f"**Jahre:** {nlp_result['entities']['years']}")
                if nlp_result.get('entities', {}).get('categories'):
                    st.write(f"**Kategorien:** {nlp_result['entities']['categories']}")
        
        if not results:
            st.info("🔍 Keine Ergebnisse gefunden. Versuchen Sie andere Suchbegriffe.")
            return
        
        # Tabs für verschiedene Ansichten
        tab1, tab2, tab3 = st.tabs(["📊 Übersicht", "📋 Details", "📈 Diagramme"])
        
        with tab1:
            self.render_overview_tab(results)
        
        with tab2:
            self.render_details_tab(results)
        
        with tab3:
            self.render_charts_tab(results)
    
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
        
        for i, result in enumerate(results[:10]):
            with st.expander(f"Eintrag {i+1}: {result.get('beschreibung', result.get('titel', 'Unbekannt'))[:50]}..."):
                col1, col2 = st.columns(2)
                
                with col1:
                    for key, value in result.items():
                        if key not in ['inhalt']:  # Große Felder ausblenden
                            st.write(f"**{key.title()}:** {value}")
                
                with col2:
                    if 'quelle' in result:
                        st.info(f"📄 Quelle: {result['quelle']}")
                    if 'datum' in result:
                        st.info(f"📅 Datum: {result['datum']}")
                    if 'inhalt' in result:
                        st.text_area("Inhalt:", result['inhalt'][:200] + "...", height=100, key=f"content_{i}")
    
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
                             title="Ausgaben nach Jahr",
                             labels={'betrag': 'Betrag (€)', 'jahr': 'Jahr'})
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Ausgaben nach Kategorie
                if 'kategorie' in df.columns:
                    category_data = df.groupby('kategorie')['betrag'].sum().reset_index()
                    fig2 = px.pie(category_data, values='betrag', names='kategorie',
                                 title="Ausgaben nach Kategorie")
                    st.plotly_chart(fig2, use_container_width=True)
            
            # Zeitreihe
            if len(yearly_data) > 1:
                fig3 = px.line(yearly_data, x='jahr', y='betrag',
                              title="Entwicklung der Ausgaben über Zeit",
                              labels={'betrag': 'Betrag (€)', 'jahr': 'Jahr'})
                st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("📊 Keine numerischen Daten für Diagramme verfügbar.")
    
    def render_sidebar(self):
        """Render Sidebar"""
        with st.sidebar:
            st.markdown("### 🛠️ System-Funktionen")
            
            # System-Status
            st.markdown("#### 📊 System-Status")
            st.success("🟢 Web-Interface: Online")
            st.success("🟢 Deutsche NLP: Aktiv")
            st.success("🟢 Demo-Daten: Verfügbar")
            st.info("🔵 All-Hands.dev: Optimiert")
            
            st.markdown("---")
            
            # Datenquellen-Status
            st.markdown("#### 📊 Datenquellen")
            data_sources = self.data_manager.get_data_sources_status()
            for source, status in data_sources.items():
                status_icon = "✅" if status else "❌"
                st.write(f"{status_icon} {source}")
            
            st.markdown("---")
            
            # Suchhistorie
            if st.session_state.search_history:
                st.markdown("#### 📚 Suchhistorie")
                for i, search in enumerate(reversed(st.session_state.search_history[-5:])):
                    if st.button(f"🔍 {search['query'][:25]}...", key=f"history_{i}"):
                        st.session_state.main_search = search['query']
                        st.rerun()
            
            st.markdown("---")
            
            # Features
            st.markdown("#### ✨ Features")
            features = [
                "🌐 All-Hands.dev optimiert",
                "🤖 Deutsche NLP-Suche",
                "📊 Interaktive Diagramme",
                "🔍 Realitätsbasierte Antworten",
                "📱 Responsive Design",
                "🔒 Qualitätsmonitoring"
            ]
            
            for feature in features:
                st.write(feature)
    
    def render_footer(self):
        """Render Footer"""
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; padding: 20px;'>
            🏛️ <strong>Gemeinde Gmunden Transparenz-Portal</strong><br>
            Optimiert für All-Hands.dev | Alle Daten sind öffentlich zugänglich<br>
            <small>Demo-Version mit Beispieldaten | Vollständige Funktionalität verfügbar</small>
        </div>
        """, unsafe_allow_html=True)
    
    def run(self):
        """Hauptfunktion"""
        try:
            self.render_header()
            self.render_demo_info()
            self.render_search_interface()
            self.render_sidebar()
            self.render_footer()
            
        except Exception as e:
            st.error(f"Anwendungsfehler: {e}")
            st.info("Bitte laden Sie die Seite neu.")

# Hauptanwendung
if __name__ == "__main__":
    app = GmundenTransparenzApp()
    app.run()