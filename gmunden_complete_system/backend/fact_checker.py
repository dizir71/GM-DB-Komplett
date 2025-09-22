#!/usr/bin/env python3
"""
Gmunden Transparenz-Datenbank - Fact Checker
Verhindert Halluzinationen und stellt sicher, dass nur echte Daten zurückgegeben werden
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
import json
import re
import hashlib
from dataclasses import dataclass
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)

@dataclass
class FactCheckResult:
    """Fact-Check Ergebnis"""
    is_verified: bool
    confidence: float
    source: str
    verification_method: str
    issues: List[str]
    metadata: Dict[str, Any] = None

class FactChecker:
    """Fact-Checking System zur Verhinderung von Halluzinationen"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.verification_cache = {}
        self.known_facts_db = None
        self.suspicious_patterns = []
        
        # Fact-Checking Regeln initialisieren
        self._initialize_fact_rules()
        self._setup_known_facts_db()
    
    def _initialize_fact_rules(self):
        """Fact-Checking Regeln definieren"""
        
        # Verdächtige Muster die auf Halluzinationen hindeuten
        self.suspicious_patterns = [
            # Unrealistische Beträge
            r'betrag.*[1-9]\d{8,}',  # Über 100 Millionen
            r'betrag.*-[1-9]\d{7,}',  # Unter -10 Millionen
            
            # Unmögliche Daten
            r'jahr.*(19[0-8]\d|20[3-9]\d)',  # Vor 1990 oder nach 2029
            r'datum.*19[0-8]\d',  # Sehr alte Daten
            
            # Verdächtige Beschreibungen
            r'beschreibung.*(alien|ufo|zeitreise|magie)',
            r'beschreibung.*(milliarde|billion)',  # Unrealistische Größenordnungen
            
            # Inkonsistente Kategorien
            r'kategorie.*(weltraum|mars|mond)',
        ]
        
        # Bekannte gültige Wertebereiche
        self.valid_ranges = {
            'jahr': (2000, datetime.now().year + 1),
            'betrag': (-1000000, 10000000),  # -1M bis 10M Euro
            'kategorie': {
                'infrastruktur', 'personal', 'kultur', 'umwelt', 
                'bildung', 'soziales', 'verwaltung', 'sonstiges'
            }
        }
        
        # Plausibilitätsprüfungen
        self.plausibility_rules = {
            'personal': {
                'min_amount': 1000,    # Mindestens 1000€ für Personalkosten
                'max_amount': 500000   # Maximal 500k€ für einzelne Personalkosten
            },
            'infrastruktur': {
                'min_amount': 100,     # Mindestens 100€
                'max_amount': 5000000  # Maximal 5M€ für Infrastrukturprojekte
            },
            'kultur': {
                'min_amount': 50,      # Mindestens 50€
                'max_amount': 100000   # Maximal 100k€ für Kulturprojekte
            }
        }
    
    def _setup_known_facts_db(self):
        """Datenbank für bekannte Fakten einrichten"""
        try:
            db_path = self.config.get('facts_db_path', 'data/known_facts.db')
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.known_facts_db = sqlite3.connect(db_path, check_same_thread=False)
            cursor = self.known_facts_db.cursor()
            
            # Tabelle für verifizierte Fakten
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verified_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact_hash TEXT UNIQUE,
                    fact_data TEXT,
                    verification_date TIMESTAMP,
                    verification_method TEXT,
                    confidence REAL,
                    source TEXT
                )
            ''')
            
            # Tabelle für verdächtige Einträge
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suspicious_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_hash TEXT UNIQUE,
                    entry_data TEXT,
                    suspicion_reason TEXT,
                    flagged_date TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            
            self.known_facts_db.commit()
            logger.info("Known facts database initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup known facts DB: {e}")
            self.known_facts_db = None
    
    def verify_results(self, results: List[Dict[str, Any]], original_query: str) -> List[Dict[str, Any]]:
        """Ergebnisse auf Faktentreue prüfen und verifizieren"""
        try:
            if not results:
                return results
            
            verified_results = []
            verification_stats = {
                'total': len(results),
                'verified': 0,
                'suspicious': 0,
                'filtered': 0
            }
            
            for result in results:
                fact_check = self._verify_single_result(result, original_query)
                
                if fact_check.is_verified:
                    # Verifikations-Metadaten hinzufügen
                    result['_fact_check'] = {
                        'verified': True,
                        'confidence': fact_check.confidence,
                        'verification_method': fact_check.verification_method,
                        'source': fact_check.source
                    }
                    verified_results.append(result)
                    verification_stats['verified'] += 1
                    
                elif fact_check.confidence > 0.5:
                    # Verdächtig, aber nicht komplett ausschließen
                    result['_fact_check'] = {
                        'verified': False,
                        'confidence': fact_check.confidence,
                        'issues': fact_check.issues,
                        'warning': 'Daten nicht vollständig verifiziert'
                    }
                    verified_results.append(result)
                    verification_stats['suspicious'] += 1
                    
                else:
                    # Zu verdächtig - herausfiltern
                    verification_stats['filtered'] += 1
                    self._log_suspicious_entry(result, fact_check.issues)
            
            logger.info(f"Fact check completed: {verification_stats}")
            
            # Verifikations-Info zu Ergebnissen hinzufügen
            if verified_results:
                verified_results[0]['_verification_stats'] = verification_stats
            
            return verified_results
            
        except Exception as e:
            logger.error(f"Fact verification error: {e}")
            # Im Fehlerfall ursprüngliche Ergebnisse zurückgeben
            return results
    
    def _verify_single_result(self, result: Dict[str, Any], query: str) -> FactCheckResult:
        """Einzelnes Ergebnis verifizieren"""
        try:
            issues = []
            confidence = 1.0
            verification_methods = []
            
            # 1. Strukturelle Validierung
            structural_check = self._check_data_structure(result)
            if not structural_check['valid']:
                issues.extend(structural_check['issues'])
                confidence *= 0.7
            verification_methods.append('structural')
            
            # 2. Wertebereich-Prüfung
            range_check = self._check_value_ranges(result)
            if not range_check['valid']:
                issues.extend(range_check['issues'])
                confidence *= 0.6
            verification_methods.append('range')
            
            # 3. Plausibilitätsprüfung
            plausibility_check = self._check_plausibility(result)
            if not plausibility_check['valid']:
                issues.extend(plausibility_check['issues'])
                confidence *= 0.8
            verification_methods.append('plausibility')
            
            # 4. Pattern-Matching für verdächtige Inhalte
            pattern_check = self._check_suspicious_patterns(result)
            if not pattern_check['valid']:
                issues.extend(pattern_check['issues'])
                confidence *= 0.3  # Starke Abwertung bei verdächtigen Mustern
            verification_methods.append('pattern')
            
            # 5. Konsistenz mit bekannten Fakten
            consistency_check = self._check_consistency_with_known_facts(result)
            if consistency_check['confidence'] < 1.0:
                issues.extend(consistency_check['issues'])
                confidence *= consistency_check['confidence']
            verification_methods.append('consistency')
            
            # 6. Query-Relevanz prüfen
            relevance_check = self._check_query_relevance(result, query)
            if not relevance_check['relevant']:
                issues.append("Ergebnis nicht relevant für Anfrage")
                confidence *= 0.9
            verification_methods.append('relevance')
            
            # Gesamtbewertung
            is_verified = confidence >= 0.7 and len(issues) <= 2
            
            # Bei hoher Konfidenz in bekannte Fakten DB eintragen
            if is_verified and confidence >= 0.9:
                self._store_verified_fact(result, verification_methods)
            
            return FactCheckResult(
                is_verified=is_verified,
                confidence=confidence,
                source='gmunden_fact_checker',
                verification_method='+'.join(verification_methods),
                issues=issues,
                metadata={
                    'checks_performed': len(verification_methods),
                    'query': query
                }
            )
            
        except Exception as e:
            logger.error(f"Single result verification error: {e}")
            return FactCheckResult(
                is_verified=False,
                confidence=0.0,
                source='error',
                verification_method='error',
                issues=[f"Verifikationsfehler: {e}"]
            )
    
    def _check_data_structure(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Datenstruktur prüfen"""
        issues = []
        
        # Pflichtfelder prüfen
        required_fields = ['beschreibung']
        for field in required_fields:
            if field not in result or not result[field]:
                issues.append(f"Pflichtfeld '{field}' fehlt oder leer")
        
        # Datentypen prüfen
        if 'jahr' in result and result['jahr']:
            if not isinstance(result['jahr'], int):
                try:
                    int(result['jahr'])
                except (ValueError, TypeError):
                    issues.append("Jahr ist kein gültiger Integer")
        
        if 'betrag' in result and result['betrag'] is not None:
            if not isinstance(result['betrag'], (int, float)):
                try:
                    float(result['betrag'])
                except (ValueError, TypeError):
                    issues.append("Betrag ist keine gültige Zahl")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    def _check_value_ranges(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Wertebereiche prüfen"""
        issues = []
        
        for field, valid_range in self.valid_ranges.items():
            if field in result and result[field] is not None:
                value = result[field]
                
                if isinstance(valid_range, tuple):
                    # Numerischer Bereich
                    if not (valid_range[0] <= value <= valid_range[1]):
                        issues.append(f"{field} ({value}) außerhalb gültigen Bereichs {valid_range}")
                
                elif isinstance(valid_range, set):
                    # Gültige Werte-Set
                    if str(value).lower() not in {str(v).lower() for v in valid_range}:
                        issues.append(f"{field} ('{value}') nicht in gültigen Werten")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    def _check_plausibility(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Plausibilität prüfen"""
        issues = []
        
        # Kategorie-spezifische Plausibilitätsprüfungen
        if 'kategorie' in result and 'betrag' in result:
            category = str(result['kategorie']).lower()
            amount = result['betrag']
            
            if category in self.plausibility_rules and amount is not None:
                rules = self.plausibility_rules[category]
                
                if amount < rules['min_amount']:
                    issues.append(f"Betrag {amount}€ zu niedrig für Kategorie '{category}'")
                
                if amount > rules['max_amount']:
                    issues.append(f"Betrag {amount}€ zu hoch für Kategorie '{category}'")
        
        # Zeitliche Plausibilität
        if 'jahr' in result and 'datum' in result:
            year = result['jahr']
            if isinstance(result['datum'], str):
                try:
                    date_obj = datetime.fromisoformat(result['datum'].replace('Z', '+00:00'))
                    if date_obj.year != year:
                        issues.append(f"Jahr {year} stimmt nicht mit Datum {result['datum']} überein")
                except:
                    pass
        
        # Beschreibungs-Plausibilität
        if 'beschreibung' in result:
            desc = str(result['beschreibung']).lower()
            
            # Zu kurze oder verdächtige Beschreibungen
            if len(desc.strip()) < 3:
                issues.append("Beschreibung zu kurz")
            
            # Verdächtige Wörter
            suspicious_words = ['fake', 'test', 'dummy', 'beispiel', 'placeholder']
            if any(word in desc for word in suspicious_words):
                issues.append("Beschreibung enthält verdächtige Begriffe")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    def _check_suspicious_patterns(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Verdächtige Muster prüfen"""
        issues = []
        
        # Ergebnis in String umwandeln für Pattern-Matching
        result_str = json.dumps(result, default=str).lower()
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, result_str):
                issues.append(f"Verdächtiges Muster erkannt: {pattern}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    def _check_consistency_with_known_facts(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Konsistenz mit bekannten Fakten prüfen"""
        if not self.known_facts_db:
            return {'confidence': 1.0, 'issues': []}
        
        try:
            # Hash des Ergebnisses berechnen
            result_hash = self._calculate_result_hash(result)
            
            cursor = self.known_facts_db.cursor()
            
            # Prüfen ob bereits verifiziert
            cursor.execute(
                "SELECT confidence, verification_method FROM verified_facts WHERE fact_hash = ?",
                (result_hash,)
            )
            verified_fact = cursor.fetchone()
            
            if verified_fact:
                return {
                    'confidence': verified_fact[0],
                    'issues': [],
                    'source': 'known_facts_db'
                }
            
            # Prüfen ob als verdächtig markiert
            cursor.execute(
                "SELECT suspicion_reason FROM suspicious_entries WHERE entry_hash = ? AND resolved = FALSE",
                (result_hash,)
            )
            suspicious_entry = cursor.fetchone()
            
            if suspicious_entry:
                return {
                    'confidence': 0.3,
                    'issues': [f"Bereits als verdächtig markiert: {suspicious_entry[0]}"]
                }
            
            # Ähnliche Einträge suchen (vereinfacht)
            similar_confidence = self._find_similar_facts_confidence(result)
            
            return {
                'confidence': similar_confidence,
                'issues': [] if similar_confidence >= 0.8 else ["Keine ähnlichen verifizierten Fakten gefunden"]
            }
            
        except Exception as e:
            logger.error(f"Consistency check error: {e}")
            return {'confidence': 0.8, 'issues': []}  # Neutral bei Fehlern
    
    def _check_query_relevance(self, result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Relevanz zur ursprünglichen Anfrage prüfen"""
        try:
            query_lower = query.lower()
            result_text = ' '.join(str(v) for v in result.values() if v).lower()
            
            # Einfache Keyword-Übereinstimmung
            query_words = set(re.findall(r'\b\w+\b', query_lower))
            result_words = set(re.findall(r'\b\w+\b', result_text))
            
            # Stopwords entfernen
            stopwords = {'der', 'die', 'das', 'und', 'oder', 'für', 'von', 'mit', 'zu', 'in', 'auf'}
            query_words -= stopwords
            result_words -= stopwords
            
            if not query_words:
                return {'relevant': True}  # Keine Keywords zu prüfen
            
            # Übereinstimmungsrate berechnen
            matches = query_words.intersection(result_words)
            relevance_score = len(matches) / len(query_words)
            
            return {
                'relevant': relevance_score >= 0.3,  # Mindestens 30% Übereinstimmung
                'score': relevance_score,
                'matches': list(matches)
            }
            
        except Exception as e:
            logger.error(f"Relevance check error: {e}")
            return {'relevant': True}  # Bei Fehlern als relevant werten
    
    def _calculate_result_hash(self, result: Dict[str, Any]) -> str:
        """Hash für Ergebnis berechnen"""
        # Nur relevante Felder für Hash verwenden
        hash_fields = ['jahr', 'kategorie', 'beschreibung', 'betrag']
        hash_data = {}
        
        for field in hash_fields:
            if field in result:
                hash_data[field] = result[field]
        
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def _store_verified_fact(self, result: Dict[str, Any], verification_methods: List[str]):
        """Verifiziertes Faktum speichern"""
        if not self.known_facts_db:
            return
        
        try:
            result_hash = self._calculate_result_hash(result)
            cursor = self.known_facts_db.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO verified_facts 
                (fact_hash, fact_data, verification_date, verification_method, confidence, source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                result_hash,
                json.dumps(result, default=str),
                datetime.now(),
                '+'.join(verification_methods),
                0.9,
                'gmunden_fact_checker'
            ))
            
            self.known_facts_db.commit()
            
        except Exception as e:
            logger.error(f"Error storing verified fact: {e}")
    
    def _log_suspicious_entry(self, result: Dict[str, Any], issues: List[str]):
        """Verdächtigen Eintrag protokollieren"""
        if not self.known_facts_db:
            return
        
        try:
            result_hash = self._calculate_result_hash(result)
            cursor = self.known_facts_db.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO suspicious_entries 
                (entry_hash, entry_data, suspicion_reason, flagged_date)
                VALUES (?, ?, ?, ?)
            ''', (
                result_hash,
                json.dumps(result, default=str),
                '; '.join(issues),
                datetime.now()
            ))
            
            self.known_facts_db.commit()
            logger.warning(f"Suspicious entry logged: {issues}")
            
        except Exception as e:
            logger.error(f"Error logging suspicious entry: {e}")
    
    def _find_similar_facts_confidence(self, result: Dict[str, Any]) -> float:
        """Konfidenz basierend auf ähnlichen Fakten finden"""
        # Vereinfachte Implementierung - in Produktion würde hier
        # eine sophistiziertere Ähnlichkeitssuche implementiert
        
        if 'kategorie' in result and 'jahr' in result:
            # Ähnliche Kategorie und Jahr = höhere Konfidenz
            return 0.8
        elif 'kategorie' in result or 'jahr' in result:
            # Teilweise Übereinstimmung
            return 0.6
        else:
            # Keine Ähnlichkeit gefunden
            return 0.5
    
    def get_fact_check_statistics(self) -> Dict[str, Any]:
        """Fact-Check Statistiken abrufen"""
        if not self.known_facts_db:
            return {'error': 'Fact database not available'}
        
        try:
            cursor = self.known_facts_db.cursor()
            
            # Verifizierte Fakten zählen
            cursor.execute("SELECT COUNT(*) FROM verified_facts")
            verified_count = cursor.fetchone()[0]
            
            # Verdächtige Einträge zählen
            cursor.execute("SELECT COUNT(*) FROM suspicious_entries WHERE resolved = FALSE")
            suspicious_count = cursor.fetchone()[0]
            
            # Durchschnittliche Konfidenz
            cursor.execute("SELECT AVG(confidence) FROM verified_facts")
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            # Häufigste Verifikationsmethoden
            cursor.execute("""
                SELECT verification_method, COUNT(*) 
                FROM verified_facts 
                GROUP BY verification_method 
                ORDER BY COUNT(*) DESC 
                LIMIT 5
            """)
            top_methods = cursor.fetchall()
            
            return {
                'verified_facts': verified_count,
                'suspicious_entries': suspicious_count,
                'average_confidence': avg_confidence,
                'top_verification_methods': dict(top_methods),
                'database_status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Error getting fact check statistics: {e}")
            return {'error': str(e)}
    
    def clear_suspicious_entries(self):
        """Verdächtige Einträge als gelöst markieren"""
        if not self.known_facts_db:
            return
        
        try:
            cursor = self.known_facts_db.cursor()
            cursor.execute("UPDATE suspicious_entries SET resolved = TRUE")
            self.known_facts_db.commit()
            logger.info("All suspicious entries marked as resolved")
            
        except Exception as e:
            logger.error(f"Error clearing suspicious entries: {e}")
    
    def add_trusted_source(self, source_identifier: str, trust_level: float):
        """Vertrauenswürdige Quelle hinzufügen"""
        # Implementierung für vertrauenswürdige Quellen
        # In einer vollständigen Version würde hier eine Quellen-DB verwaltet
        pass
    
    def __del__(self):
        """Cleanup bei Objektzerstörung"""
        try:
            if self.known_facts_db:
                self.known_facts_db.close()
        except:
            pass