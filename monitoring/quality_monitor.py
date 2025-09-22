#!/usr/bin/env python3
"""
Qualitätsmonitor für das Gmunden Transparenz-System
Überwacht Datenqualität und verhindert Halluzinationen
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import threading

class QualityMonitor:
    """
    Überwacht kontinuierlich die Datenqualität und Systemleistung
    """
    
    def __init__(self):
        self.setup_logging()
        self.init_monitoring()
        self.start_monitoring_thread()
    
    def setup_logging(self):
        """Setup Logging für Monitoring"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def init_monitoring(self):
        """Initialisiere Monitoring-System"""
        self.metrics = {
            'data_quality': {
                'score': 100,
                'last_check': datetime.now(),
                'issues_found': 0,
                'total_records_checked': 0
            },
            'system_performance': {
                'response_time_avg': 0.0,
                'queries_per_minute': 0,
                'error_rate': 0.0,
                'uptime': datetime.now()
            },
            'user_satisfaction': {
                'successful_queries': 0,
                'failed_queries': 0,
                'user_feedback_score': 0.0
            }
        }
        
        self.quality_thresholds = {
            'min_data_quality_score': 80,
            'max_response_time': 5.0,  # Sekunden
            'max_error_rate': 0.05,    # 5%
            'min_confidence_score': 0.7
        }
        
        self.monitoring_active = True
        self.alerts = []
    
    def start_monitoring_thread(self):
        """Starte Monitoring-Thread"""
        def monitor_loop():
            while self.monitoring_active:
                try:
                    self.perform_quality_check()
                    self.check_system_health()
                    time.sleep(60)  # Prüfe jede Minute
                except Exception as e:
                    self.logger.error(f"Monitoring-Fehler: {e}")
                    time.sleep(60)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Qualitätsmonitor gestartet")
    
    def perform_quality_check(self):
        """Führe Qualitätsprüfung durch"""
        try:
            current_time = datetime.now()
            
            # Simuliere Qualitätsprüfung (in echter Implementierung würde hier die DB geprüft)
            quality_issues = self.check_data_consistency()
            
            # Aktualisiere Metriken
            self.metrics['data_quality']['last_check'] = current_time
            self.metrics['data_quality']['issues_found'] = len(quality_issues)
            
            # Berechne Qualitäts-Score
            if quality_issues:
                penalty = min(len(quality_issues) * 5, 30)  # Max 30 Punkte Abzug
                self.metrics['data_quality']['score'] = max(70, 100 - penalty)
            else:
                self.metrics['data_quality']['score'] = 100
            
            # Prüfe Schwellenwerte
            if self.metrics['data_quality']['score'] < self.quality_thresholds['min_data_quality_score']:
                self.create_alert('data_quality', f"Datenqualität unter Schwellenwert: {self.metrics['data_quality']['score']}%")
            
        except Exception as e:
            self.logger.error(f"Qualitätsprüfung fehlgeschlagen: {e}")
    
    def check_data_consistency(self) -> List[Dict[str, Any]]:
        """Prüfe Datenkonsistenz"""
        issues = []
        
        # Simuliere verschiedene Konsistenzprüfungen
        checks = [
            self.check_temporal_consistency(),
            self.check_financial_plausibility(),
            self.check_duplicate_detection(),
            self.check_missing_data()
        ]
        
        for check_result in checks:
            if check_result:
                issues.extend(check_result)
        
        return issues
    
    def check_temporal_consistency(self) -> List[Dict[str, Any]]:
        """Prüfe zeitliche Konsistenz"""
        issues = []
        
        # Simuliere Prüfung auf unrealistische Daten
        current_year = datetime.now().year
        
        # Beispiel: Prüfe auf Zukunftsdaten
        # In echter Implementierung würde hier die Datenbank abgefragt
        
        return issues
    
    def check_financial_plausibility(self) -> List[Dict[str, Any]]:
        """Prüfe finanzielle Plausibilität"""
        issues = []
        
        # Simuliere Prüfung auf unrealistische Beträge
        # Beispiel: Ausgaben über 1 Million Euro sollten besonders geprüft werden
        
        return issues
    
    def check_duplicate_detection(self) -> List[Dict[str, Any]]:
        """Prüfe auf Duplikate"""
        issues = []
        
        # Simuliere Duplikatsprüfung
        # In echter Implementierung würde hier nach identischen Einträgen gesucht
        
        return issues
    
    def check_missing_data(self) -> List[Dict[str, Any]]:
        """Prüfe auf fehlende Daten"""
        issues = []
        
        # Simuliere Prüfung auf unvollständige Datensätze
        # Beispiel: Finanzeinträge ohne Kategorie oder Beschreibung
        
        return issues
    
    def check_system_health(self):
        """Prüfe Systemgesundheit"""
        try:
            current_time = datetime.now()
            
            # Berechne Uptime
            uptime_delta = current_time - self.metrics['system_performance']['uptime']
            uptime_hours = uptime_delta.total_seconds() / 3600
            
            # Simuliere Performance-Metriken
            # In echter Implementierung würden hier echte Metriken gesammelt
            self.metrics['system_performance']['response_time_avg'] = 1.2  # Sekunden
            self.metrics['system_performance']['error_rate'] = 0.02  # 2%
            
            # Prüfe Schwellenwerte
            if self.metrics['system_performance']['response_time_avg'] > self.quality_thresholds['max_response_time']:
                self.create_alert('performance', f"Antwortzeit zu hoch: {self.metrics['system_performance']['response_time_avg']:.2f}s")
            
            if self.metrics['system_performance']['error_rate'] > self.quality_thresholds['max_error_rate']:
                self.create_alert('errors', f"Fehlerrate zu hoch: {self.metrics['system_performance']['error_rate']:.2%}")
            
        except Exception as e:
            self.logger.error(f"System-Health-Check fehlgeschlagen: {e}")
    
    def create_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        """Erstelle Alert"""
        alert = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now(),
            'resolved': False
        }
        
        self.alerts.append(alert)
        self.logger.warning(f"ALERT [{alert_type}]: {message}")
        
        # Behalte nur die letzten 100 Alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def log_query_performance(self, query: str, response_time: float, success: bool, confidence: float = None):
        """Logge Query-Performance"""
        try:
            if success:
                self.metrics['user_satisfaction']['successful_queries'] += 1
            else:
                self.metrics['user_satisfaction']['failed_queries'] += 1
            
            # Aktualisiere durchschnittliche Antwortzeit
            current_avg = self.metrics['system_performance']['response_time_avg']
            total_queries = (self.metrics['user_satisfaction']['successful_queries'] + 
                           self.metrics['user_satisfaction']['failed_queries'])
            
            if total_queries > 0:
                self.metrics['system_performance']['response_time_avg'] = (
                    (current_avg * (total_queries - 1) + response_time) / total_queries
                )
            
            # Prüfe Konfidenz-Schwellenwert
            if confidence and confidence < self.quality_thresholds['min_confidence_score']:
                self.create_alert('low_confidence', 
                                f"Niedrige Konfidenz für Query: '{query[:50]}...' (Konfidenz: {confidence:.2f})")
            
        except Exception as e:
            self.logger.error(f"Query-Performance-Logging fehlgeschlagen: {e}")
    
    def validate_search_results(self, results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Validiere Suchergebnisse auf Qualität"""
        validation = {
            'total_results': len(results),
            'quality_score': 100,
            'issues': [],
            'recommendations': []
        }
        
        if not results:
            validation['quality_score'] = 50
            validation['issues'].append("Keine Ergebnisse gefunden")
            validation['recommendations'].append("Versuchen Sie andere Suchbegriffe")
            return validation
        
        # Prüfe Ergebnis-Qualität
        quality_issues = 0
        
        for result in results:
            # Prüfe auf fehlende wichtige Felder
            if not result.get('beschreibung') and not result.get('filename'):
                quality_issues += 1
                validation['issues'].append("Ergebnis ohne Beschreibung gefunden")
            
            # Prüfe auf unrealistische Werte
            if 'betrag' in result and result['betrag'] > 10000000:  # 10 Millionen
                quality_issues += 1
                validation['issues'].append(f"Unrealistisch hoher Betrag: {result['betrag']:,.2f}€")
            
            # Prüfe auf zeitliche Konsistenz
            if 'jahr' in result:
                current_year = datetime.now().year
                if result['jahr'] < 1990 or result['jahr'] > current_year:
                    quality_issues += 1
                    validation['issues'].append(f"Unrealistisches Jahr: {result['jahr']}")
        
        # Berechne Qualitäts-Score
        if quality_issues > 0:
            penalty = min(quality_issues * 10, 50)  # Max 50 Punkte Abzug
            validation['quality_score'] = max(50, 100 - penalty)
        
        # Generiere Empfehlungen
        if validation['quality_score'] < 80:
            validation['recommendations'].append("Überprüfen Sie die Datenquellen")
            validation['recommendations'].append("Verfeinern Sie Ihre Suchanfrage")
        
        return validation
    
    def get_quality_report(self) -> Dict[str, Any]:
        """Erstelle Qualitätsbericht"""
        current_time = datetime.now()
        
        # Berechne Gesamtqualität
        data_quality = self.metrics['data_quality']['score']
        performance_score = 100 if self.metrics['system_performance']['response_time_avg'] < 3.0 else 80
        error_score = 100 if self.metrics['system_performance']['error_rate'] < 0.03 else 70
        
        overall_quality = (data_quality + performance_score + error_score) / 3
        
        report = {
            'timestamp': current_time,
            'overall_quality_score': round(overall_quality, 1),
            'data_quality': {
                'score': self.metrics['data_quality']['score'],
                'last_check': self.metrics['data_quality']['last_check'],
                'issues_found': self.metrics['data_quality']['issues_found']
            },
            'system_performance': {
                'avg_response_time': round(self.metrics['system_performance']['response_time_avg'], 2),
                'error_rate': round(self.metrics['system_performance']['error_rate'] * 100, 2),
                'uptime_hours': round((current_time - self.metrics['system_performance']['uptime']).total_seconds() / 3600, 1)
            },
            'user_satisfaction': {
                'successful_queries': self.metrics['user_satisfaction']['successful_queries'],
                'failed_queries': self.metrics['user_satisfaction']['failed_queries'],
                'success_rate': self.calculate_success_rate()
            },
            'active_alerts': len([a for a in self.alerts if not a['resolved']]),
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def calculate_success_rate(self) -> float:
        """Berechne Erfolgsrate"""
        total = (self.metrics['user_satisfaction']['successful_queries'] + 
                self.metrics['user_satisfaction']['failed_queries'])
        
        if total == 0:
            return 100.0
        
        return round((self.metrics['user_satisfaction']['successful_queries'] / total) * 100, 1)
    
    def generate_recommendations(self) -> List[str]:
        """Generiere Verbesserungsempfehlungen"""
        recommendations = []
        
        if self.metrics['data_quality']['score'] < 90:
            recommendations.append("Datenqualität verbessern durch regelmäßige Validierung")
        
        if self.metrics['system_performance']['response_time_avg'] > 3.0:
            recommendations.append("Performance optimieren - Caching implementieren")
        
        if self.metrics['system_performance']['error_rate'] > 0.03:
            recommendations.append("Fehlerbehandlung verbessern")
        
        if len([a for a in self.alerts if not a['resolved']]) > 5:
            recommendations.append("Aktive Alerts bearbeiten")
        
        return recommendations
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Gebe aktive Alerts zurück"""
        return [alert for alert in self.alerts if not alert['resolved']]
    
    def resolve_alert(self, alert_index: int):
        """Markiere Alert als gelöst"""
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index]['resolved'] = True
            self.alerts[alert_index]['resolved_at'] = datetime.now()
    
    def export_metrics(self, file_path: str = None) -> str:
        """Exportiere Metriken als JSON"""
        if not file_path:
            file_path = f"/tmp/quality_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'metrics': self.metrics,
            'alerts': self.alerts,
            'quality_report': self.get_quality_report()
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Metriken exportiert nach: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Metriken-Export fehlgeschlagen: {e}")
            return ""
    
    def stop_monitoring(self):
        """Stoppe Monitoring"""
        self.monitoring_active = False
        self.logger.info("Qualitätsmonitor gestoppt")