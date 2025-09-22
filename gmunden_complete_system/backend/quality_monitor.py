#!/usr/bin/env python3
"""
Gmunden Transparenz-Datenbank - Qualitätsmonitor
Überwacht Datenqualität und verhindert Halluzinationen
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import re
import hashlib
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class QualityCheck:
    """Qualitätsprüfung-Ergebnis"""
    check_type: str
    passed: bool
    score: float
    message: str
    details: Dict[str, Any] = None

class QualityMonitor:
    """Qualitätsüberwachung für Datenintegrität"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.min_quality_threshold = self.config.get('min_quality_threshold', 0.7)
        self.checks_history = []
        
        # Qualitätskriterien definieren
        self._define_quality_criteria()
    
    def _define_quality_criteria(self):
        """Qualitätskriterien definieren"""
        self.quality_criteria = {
            'data_completeness': {
                'weight': 0.3,
                'min_fields': ['jahr', 'beschreibung'],
                'preferred_fields': ['kategorie', 'betrag', 'datum']
            },
            'data_consistency': {
                'weight': 0.25,
                'year_range': (2000, datetime.now().year + 1),
                'amount_range': (-1000000, 10000000)
            },
            'data_accuracy': {
                'weight': 0.25,
                'required_patterns': {
                    'year': r'^(19|20)\d{2}$',
                    'amount': r'^-?\d+(\.\d{2})?$'
                }
            },
            'data_freshness': {
                'weight': 0.2,
                'max_age_days': 365
            }
        }
    
    def check_results(self, results: List[Dict[str, Any]]) -> float:
        """Ergebnisse auf Qualität prüfen"""
        try:
            if not results:
                return 0.0
            
            quality_checks = []
            
            # Vollständigkeitsprüfung
            completeness_check = self._check_completeness(results)
            quality_checks.append(completeness_check)
            
            # Konsistenzprüfung
            consistency_check = self._check_consistency(results)
            quality_checks.append(consistency_check)
            
            # Genauigkeitsprüfung
            accuracy_check = self._check_accuracy(results)
            quality_checks.append(accuracy_check)
            
            # Aktualitätsprüfung
            freshness_check = self._check_freshness(results)
            quality_checks.append(freshness_check)
            
            # Gesamtqualität berechnen
            total_score = self._calculate_total_quality(quality_checks)
            
            # Prüfung zur Historie hinzufügen
            self.checks_history.append({
                'timestamp': datetime.now(),
                'total_score': total_score,
                'checks': quality_checks,
                'result_count': len(results)
            })
            
            logger.info(f"Quality check completed: {total_score:.2%}")
            return total_score
            
        except Exception as e:
            logger.error(f"Quality check error: {e}")
            return 0.5  # Fallback-Wert
    
    def _check_completeness(self, results: List[Dict]) -> QualityCheck:
        """Vollständigkeit der Daten prüfen"""
        try:
            criteria = self.quality_criteria['data_completeness']
            required_fields = criteria['min_fields']
            preferred_fields = criteria['preferred_fields']
            
            total_items = len(results)
            complete_items = 0
            field_coverage = {}
            
            for result in results:
                # Pflichtfelder prüfen
                has_required = all(field in result and result[field] for field in required_fields)
                
                # Optionale Felder zählen
                optional_count = sum(1 for field in preferred_fields 
                                   if field in result and result[field])
                
                if has_required:
                    complete_items += 1
                
                # Feldabdeckung tracken
                for field in required_fields + preferred_fields:
                    if field not in field_coverage:
                        field_coverage[field] = 0
                    if field in result and result[field]:
                        field_coverage[field] += 1
            
            completeness_score = complete_items / total_items if total_items > 0 else 0
            
            return QualityCheck(
                check_type='completeness',
                passed=completeness_score >= 0.8,
                score=completeness_score,
                message=f"{complete_items}/{total_items} Einträge vollständig",
                details={
                    'field_coverage': {k: v/total_items for k, v in field_coverage.items()},
                    'complete_items': complete_items,
                    'total_items': total_items
                }
            )
            
        except Exception as e:
            logger.error(f"Completeness check error: {e}")
            return QualityCheck('completeness', False, 0.0, f"Fehler: {e}")
    
    def _check_consistency(self, results: List[Dict]) -> QualityCheck:
        """Konsistenz der Daten prüfen"""
        try:
            criteria = self.quality_criteria['data_consistency']
            year_range = criteria['year_range']
            amount_range = criteria['amount_range']
            
            total_items = len(results)
            consistent_items = 0
            issues = []
            
            for i, result in enumerate(results):
                item_consistent = True
                
                # Jahr-Konsistenz
                if 'jahr' in result and result['jahr']:
                    year = result['jahr']
                    if not (year_range[0] <= year <= year_range[1]):
                        item_consistent = False
                        issues.append(f"Item {i}: Jahr {year} außerhalb gültigen Bereichs")
                
                # Betrag-Konsistenz
                if 'betrag' in result and result['betrag'] is not None:
                    amount = result['betrag']
                    if not (amount_range[0] <= amount <= amount_range[1]):
                        item_consistent = False
                        issues.append(f"Item {i}: Betrag {amount} außerhalb gültigen Bereichs")
                
                # Kategorie-Konsistenz
                if 'kategorie' in result and result['kategorie']:
                    category = result['kategorie'].lower()
                    valid_categories = ['infrastruktur', 'personal', 'kultur', 'umwelt', 
                                      'bildung', 'soziales', 'verwaltung', 'sonstiges']
                    if category not in valid_categories:
                        # Warnung, aber nicht als Fehler werten
                        issues.append(f"Item {i}: Unbekannte Kategorie '{category}'")
                
                if item_consistent:
                    consistent_items += 1
            
            consistency_score = consistent_items / total_items if total_items > 0 else 0
            
            return QualityCheck(
                check_type='consistency',
                passed=consistency_score >= 0.9,
                score=consistency_score,
                message=f"{consistent_items}/{total_items} Einträge konsistent",
                details={
                    'consistent_items': consistent_items,
                    'total_items': total_items,
                    'issues': issues[:10]  # Nur erste 10 Issues
                }
            )
            
        except Exception as e:
            logger.error(f"Consistency check error: {e}")
            return QualityCheck('consistency', False, 0.0, f"Fehler: {e}")
    
    def _check_accuracy(self, results: List[Dict]) -> QualityCheck:
        """Genauigkeit der Daten prüfen"""
        try:
            criteria = self.quality_criteria['data_accuracy']
            patterns = criteria['required_patterns']
            
            total_items = len(results)
            accurate_items = 0
            pattern_matches = {}
            
            for result in results:
                item_accurate = True
                
                # Pattern-Matching für verschiedene Felder
                for field, pattern in patterns.items():
                    if field in result and result[field] is not None:
                        value_str = str(result[field])
                        if not re.match(pattern, value_str):
                            item_accurate = False
                        
                        # Pattern-Statistiken
                        if field not in pattern_matches:
                            pattern_matches[field] = {'matches': 0, 'total': 0}
                        pattern_matches[field]['total'] += 1
                        if re.match(pattern, value_str):
                            pattern_matches[field]['matches'] += 1
                
                # Zusätzliche Genauigkeitsprüfungen
                if 'beschreibung' in result and result['beschreibung']:
                    desc = result['beschreibung'].strip()
                    if len(desc) < 3:  # Zu kurze Beschreibungen
                        item_accurate = False
                
                if item_accurate:
                    accurate_items += 1
            
            accuracy_score = accurate_items / total_items if total_items > 0 else 0
            
            return QualityCheck(
                check_type='accuracy',
                passed=accuracy_score >= 0.85,
                score=accuracy_score,
                message=f"{accurate_items}/{total_items} Einträge genau",
                details={
                    'accurate_items': accurate_items,
                    'total_items': total_items,
                    'pattern_matches': pattern_matches
                }
            )
            
        except Exception as e:
            logger.error(f"Accuracy check error: {e}")
            return QualityCheck('accuracy', False, 0.0, f"Fehler: {e}")
    
    def _check_freshness(self, results: List[Dict]) -> QualityCheck:
        """Aktualität der Daten prüfen"""
        try:
            criteria = self.quality_criteria['data_freshness']
            max_age_days = criteria['max_age_days']
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            total_items = len(results)
            fresh_items = 0
            date_info = {'has_date': 0, 'recent_date': 0, 'no_date': 0}
            
            for result in results:
                item_fresh = True
                
                # Datum prüfen (verschiedene Felder)
                date_fields = ['datum', 'created_at', 'last_modified']
                item_date = None
                
                for field in date_fields:
                    if field in result and result[field]:
                        try:
                            if isinstance(result[field], str):
                                item_date = datetime.fromisoformat(result[field].replace('Z', '+00:00'))
                            elif isinstance(result[field], datetime):
                                item_date = result[field]
                            break
                        except:
                            continue
                
                if item_date:
                    date_info['has_date'] += 1
                    if item_date >= cutoff_date:
                        date_info['recent_date'] += 1
                    else:
                        item_fresh = False
                else:
                    date_info['no_date'] += 1
                    # Ohne Datum als "frisch" werten (könnte historische Daten sein)
                
                if item_fresh:
                    fresh_items += 1
            
            # Freshness-Score: Berücksichtigt sowohl Aktualität als auch Verfügbarkeit von Daten
            if date_info['has_date'] > 0:
                freshness_score = date_info['recent_date'] / date_info['has_date']
            else:
                freshness_score = 0.8  # Fallback für Daten ohne Zeitstempel
            
            return QualityCheck(
                check_type='freshness',
                passed=freshness_score >= 0.6,
                score=freshness_score,
                message=f"{date_info['recent_date']}/{date_info['has_date']} Einträge aktuell",
                details={
                    'fresh_items': fresh_items,
                    'total_items': total_items,
                    'date_info': date_info,
                    'cutoff_date': cutoff_date.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Freshness check error: {e}")
            return QualityCheck('freshness', False, 0.0, f"Fehler: {e}")
    
    def _calculate_total_quality(self, quality_checks: List[QualityCheck]) -> float:
        """Gesamtqualität aus einzelnen Prüfungen berechnen"""
        total_score = 0.0
        total_weight = 0.0
        
        for check in quality_checks:
            if check.check_type in self.quality_criteria:
                weight = self.quality_criteria[check.check_type]['weight']
                total_score += check.score * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def validate_query_result(self, query: str, results: List[Dict]) -> Dict[str, Any]:
        """Suchergebnis gegen Query validieren"""
        try:
            validation = {
                'is_valid': True,
                'confidence': 1.0,
                'issues': [],
                'recommendations': []
            }
            
            # Leere Ergebnisse prüfen
            if not results:
                validation['issues'].append("Keine Ergebnisse gefunden")
                validation['confidence'] = 0.3
                validation['recommendations'].append("Versuchen Sie eine breitere Suchanfrage")
                return validation
            
            # Relevanz prüfen
            query_lower = query.lower()
            relevant_results = 0
            
            for result in results:
                # Einfache Relevanzprüfung
                result_text = ' '.join(str(v) for v in result.values() if v).lower()
                query_words = query_lower.split()
                matches = sum(1 for word in query_words if word in result_text)
                
                if matches > 0:
                    relevant_results += 1
            
            relevance_ratio = relevant_results / len(results)
            
            if relevance_ratio < 0.5:
                validation['issues'].append(f"Nur {relevance_ratio:.1%} der Ergebnisse scheinen relevant")
                validation['confidence'] *= 0.7
                validation['recommendations'].append("Präzisieren Sie Ihre Suchanfrage")
            
            # Datenqualität einbeziehen
            quality_score = self.check_results(results)
            validation['confidence'] *= quality_score
            
            if quality_score < self.min_quality_threshold:
                validation['issues'].append(f"Datenqualität unter Schwellenwert ({quality_score:.1%})")
                validation['recommendations'].append("Datenquelle überprüfen")
            
            # Gesamtvalidierung
            validation['is_valid'] = (validation['confidence'] >= 0.6 and 
                                    len(validation['issues']) <= 2)
            
            return validation
            
        except Exception as e:
            logger.error(f"Query validation error: {e}")
            return {
                'is_valid': False,
                'confidence': 0.0,
                'issues': [f"Validierungsfehler: {e}"],
                'recommendations': ["Kontaktieren Sie den Support"]
            }
    
    def get_quality_report(self) -> Dict[str, Any]:
        """Qualitätsbericht erstellen"""
        try:
            if not self.checks_history:
                return {'message': 'Noch keine Qualitätsprüfungen durchgeführt'}
            
            recent_checks = self.checks_history[-10:]  # Letzte 10 Prüfungen
            
            # Durchschnittliche Qualität
            avg_quality = sum(check['total_score'] for check in recent_checks) / len(recent_checks)
            
            # Trend berechnen
            if len(recent_checks) >= 2:
                trend = recent_checks[-1]['total_score'] - recent_checks[0]['total_score']
            else:
                trend = 0.0
            
            # Häufigste Probleme
            all_issues = []
            for check in recent_checks:
                for quality_check in check['checks']:
                    if not quality_check.passed:
                        all_issues.append(quality_check.check_type)
            
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            report = {
                'summary': {
                    'average_quality': avg_quality,
                    'trend': trend,
                    'total_checks': len(self.checks_history),
                    'recent_checks': len(recent_checks)
                },
                'quality_breakdown': {
                    'excellent': sum(1 for c in recent_checks if c['total_score'] >= 0.9),
                    'good': sum(1 for c in recent_checks if 0.7 <= c['total_score'] < 0.9),
                    'fair': sum(1 for c in recent_checks if 0.5 <= c['total_score'] < 0.7),
                    'poor': sum(1 for c in recent_checks if c['total_score'] < 0.5)
                },
                'common_issues': sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                'recommendations': self._generate_recommendations(avg_quality, issue_counts),
                'last_check': recent_checks[-1]['timestamp'].isoformat() if recent_checks else None
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Quality report error: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, avg_quality: float, issue_counts: Dict[str, int]) -> List[str]:
        """Empfehlungen basierend auf Qualitätsanalyse generieren"""
        recommendations = []
        
        if avg_quality < 0.6:
            recommendations.append("Datenqualität ist kritisch - sofortige Überprüfung erforderlich")
        elif avg_quality < 0.8:
            recommendations.append("Datenqualität sollte verbessert werden")
        
        # Spezifische Empfehlungen basierend auf häufigen Problemen
        for issue_type, count in issue_counts.items():
            if count >= 3:  # Häufiges Problem
                if issue_type == 'completeness':
                    recommendations.append("Vollständigkeit der Datenfelder verbessern")
                elif issue_type == 'consistency':
                    recommendations.append("Datenkonsistenz-Regeln überprüfen")
                elif issue_type == 'accuracy':
                    recommendations.append("Datenvalidierung bei der Eingabe verstärken")
                elif issue_type == 'freshness':
                    recommendations.append("Häufigere Datenaktualisierung einrichten")
        
        if not recommendations:
            recommendations.append("Datenqualität ist zufriedenstellend")
        
        return recommendations
    
    def reset_history(self):
        """Prüfungshistorie zurücksetzen"""
        self.checks_history = []
        logger.info("Quality check history reset")
    
    def get_quality_threshold(self) -> float:
        """Aktuellen Qualitätsschwellenwert zurückgeben"""
        return self.min_quality_threshold
    
    def set_quality_threshold(self, threshold: float):
        """Qualitätsschwellenwert setzen"""
        if 0.0 <= threshold <= 1.0:
            self.min_quality_threshold = threshold
            logger.info(f"Quality threshold set to {threshold:.1%}")
        else:
            raise ValueError("Threshold must be between 0.0 and 1.0")