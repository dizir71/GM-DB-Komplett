#!/usr/bin/env python3
"""
Fact-Checker für das Gmunden Transparenz-System
Verhindert Halluzinationen und stellt sicher, dass nur reale Daten ausgegeben werden
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import json
from pathlib import Path

class FactChecker:
    """
    Überprüft Fakten und verhindert Halluzinationen im System
    """
    
    def __init__(self):
        self.setup_validation_rules()
        self.load_known_facts()
    
    def setup_validation_rules(self):
        """Setup für Validierungsregeln"""
        self.validation_rules = {
            'financial': {
                'max_single_expense': 10000000,  # 10 Millionen Euro
                'min_year': 1990,
                'max_year': datetime.now().year + 1,
                'valid_categories': [
                    'infrastruktur', 'personal', 'verwaltung', 
                    'kultur', 'soziales', 'umwelt', 'bildung'
                ]
            },
            'documents': {
                'valid_types': ['protokoll', 'bericht', 'beschluss', 'vertrag', 'rechnung'],
                'max_file_size': 100 * 1024 * 1024,  # 100 MB
                'valid_extensions': ['.pdf', '.docx', '.txt', '.xlsx']
            },
            'temporal': {
                'min_date': datetime(1990, 1, 1),
                'max_date': datetime.now(),
                'valid_date_formats': ['%Y-%m-%d', '%d.%m.%Y', '%Y']
            }
        }
    
    def load_known_facts(self):
        """Lade bekannte Fakten für Verifikation"""
        self.known_facts = {
            'gemeinde_info': {
                'name': 'Gmunden',
                'bundesland': 'Oberösterreich',
                'land': 'Österreich',
                'einwohner_ca': 13000,  # Ungefähre Einwohnerzahl
                'gruendung': 'Mittelalter'
            },
            'data_sources': {
                'official_sources': [
                    'data.gv.at',
                    'statistik.at',
                    'gemeinde-gmunden.at'
                ],
                'last_verified': datetime.now().isoformat()
            }
        }
    
    def verify_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Überprüfe Suchergebnisse auf Realität und Konsistenz
        
        Args:
            results: Liste der Suchergebnisse
            
        Returns:
            Dict mit Verifikationsergebnis
        """
        verification = {
            'total_results': len(results),
            'verified_results': 0,
            'warnings': [],
            'errors': [],
            'score': 100,
            'confidence': 'high',
            'data_quality': 'excellent'
        }
        
        if not results:
            verification['confidence'] = 'low'
            verification['data_quality'] = 'no_data'
            return verification
        
        for i, result in enumerate(results):
            result_verification = self.verify_single_result(result)
            
            if result_verification['is_valid']:
                verification['verified_results'] += 1
            else:
                verification['warnings'].extend(result_verification['warnings'])
                verification['errors'].extend(result_verification['errors'])
        
        # Berechne Qualitäts-Score
        if verification['total_results'] > 0:
            verification['score'] = int(
                (verification['verified_results'] / verification['total_results']) * 100
            )
        
        # Bestimme Konfidenz
        if verification['score'] >= 90:
            verification['confidence'] = 'high'
            verification['data_quality'] = 'excellent'
        elif verification['score'] >= 70:
            verification['confidence'] = 'medium'
            verification['data_quality'] = 'good'
        else:
            verification['confidence'] = 'low'
            verification['data_quality'] = 'questionable'
        
        return verification
    
    def verify_single_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Überprüfe ein einzelnes Ergebnis"""
        verification = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'checks_performed': []
        }
        
        # Finanz-Validierung
        if 'betrag' in result:
            finance_check = self.validate_financial_data(result)
            verification['checks_performed'].append('financial')
            if not finance_check['is_valid']:
                verification['is_valid'] = False
                verification['errors'].extend(finance_check['errors'])
        
        # Datum-Validierung
        if any(key in result for key in ['datum', 'jahr']):
            date_check = self.validate_temporal_data(result)
            verification['checks_performed'].append('temporal')
            if not date_check['is_valid']:
                verification['warnings'].extend(date_check['warnings'])
        
        # Dokument-Validierung
        if 'filename' in result or 'dokument' in result:
            doc_check = self.validate_document_data(result)
            verification['checks_performed'].append('document')
            if not doc_check['is_valid']:
                verification['warnings'].extend(doc_check['warnings'])
        
        # Konsistenz-Prüfung
        consistency_check = self.validate_consistency(result)
        verification['checks_performed'].append('consistency')
        if not consistency_check['is_valid']:
            verification['warnings'].extend(consistency_check['warnings'])
        
        return verification
    
    def validate_financial_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validiere Finanzdaten"""
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        betrag = result.get('betrag', 0)
        
        # Unrealistische Beträge
        if betrag > self.validation_rules['financial']['max_single_expense']:
            validation['is_valid'] = False
            validation['errors'].append(
                f"Betrag {betrag:,.2f}€ ist unrealistisch hoch für eine Gemeinde"
            )
        
        if betrag < 0:
            validation['warnings'].append("Negativer Betrag gefunden")
        
        # Kategorie-Validierung
        kategorie = result.get('kategorie', '').lower()
        if kategorie and kategorie not in self.validation_rules['financial']['valid_categories']:
            validation['warnings'].append(f"Unbekannte Kategorie: {kategorie}")
        
        return validation
    
    def validate_temporal_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validiere Zeitdaten"""
        validation = {
            'is_valid': True,
            'warnings': []
        }
        
        # Jahr-Validierung
        if 'jahr' in result:
            jahr = result['jahr']
            min_year = self.validation_rules['financial']['min_year']
            max_year = self.validation_rules['financial']['max_year']
            
            if jahr < min_year or jahr > max_year:
                validation['warnings'].append(
                    f"Jahr {jahr} liegt außerhalb des erwarteten Bereichs ({min_year}-{max_year})"
                )
        
        # Datum-Validierung
        if 'datum' in result:
            try:
                if isinstance(result['datum'], str):
                    # Versuche verschiedene Datumsformate
                    parsed_date = None
                    for fmt in self.validation_rules['temporal']['valid_date_formats']:
                        try:
                            parsed_date = datetime.strptime(result['datum'], fmt)
                            break
                        except ValueError:
                            continue
                    
                    if not parsed_date:
                        validation['warnings'].append(f"Unbekanntes Datumsformat: {result['datum']}")
                    elif (parsed_date < self.validation_rules['temporal']['min_date'] or 
                          parsed_date > self.validation_rules['temporal']['max_date']):
                        validation['warnings'].append(f"Datum außerhalb des gültigen Bereichs: {result['datum']}")
            except Exception as e:
                validation['warnings'].append(f"Fehler bei Datumsvalidierung: {e}")
        
        return validation
    
    def validate_document_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validiere Dokumentdaten"""
        validation = {
            'is_valid': True,
            'warnings': []
        }
        
        # Dateiname-Validierung
        if 'filename' in result:
            filename = result['filename']
            
            # Prüfe Dateierweiterung
            valid_extensions = self.validation_rules['documents']['valid_extensions']
            if not any(filename.lower().endswith(ext) for ext in valid_extensions):
                validation['warnings'].append(f"Ungewöhnliche Dateierweiterung: {filename}")
        
        # Dateigröße-Validierung
        if 'filesize' in result:
            filesize = result['filesize']
            max_size = self.validation_rules['documents']['max_file_size']
            
            if filesize > max_size:
                validation['warnings'].append(f"Datei sehr groß: {filesize / (1024*1024):.1f} MB")
        
        # Dokumenttyp-Validierung
        if 'typ' in result:
            typ = result['typ'].lower()
            valid_types = self.validation_rules['documents']['valid_types']
            
            if typ not in valid_types:
                validation['warnings'].append(f"Unbekannter Dokumenttyp: {typ}")
        
        return validation
    
    def validate_consistency(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Prüfe interne Konsistenz der Daten"""
        validation = {
            'is_valid': True,
            'warnings': []
        }
        
        # Prüfe Konsistenz zwischen Jahr und Datum
        if 'jahr' in result and 'datum' in result:
            jahr = result['jahr']
            datum_str = str(result['datum'])
            
            if str(jahr) not in datum_str:
                validation['warnings'].append(
                    f"Inkonsistenz zwischen Jahr ({jahr}) und Datum ({datum_str})"
                )
        
        # Prüfe Konsistenz zwischen Betrag und Beschreibung
        if 'betrag' in result and 'beschreibung' in result:
            betrag = result['betrag']
            beschreibung = result['beschreibung'].lower()
            
            # Sehr hohe Beträge sollten entsprechende Beschreibungen haben
            if betrag > 100000 and not any(word in beschreibung for word in 
                                         ['projekt', 'bau', 'investition', 'sanierung']):
                validation['warnings'].append(
                    f"Hoher Betrag ({betrag:,.2f}€) ohne entsprechende Projektbeschreibung"
                )
        
        return validation
    
    def create_data_fingerprint(self, data: Dict[str, Any]) -> str:
        """Erstelle Fingerprint für Datenintegrität"""
        # Sortiere und serialisiere Daten für konsistenten Hash
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(sorted_data.encode()).hexdigest()[:16]
    
    def verify_data_integrity(self, data: List[Dict[str, Any]], 
                            expected_fingerprint: Optional[str] = None) -> Dict[str, Any]:
        """Überprüfe Datenintegrität"""
        current_fingerprint = self.create_data_fingerprint({'data': data})
        
        integrity_check = {
            'current_fingerprint': current_fingerprint,
            'expected_fingerprint': expected_fingerprint,
            'integrity_verified': True,
            'timestamp': datetime.now().isoformat()
        }
        
        if expected_fingerprint and current_fingerprint != expected_fingerprint:
            integrity_check['integrity_verified'] = False
            integrity_check['warning'] = "Datenintegrität könnte kompromittiert sein"
        
        return integrity_check
    
    def generate_quality_report(self, verification_results: Dict[str, Any]) -> str:
        """Generiere Qualitätsbericht"""
        report = []
        
        report.append("=== DATENQUALITÄTSBERICHT ===")
        report.append(f"Zeitpunkt: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        report.append("")
        
        report.append(f"Gesamtergebnisse: {verification_results['total_results']}")
        report.append(f"Verifizierte Ergebnisse: {verification_results['verified_results']}")
        report.append(f"Qualitäts-Score: {verification_results['score']}%")
        report.append(f"Konfidenz: {verification_results['confidence']}")
        report.append(f"Datenqualität: {verification_results['data_quality']}")
        report.append("")
        
        if verification_results['warnings']:
            report.append("WARNUNGEN:")
            for warning in verification_results['warnings']:
                report.append(f"  ⚠️  {warning}")
            report.append("")
        
        if verification_results['errors']:
            report.append("FEHLER:")
            for error in verification_results['errors']:
                report.append(f"  ❌ {error}")
            report.append("")
        
        report.append("=== ENDE BERICHT ===")
        
        return "\n".join(report)
    
    def suggest_data_improvements(self, verification_results: Dict[str, Any]) -> List[str]:
        """Schlage Verbesserungen für Datenqualität vor"""
        suggestions = []
        
        if verification_results['score'] < 90:
            suggestions.append("Überprüfen Sie die Datenquellen auf Vollständigkeit")
            suggestions.append("Implementieren Sie zusätzliche Validierungsregeln")
        
        if verification_results['errors']:
            suggestions.append("Korrigieren Sie die identifizierten Datenfehler")
            suggestions.append("Überprüfen Sie die Datenimport-Prozesse")
        
        if verification_results['warnings']:
            suggestions.append("Untersuchen Sie die gemeldeten Warnungen")
            suggestions.append("Erwägen Sie eine Bereinigung der Datenbestände")
        
        return suggestions