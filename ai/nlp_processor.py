#!/usr/bin/env python3
"""
Deutsche NLP-Verarbeitung für das Gmunden Transparenz-System
Optimiert für realitätsbasierte Antworten ohne Halluzinationen
"""

import spacy
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import yaml
from pathlib import Path

class GermanNLPProcessor:
    """
    Deutsche NLP-Verarbeitung mit Fokus auf Realität und Genauigkeit
    """
    
    def __init__(self):
        self.load_config()
        self.init_nlp_model()
        self.setup_patterns()
    
    def load_config(self):
        """Lade NLP-Konfiguration"""
        try:
            config_path = Path(__file__).parent.parent / "config" / "system_settings.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.config = config.get('ai_config', {}).get('nlp', {})
        except Exception:
            self.config = {
                'language': 'de',
                'confidence_threshold': 0.8,
                'fact_checking': True
            }
    
    def init_nlp_model(self):
        """Initialisiere deutsches spaCy-Modell"""
        try:
            # Versuche großes deutsches Modell zu laden
            self.nlp = spacy.load("de_core_news_lg")
        except OSError:
            try:
                # Fallback auf mittleres Modell
                self.nlp = spacy.load("de_core_news_md")
            except OSError:
                try:
                    # Fallback auf kleines Modell
                    self.nlp = spacy.load("de_core_news_sm")
                except OSError:
                    # Fallback auf englisches Modell
                    self.nlp = spacy.load("en_core_web_sm")
                    print("Warnung: Deutsches spaCy-Modell nicht verfügbar, verwende englisches Modell")
    
    def setup_patterns(self):
        """Setup für deutsche Sprachmuster"""
        # Finanz-Keywords
        self.finance_keywords = {
            'ausgaben': ['ausgaben', 'kosten', 'aufwand', 'aufwendungen', 'bezahlt', 'gezahlt'],
            'einnahmen': ['einnahmen', 'erlöse', 'erträge', 'einkommen', 'verdienst'],
            'budget': ['budget', 'haushalt', 'etat', 'finanzplan'],
            'kategorien': {
                'infrastruktur': ['straße', 'straßen', 'brücke', 'brücken', 'kanal', 'kanäle', 'wasser', 'abwasser'],
                'personal': ['personal', 'gehalt', 'gehälter', 'lohn', 'löhne', 'mitarbeiter'],
                'verwaltung': ['verwaltung', 'büro', 'verwaltungskosten', 'bürokosten'],
                'kultur': ['kultur', 'veranstaltung', 'veranstaltungen', 'fest', 'feste'],
                'soziales': ['sozial', 'soziales', 'hilfe', 'unterstützung', 'förderung']
            }
        }
        
        # Zeit-Pattern
        self.time_patterns = {
            'jahr': r'\b(19|20)\d{2}\b',
            'jahr_wort': r'\b(letztes?\s+jahr|dieses?\s+jahr|voriges?\s+jahr)\b',
            'zeitraum': r'\b(zwischen|von)\s+(\d{4})\s+(und|bis)\s+(\d{4})\b'
        }
        
        # Betrag-Pattern
        self.amount_patterns = {
            'euro': r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*€?',
            'über': r'über\s+(\d+(?:\.\d{3})*(?:,\d{2})?)',
            'unter': r'unter\s+(\d+(?:\.\d{3})*(?:,\d{2})?)',
            'zwischen': r'zwischen\s+(\d+(?:\.\d{3})*(?:,\d{2})?)\s+und\s+(\d+(?:\.\d{3})*(?:,\d{2})?)'
        }
        
        # Intent-Pattern
        self.intent_patterns = {
            'search_financial': ['ausgaben', 'kosten', 'budget', 'geld', 'euro', 'finanz'],
            'search_documents': ['dokument', 'protokoll', 'bericht', 'datei', 'pdf'],
            'search_projects': ['projekt', 'bauvorhaben', 'maßnahme', 'vorhaben'],
            'search_statistics': ['statistik', 'entwicklung', 'trend', 'vergleich', 'analyse'],
            'search_general': ['zeige', 'finde', 'suche', 'liste', 'übersicht']
        }
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analysiere deutsche Suchanfrage und extrahiere strukturierte Informationen
        
        Args:
            query: Deutsche Suchanfrage
            
        Returns:
            Dict mit extrahierten Informationen
        """
        query_lower = query.lower()
        
        result = {
            'original_query': query,
            'intent': self.detect_intent(query_lower),
            'entities': self.extract_entities(query_lower),
            'filters': self.extract_filters(query_lower),
            'confidence': 0.0,
            'search_terms': self.extract_search_terms(query_lower),
            'query_type': 'general'
        }
        
        # Berechne Konfidenz-Score
        result['confidence'] = self.calculate_confidence(result)
        
        # Bestimme Query-Typ
        result['query_type'] = self.determine_query_type(result)
        
        return result
    
    def detect_intent(self, query: str) -> str:
        """Erkenne die Absicht der Anfrage"""
        for intent, keywords in self.intent_patterns.items():
            if any(keyword in query for keyword in keywords):
                return intent
        return 'search_general'
    
    def extract_entities(self, query: str) -> Dict[str, Any]:
        """Extrahiere Entitäten aus der Anfrage"""
        entities = {
            'years': [],
            'amounts': [],
            'categories': [],
            'locations': [],
            'organizations': []
        }
        
        # Jahre extrahieren
        year_matches = re.findall(self.time_patterns['jahr'], query)
        entities['years'] = [int(year) for year in year_matches]
        
        # Relative Zeitangaben
        if re.search(self.time_patterns['jahr_wort'], query):
            current_year = datetime.now().year
            if 'letztes jahr' in query or 'voriges jahr' in query:
                entities['years'].append(current_year - 1)
            elif 'dieses jahr' in query:
                entities['years'].append(current_year)
        
        # Zeiträume
        zeitraum_match = re.search(self.time_patterns['zeitraum'], query)
        if zeitraum_match:
            start_year = int(zeitraum_match.group(2))
            end_year = int(zeitraum_match.group(4))
            entities['years'] = list(range(start_year, end_year + 1))
        
        # Beträge extrahieren
        for pattern_name, pattern in self.amount_patterns.items():
            matches = re.findall(pattern, query)
            if matches:
                entities['amounts'].extend(matches)
        
        # Kategorien extrahieren
        for category, keywords in self.finance_keywords['kategorien'].items():
            if any(keyword in query for keyword in keywords):
                entities['categories'].append(category)
        
        # NLP-basierte Entitäten
        doc = self.nlp(query)
        for ent in doc.ents:
            if ent.label_ == "LOC":
                entities['locations'].append(ent.text)
            elif ent.label_ == "ORG":
                entities['organizations'].append(ent.text)
        
        return entities
    
    def extract_filters(self, query: str) -> Dict[str, Any]:
        """Extrahiere Filter-Kriterien"""
        filters = {}
        
        # Finanz-Filter
        if any(word in query for word in self.finance_keywords['ausgaben']):
            filters['type'] = 'ausgaben'
        elif any(word in query for word in self.finance_keywords['einnahmen']):
            filters['type'] = 'einnahmen'
        
        # Betrag-Filter
        if 'über' in query:
            match = re.search(self.amount_patterns['über'], query)
            if match:
                filters['amount_min'] = self.parse_amount(match.group(1))
        
        if 'unter' in query:
            match = re.search(self.amount_patterns['unter'], query)
            if match:
                filters['amount_max'] = self.parse_amount(match.group(1))
        
        # Sortierung
        if 'größte' in query or 'höchste' in query:
            filters['sort'] = 'desc'
        elif 'kleinste' in query or 'niedrigste' in query:
            filters['sort'] = 'asc'
        
        return filters
    
    def extract_search_terms(self, query: str) -> List[str]:
        """Extrahiere relevante Suchbegriffe"""
        doc = self.nlp(query)
        
        # Entferne Stoppwörter und extrahiere wichtige Begriffe
        search_terms = []
        for token in doc:
            if (not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2 and
                token.pos_ in ['NOUN', 'ADJ', 'VERB']):
                search_terms.append(token.lemma_.lower())
        
        return list(set(search_terms))  # Entferne Duplikate
    
    def parse_amount(self, amount_str: str) -> float:
        """Parse deutschen Betrag zu Float"""
        try:
            # Entferne Tausender-Punkte und ersetze Komma durch Punkt
            amount_str = amount_str.replace('.', '').replace(',', '.')
            return float(amount_str)
        except ValueError:
            return 0.0
    
    def calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Berechne Konfidenz-Score für die Analyse"""
        confidence = 0.5  # Basis-Konfidenz
        
        # Erhöhe Konfidenz basierend auf gefundenen Entitäten
        if result['entities']['years']:
            confidence += 0.2
        if result['entities']['amounts']:
            confidence += 0.2
        if result['entities']['categories']:
            confidence += 0.2
        if result['search_terms']:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def determine_query_type(self, result: Dict[str, Any]) -> str:
        """Bestimme den Typ der Anfrage"""
        if result['entities']['amounts'] or result['intent'] == 'search_financial':
            return 'financial'
        elif result['intent'] == 'search_documents':
            return 'documents'
        elif result['intent'] == 'search_projects':
            return 'projects'
        elif result['intent'] == 'search_statistics':
            return 'statistics'
        else:
            return 'general'
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validiere Anfrage auf Realitätsbezug
        Verhindere Halluzinationen und unrealistische Anfragen
        """
        validation = {
            'is_valid': True,
            'warnings': [],
            'suggestions': []
        }
        
        # Prüfe auf unrealistische Jahre
        current_year = datetime.now().year
        year_matches = re.findall(self.time_patterns['jahr'], query)
        for year_str in year_matches:
            year = int(year_str)
            if year < 1990 or year > current_year + 1:
                validation['warnings'].append(f"Jahr {year} liegt außerhalb des erwarteten Bereichs")
                validation['suggestions'].append(f"Verfügbare Jahre: 1990-{current_year}")
        
        # Prüfe auf unrealistische Beträge
        amount_matches = re.findall(r'(\d+(?:\.\d{3})*(?:,\d{2})?)', query)
        for amount_str in amount_matches:
            amount = self.parse_amount(amount_str)
            if amount > 1000000000:  # 1 Milliarde
                validation['warnings'].append(f"Betrag {amount_str} ist unrealistisch hoch für eine Gemeinde")
        
        return validation
    
    def generate_search_suggestions(self, query: str) -> List[str]:
        """Generiere Suchvorschläge basierend auf der Anfrage"""
        suggestions = []
        
        entities = self.extract_entities(query.lower())
        
        # Jahr-basierte Vorschläge
        if entities['years']:
            year = entities['years'][0]
            suggestions.extend([
                f"Alle Ausgaben von {year}",
                f"Größte Projekte {year}",
                f"Protokolle aus {year}"
            ])
        
        # Kategorie-basierte Vorschläge
        if entities['categories']:
            category = entities['categories'][0]
            suggestions.extend([
                f"Entwicklung {category} über die Jahre",
                f"Vergleich {category} mit anderen Kategorien"
            ])
        
        return suggestions[:5]  # Limitiere auf 5 Vorschläge