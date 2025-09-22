#!/usr/bin/env python3
"""
Gmunden Transparenz-Datenbank - NLP-Processor
Verarbeitet deutsche Suchanfragen in natürlicher Sprache
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
from dataclasses import dataclass
from pathlib import Path

# Optionale spaCy-Integration
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

logger = logging.getLogger(__name__)

@dataclass
class QueryEntity:
    """Entität aus Suchanfrage"""
    type: str
    value: Any
    confidence: float
    text: str

class NLPProcessor:
    """Deutsche NLP-Verarbeitung für Suchanfragen"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.nlp_model = None
        
        # Sprachmodell laden (falls verfügbar)
        if HAS_SPACY:
            try:
                self.nlp_model = spacy.load("de_core_news_sm")
                logger.info("German spaCy model loaded successfully")
            except OSError:
                logger.warning("German spaCy model not found, using fallback methods")
        
        # Deutsche Wörterbücher und Patterns
        self._load_german_patterns()
    
    def _load_german_patterns(self):
        """Deutsche Sprachmuster und Wörterbücher laden"""
        
        # Finanz-Keywords
        self.finance_keywords = {
            'ausgaben': ['ausgaben', 'ausgabe', 'kosten', 'aufwand', 'aufwendungen', 'bezahlt', 'gezahlt'],
            'einnahmen': ['einnahmen', 'einnahme', 'erlös', 'erlöse', 'einkommen', 'erhalten'],
            'budget': ['budget', 'haushalt', 'etat', 'finanzplan'],
            'betrag': ['betrag', 'summe', 'höhe', 'wert', 'euro', '€']
        }
        
        # Kategorie-Keywords
        self.category_keywords = {
            'infrastruktur': ['straße', 'straßen', 'weg', 'wege', 'brücke', 'brücken', 'kanal', 'kanäle', 
                             'wasserleitung', 'wasserleitungen', 'abwasser', 'infrastruktur', 'bau', 'bauten'],
            'personal': ['personal', 'gehalt', 'gehälter', 'lohn', 'löhne', 'mitarbeiter', 'angestellte', 
                        'beamte', 'personalkosten'],
            'kultur': ['kultur', 'fest', 'feste', 'veranstaltung', 'veranstaltungen', 'museum', 'theater', 
                      'konzert', 'konzerte', 'stadtfest'],
            'umwelt': ['umwelt', 'grün', 'grünfläche', 'grünflächen', 'park', 'parks', 'baum', 'bäume', 
                      'umweltschutz', 'natur'],
            'bildung': ['schule', 'schulen', 'bildung', 'kindergarten', 'kindergärten', 'unterricht'],
            'soziales': ['sozial', 'soziales', 'hilfe', 'unterstützung', 'betreuung', 'pflege'],
            'verwaltung': ['verwaltung', 'büro', 'amt', 'ämter', 'rathaus', 'gemeinde']
        }
        
        # Dokument-Keywords
        self.document_keywords = {
            'protokoll': ['protokoll', 'protokolle', 'sitzung', 'sitzungen', 'gemeinderat', 'beschluss', 'beschlüsse'],
            'vertrag': ['vertrag', 'verträge', 'vereinbarung', 'vereinbarungen', 'kontrakt'],
            'rechnung': ['rechnung', 'rechnungen', 'beleg', 'belege', 'quittung', 'quittungen'],
            'bericht': ['bericht', 'berichte', 'dokumentation', 'studie', 'studien', 'analyse']
        }
        
        # Zeit-Keywords
        self.time_keywords = {
            'jahr': ['jahr', 'jahre', 'jährlich'],
            'monat': ['monat', 'monate', 'monatlich'],
            'quartal': ['quartal', 'quartale', 'vierteljahr'],
            'aktuell': ['aktuell', 'aktueller', 'aktuelle', 'derzeit', 'momentan', 'jetzt'],
            'vergangen': ['letztes', 'letzter', 'letzte', 'vergangen', 'vergangenes', 'voriges', 'vorige'],
            'zwischen': ['zwischen', 'von', 'bis', 'ab', 'seit']
        }
        
        # Vergleichs-Keywords
        self.comparison_keywords = {
            'mehr': ['mehr', 'über', 'größer', 'höher', 'mindestens', 'ab'],
            'weniger': ['weniger', 'unter', 'kleiner', 'niedriger', 'höchstens', 'bis'],
            'gleich': ['gleich', 'genau', 'exakt'],
            'zwischen': ['zwischen', 'von', 'bis']
        }
        
        # Frage-Keywords
        self.question_keywords = {
            'was': ['was', 'welche', 'welcher', 'welches'],
            'wie': ['wie', 'wieviel', 'wie viel', 'wie viele'],
            'wann': ['wann', 'ab wann', 'bis wann'],
            'wo': ['wo', 'woher', 'wohin'],
            'warum': ['warum', 'weshalb', 'wieso'],
            'wer': ['wer', 'wen', 'wem']
        }
        
        # Regex-Patterns
        self.patterns = {
            'year': re.compile(r'\b(19|20)\d{2}\b'),
            'amount': re.compile(r'\b(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(?:euro|€|eur)\b', re.IGNORECASE),
            'amount_simple': re.compile(r'\b(\d+(?:\.\d{3})*(?:,\d{2})?)\b'),
            'date': re.compile(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b'),
            'month_year': re.compile(r'\b(\d{1,2})/(\d{4})\b'),
            'percentage': re.compile(r'\b(\d+(?:,\d+)?)\s*%\b')
        }
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Hauptfunktion zur Analyse einer deutschen Suchanfrage"""
        try:
            logger.info(f"Analyzing query: {query}")
            
            # Query normalisieren
            normalized_query = self._normalize_query(query)
            
            # Intent erkennen
            intent = self._detect_intent(normalized_query)
            
            # Entitäten extrahieren
            entities = self._extract_entities(normalized_query)
            
            # Keywords extrahieren
            keywords = self._extract_keywords(normalized_query)
            
            # Kontext analysieren
            context = self._analyze_context(normalized_query, entities)
            
            result = {
                'original_query': query,
                'normalized_query': normalized_query,
                'intent': intent,
                'entities': entities,
                'keywords': keywords,
                'context': context,
                'confidence': self._calculate_confidence(intent, entities, keywords),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"NLP analysis result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"NLP analysis error: {e}")
            return {
                'original_query': query,
                'intent': 'general_search',
                'entities': {},
                'keywords': [query],
                'confidence': 0.5,
                'error': str(e)
            }
    
    def _normalize_query(self, query: str) -> str:
        """Query normalisieren"""
        # Kleinschreibung
        normalized = query.lower().strip()
        
        # Sonderzeichen normalisieren
        replacements = {
            'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
            '€': 'euro', '&': 'und'
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Mehrfache Leerzeichen entfernen
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _detect_intent(self, query: str) -> str:
        """Intent (Absicht) der Anfrage erkennen"""
        
        # Finanz-Intent
        finance_indicators = 0
        for keyword_list in self.finance_keywords.values():
            if any(keyword in query for keyword in keyword_list):
                finance_indicators += 1
        
        # Dokument-Intent
        document_indicators = 0
        for keyword_list in self.document_keywords.values():
            if any(keyword in query for keyword in keyword_list):
                document_indicators += 1
        
        # Statistik-Intent
        stats_keywords = ['statistik', 'übersicht', 'zusammenfassung', 'entwicklung', 'trend', 'vergleich']
        stats_indicators = sum(1 for keyword in stats_keywords if keyword in query)
        
        # Intent bestimmen
        if finance_indicators >= 1:
            return 'financial_search'
        elif document_indicators >= 1:
            return 'document_search'
        elif stats_indicators >= 1:
            return 'statistics_search'
        elif any(keyword in query for keyword in ['protokoll', 'sitzung', 'beschluss']):
            return 'protocol_search'
        else:
            return 'general_search'
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Entitäten aus der Anfrage extrahieren"""
        entities = {}
        
        # Jahre extrahieren
        years = self._extract_years(query)
        if years:
            entities['year'] = years[0] if len(years) == 1 else years
        
        # Beträge extrahieren
        amounts = self._extract_amounts(query)
        if amounts:
            entities.update(amounts)
        
        # Kategorien extrahieren
        categories = self._extract_categories(query)
        if categories:
            entities['category'] = categories[0] if len(categories) == 1 else categories
        
        # Dokumenttypen extrahieren
        doc_types = self._extract_document_types(query)
        if doc_types:
            entities['document_type'] = doc_types[0] if len(doc_types) == 1 else doc_types
        
        # Zeiträume extrahieren
        time_range = self._extract_time_range(query)
        if time_range:
            entities.update(time_range)
        
        # Vergleichsoperatoren extrahieren
        comparisons = self._extract_comparisons(query)
        if comparisons:
            entities.update(comparisons)
        
        return entities
    
    def _extract_years(self, query: str) -> List[int]:
        """Jahre aus Query extrahieren"""
        years = []
        
        # Direkte Jahreszahlen
        year_matches = self.patterns['year'].findall(query)
        for match in year_matches:
            year = int(match)
            if 1990 <= year <= datetime.now().year + 1:
                years.append(year)
        
        # Relative Zeitangaben
        current_year = datetime.now().year
        
        if any(keyword in query for keyword in ['letztes jahr', 'voriges jahr', 'vergangenes jahr']):
            years.append(current_year - 1)
        elif any(keyword in query for keyword in ['dieses jahr', 'aktuelles jahr']):
            years.append(current_year)
        elif 'letzte' in query and 'jahre' in query:
            # "letzte 3 Jahre" etc.
            number_match = re.search(r'letzte[n]?\s+(\d+)\s+jahre', query)
            if number_match:
                num_years = int(number_match.group(1))
                years.extend(range(current_year - num_years + 1, current_year + 1))
        
        return sorted(list(set(years)), reverse=True)
    
    def _extract_amounts(self, query: str) -> Dict[str, float]:
        """Geldbeträge extrahieren"""
        amounts = {}
        
        # Direkte Beträge
        amount_matches = self.patterns['amount'].findall(query)
        if not amount_matches:
            amount_matches = self.patterns['amount_simple'].findall(query)
        
        for match in amount_matches:
            try:
                # Deutsche Zahlenformatierung berücksichtigen
                amount_str = match.replace('.', '').replace(',', '.')
                amount = float(amount_str)
                
                # Kontext analysieren für min/max
                match_pos = query.find(match)
                context_before = query[max(0, match_pos-20):match_pos].lower()
                context_after = query[match_pos:match_pos+20].lower()
                
                if any(keyword in context_before for keyword in ['über', 'mehr als', 'mindestens', 'ab']):
                    amounts['amount_min'] = amount
                elif any(keyword in context_before for keyword in ['unter', 'weniger als', 'höchstens', 'bis']):
                    amounts['amount_max'] = amount
                elif 'zwischen' in context_before:
                    if 'amount_min' not in amounts:
                        amounts['amount_min'] = amount
                    else:
                        amounts['amount_max'] = amount
                else:
                    amounts['amount'] = amount
                    
            except ValueError:
                continue
        
        return amounts
    
    def _extract_categories(self, query: str) -> List[str]:
        """Kategorien extrahieren"""
        found_categories = []
        
        for category, keywords in self.category_keywords.items():
            if any(keyword in query for keyword in keywords):
                found_categories.append(category)
        
        return found_categories
    
    def _extract_document_types(self, query: str) -> List[str]:
        """Dokumenttypen extrahieren"""
        found_types = []
        
        for doc_type, keywords in self.document_keywords.items():
            if any(keyword in query for keyword in keywords):
                found_types.append(doc_type)
        
        return found_types
    
    def _extract_time_range(self, query: str) -> Dict[str, Any]:
        """Zeiträume extrahieren"""
        time_range = {}
        
        # "zwischen X und Y"
        between_match = re.search(r'zwischen\s+(\d{4})\s+und\s+(\d{4})', query)
        if between_match:
            start_year = int(between_match.group(1))
            end_year = int(between_match.group(2))
            time_range['year_range'] = [start_year, end_year]
        
        # "von X bis Y"
        from_to_match = re.search(r'von\s+(\d{4})\s+bis\s+(\d{4})', query)
        if from_to_match:
            start_year = int(from_to_match.group(1))
            end_year = int(from_to_match.group(2))
            time_range['year_range'] = [start_year, end_year]
        
        # "seit X"
        since_match = re.search(r'seit\s+(\d{4})', query)
        if since_match:
            start_year = int(since_match.group(1))
            time_range['year_min'] = start_year
        
        return time_range
    
    def _extract_comparisons(self, query: str) -> Dict[str, Any]:
        """Vergleichsoperatoren extrahieren"""
        comparisons = {}
        
        # Größer/Kleiner-Vergleiche für Beträge
        if any(keyword in query for keyword in self.comparison_keywords['mehr']):
            comparisons['comparison_type'] = 'greater_than'
        elif any(keyword in query for keyword in self.comparison_keywords['weniger']):
            comparisons['comparison_type'] = 'less_than'
        elif any(keyword in query for keyword in self.comparison_keywords['zwischen']):
            comparisons['comparison_type'] = 'between'
        
        return comparisons
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Relevante Keywords extrahieren"""
        # Stopwords entfernen
        stopwords = {
            'der', 'die', 'das', 'den', 'dem', 'des', 'ein', 'eine', 'einer', 'eines',
            'und', 'oder', 'aber', 'doch', 'dann', 'also', 'noch', 'nur', 'schon',
            'auch', 'sehr', 'hier', 'dort', 'da', 'so', 'wie', 'was', 'wenn', 'als',
            'bei', 'mit', 'nach', 'vor', 'auf', 'für', 'zu', 'an', 'von', 'in', 'im',
            'ist', 'sind', 'war', 'waren', 'hat', 'haben', 'wird', 'werden', 'kann',
            'könnte', 'soll', 'sollte', 'muss', 'müssen', 'darf', 'dürfen'
        }
        
        # Query in Wörter aufteilen
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Stopwords und kurze Wörter entfernen
        keywords = [word for word in words 
                   if word not in stopwords and len(word) > 2]
        
        # Duplikate entfernen, Reihenfolge beibehalten
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords
    
    def _analyze_context(self, query: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Kontext der Anfrage analysieren"""
        context = {
            'question_type': self._detect_question_type(query),
            'temporal_context': self._analyze_temporal_context(query, entities),
            'scope': self._analyze_scope(query),
            'specificity': self._analyze_specificity(entities)
        }
        
        return context
    
    def _detect_question_type(self, query: str) -> str:
        """Art der Frage erkennen"""
        for question_type, keywords in self.question_keywords.items():
            if any(keyword in query for keyword in keywords):
                return question_type
        
        return 'statement'
    
    def _analyze_temporal_context(self, query: str, entities: Dict[str, Any]) -> str:
        """Zeitlichen Kontext analysieren"""
        if 'year' in entities:
            if isinstance(entities['year'], list):
                return 'multi_year'
            else:
                current_year = datetime.now().year
                if entities['year'] == current_year:
                    return 'current'
                elif entities['year'] == current_year - 1:
                    return 'recent_past'
                else:
                    return 'historical'
        
        if any(keyword in query for keyword in self.time_keywords['aktuell']):
            return 'current'
        elif any(keyword in query for keyword in self.time_keywords['vergangen']):
            return 'past'
        
        return 'unspecified'
    
    def _analyze_scope(self, query: str) -> str:
        """Umfang der Anfrage analysieren"""
        if any(keyword in query for keyword in ['alle', 'gesamt', 'komplett', 'vollständig']):
            return 'comprehensive'
        elif any(keyword in query for keyword in ['top', 'größte', 'höchste', 'wichtigste']):
            return 'top_results'
        elif any(keyword in query for keyword in ['einzeln', 'spezifisch', 'bestimmte']):
            return 'specific'
        else:
            return 'general'
    
    def _analyze_specificity(self, entities: Dict[str, Any]) -> float:
        """Spezifität der Anfrage bewerten (0.0 - 1.0)"""
        specificity_score = 0.0
        
        # Punkte für verschiedene Entitäten
        if 'year' in entities:
            specificity_score += 0.3
        if 'category' in entities:
            specificity_score += 0.2
        if 'amount' in entities or 'amount_min' in entities or 'amount_max' in entities:
            specificity_score += 0.2
        if 'document_type' in entities:
            specificity_score += 0.2
        if len(entities) > 3:
            specificity_score += 0.1
        
        return min(1.0, specificity_score)
    
    def _calculate_confidence(self, intent: str, entities: Dict[str, Any], keywords: List[str]) -> float:
        """Vertrauen in die Analyse berechnen"""
        confidence = 0.5  # Basis-Vertrauen
        
        # Intent-spezifisches Vertrauen
        if intent != 'general_search':
            confidence += 0.2
        
        # Entitäten erhöhen Vertrauen
        confidence += min(0.2, len(entities) * 0.05)
        
        # Keywords erhöhen Vertrauen
        confidence += min(0.1, len(keywords) * 0.02)
        
        # spaCy-Modell verfügbar
        if HAS_SPACY and self.nlp_model:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """Vorschläge für Suchanfragen generieren"""
        suggestions = []
        
        # Basis-Vorschläge
        base_suggestions = [
            "Wie viel gab die Gemeinde 2023 für Straßen aus?",
            "Zeige mir alle Gemeinderatsprotokolle von 2022",
            "Welche Ausgaben über 10.000 Euro gab es im letzten Jahr?",
            "Finde Dokumente über Wasserleitungsprojekte",
            "Wie entwickelten sich die Personalkosten zwischen 2020 und 2023?",
            "Zeige mir die größten Ausgaben der letzten 5 Jahre"
        ]
        
        # Ähnliche Vorschläge basierend auf Eingabe
        if partial_query:
            partial_lower = partial_query.lower()
            for suggestion in base_suggestions:
                if any(word in suggestion.lower() for word in partial_lower.split()):
                    suggestions.append(suggestion)
        
        # Falls keine passenden gefunden, alle Basis-Vorschläge zurückgeben
        if not suggestions:
            suggestions = base_suggestions[:3]
        
        return suggestions
    
    def explain_query_analysis(self, analysis_result: Dict[str, Any]) -> str:
        """Analyse-Ergebnis in verständlicher Form erklären"""
        explanation_parts = []
        
        # Intent erklären
        intent_explanations = {
            'financial_search': 'Suche nach Finanzdaten',
            'document_search': 'Suche nach Dokumenten',
            'protocol_search': 'Suche nach Protokollen',
            'statistics_search': 'Suche nach Statistiken',
            'general_search': 'Allgemeine Suche'
        }
        
        intent = analysis_result.get('intent', 'general_search')
        explanation_parts.append(f"Erkannte Absicht: {intent_explanations.get(intent, intent)}")
        
        # Entitäten erklären
        entities = analysis_result.get('entities', {})
        if entities:
            entity_explanations = []
            
            if 'year' in entities:
                year = entities['year']
                if isinstance(year, list):
                    entity_explanations.append(f"Jahre: {', '.join(map(str, year))}")
                else:
                    entity_explanations.append(f"Jahr: {year}")
            
            if 'category' in entities:
                entity_explanations.append(f"Kategorie: {entities['category']}")
            
            if 'amount' in entities:
                entity_explanations.append(f"Betrag: {entities['amount']:,.2f} €")
            elif 'amount_min' in entities or 'amount_max' in entities:
                amount_range = []
                if 'amount_min' in entities:
                    amount_range.append(f"ab {entities['amount_min']:,.2f} €")
                if 'amount_max' in entities:
                    amount_range.append(f"bis {entities['amount_max']:,.2f} €")
                entity_explanations.append(f"Betrag: {' '.join(amount_range)}")
            
            if entity_explanations:
                explanation_parts.append(f"Erkannte Parameter: {', '.join(entity_explanations)}")
        
        # Vertrauen erklären
        confidence = analysis_result.get('confidence', 0.5)
        confidence_text = "hoch" if confidence > 0.8 else "mittel" if confidence > 0.6 else "niedrig"
        explanation_parts.append(f"Vertrauen in die Analyse: {confidence_text} ({confidence:.1%})")
        
        return " | ".join(explanation_parts)
    
    def get_supported_languages(self) -> List[str]:
        """Unterstützte Sprachen zurückgeben"""
        return ['de', 'deutsch', 'german']
    
    def get_capabilities(self) -> Dict[str, Any]:
        """NLP-Fähigkeiten zurückgeben"""
        return {
            'languages': self.get_supported_languages(),
            'intents': ['financial_search', 'document_search', 'protocol_search', 'statistics_search', 'general_search'],
            'entities': ['year', 'category', 'amount', 'document_type', 'time_range'],
            'spacy_available': HAS_SPACY,
            'model_loaded': self.nlp_model is not None,
            'features': [
                'German language processing',
                'Intent detection',
                'Entity extraction',
                'Temporal analysis',
                'Amount recognition',
                'Category classification',
                'Query suggestions'
            ]
        }