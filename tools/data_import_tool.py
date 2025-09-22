#!/usr/bin/env python3
"""
Universelles Datenimport-Tool für das Gmunden Transparenz-System
Unterstützt alle Datenquellen: Dateien, Web-APIs, Datenbanken
"""

import argparse
import sys
from pathlib import Path
import json
import yaml
from typing import Dict, List, Any
import logging

# Füge Projekt-Root zum Python-Path hinzu
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from data.data_manager import DataManager
from ai.fact_checker import FactChecker
from monitoring.quality_monitor import QualityMonitor

class UniversalDataImporter:
    """
    Universelles Tool für Datenimport aus verschiedenen Quellen
    """
    
    def __init__(self):
        self.setup_logging()
        self.data_manager = DataManager()
        self.fact_checker = FactChecker()
        self.quality_monitor = QualityMonitor()
    
    def setup_logging(self):
        """Setup Logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def import_from_file(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """Importiere Daten aus Datei"""
        self.logger.info(f"Importiere Datei: {file_path}")
        
        result = self.data_manager.import_data_from_file(file_path, file_type)
        
        if result['success']:
            self.logger.info(f"Import erfolgreich: {result.get('imported_records', 0)} Datensätze")
        else:
            self.logger.error(f"Import fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
        
        return result
    
    def import_from_web_api(self, api_url: str, api_key: str = None) -> Dict[str, Any]:
        """Importiere Daten von Web-API"""
        self.logger.info(f"Importiere von API: {api_url}")
        
        result = self.data_manager.import_from_web_api(api_url, api_key)
        
        if result['success']:
            self.logger.info(f"API-Import erfolgreich: {result.get('imported_records', 0)} Datensätze")
        else:
            self.logger.error(f"API-Import fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
        
        return result
    
    def import_directory(self, directory_path: str, recursive: bool = False) -> Dict[str, Any]:
        """Importiere alle Dateien aus einem Verzeichnis"""
        directory = Path(directory_path)
        
        if not directory.exists():
            return {'success': False, 'error': 'Verzeichnis nicht gefunden'}
        
        results = {
            'total_files': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'details': []
        }
        
        # Unterstützte Dateierweiterungen
        supported_extensions = ['.pdf', '.csv', '.xlsx', '.xls', '.json', '.txt', '.jpg', '.jpeg', '.png']
        
        # Finde alle Dateien
        if recursive:
            files = []
            for ext in supported_extensions:
                files.extend(directory.rglob(f'*{ext}'))
        else:
            files = []
            for ext in supported_extensions:
                files.extend(directory.glob(f'*{ext}'))
        
        results['total_files'] = len(files)
        self.logger.info(f"Gefunden: {len(files)} Dateien zum Import")
        
        for file_path in files:
            self.logger.info(f"Importiere: {file_path.name}")
            
            import_result = self.import_from_file(str(file_path))
            
            if import_result['success']:
                results['successful_imports'] += 1
            else:
                results['failed_imports'] += 1
            
            results['details'].append({
                'file': str(file_path),
                'success': import_result['success'],
                'records': import_result.get('imported_records', 0),
                'error': import_result.get('error')
            })
        
        return results
    
    def import_from_config(self, config_file: str) -> Dict[str, Any]:
        """Importiere basierend auf Konfigurationsdatei"""
        config_path = Path(config_file)
        
        if not config_path.exists():
            return {'success': False, 'error': 'Konfigurationsdatei nicht gefunden'}
        
        try:
            if config_path.suffix.lower() == '.json':
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:  # YAML
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            
            results = {
                'total_sources': 0,
                'successful_imports': 0,
                'failed_imports': 0,
                'details': []
            }
            
            # Datei-Quellen
            if 'files' in config:
                for file_config in config['files']:
                    results['total_sources'] += 1
                    
                    file_path = file_config.get('path')
                    file_type = file_config.get('type')
                    
                    import_result = self.import_from_file(file_path, file_type)
                    
                    if import_result['success']:
                        results['successful_imports'] += 1
                    else:
                        results['failed_imports'] += 1
                    
                    results['details'].append({
                        'source': file_path,
                        'type': 'file',
                        'success': import_result['success'],
                        'records': import_result.get('imported_records', 0)
                    })
            
            # API-Quellen
            if 'apis' in config:
                for api_config in config['apis']:
                    results['total_sources'] += 1
                    
                    api_url = api_config.get('url')
                    api_key = api_config.get('key')
                    
                    import_result = self.import_from_web_api(api_url, api_key)
                    
                    if import_result['success']:
                        results['successful_imports'] += 1
                    else:
                        results['failed_imports'] += 1
                    
                    results['details'].append({
                        'source': api_url,
                        'type': 'api',
                        'success': import_result['success'],
                        'records': import_result.get('imported_records', 0)
                    })
            
            return results
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_imported_data(self) -> Dict[str, Any]:
        """Validiere alle importierten Daten"""
        self.logger.info("Starte Datenvalidierung...")
        
        # Hole alle Daten (vereinfacht für Demo)
        all_data = []
        
        # In echter Implementierung würden hier alle Collections abgefragt
        if hasattr(self.data_manager, 'mock_db'):
            for collection_name, data in self.data_manager.mock_db.items():
                all_data.extend(data)
        
        # Führe Fact-Check durch
        validation_result = self.fact_checker.verify_results(all_data)
        
        self.logger.info(f"Validierung abgeschlossen: {validation_result['score']}% Qualität")
        
        return validation_result
    
    def generate_import_report(self, import_results: Dict[str, Any]) -> str:
        """Generiere Import-Bericht"""
        report_lines = []
        
        report_lines.append("=" * 60)
        report_lines.append("DATENIMPORT-BERICHT")
        report_lines.append("=" * 60)
        report_lines.append(f"Zeitpunkt: {import_results.get('timestamp', 'N/A')}")
        report_lines.append("")
        
        if 'total_files' in import_results:
            # Verzeichnis-Import
            report_lines.append(f"Gesamte Dateien: {import_results['total_files']}")
            report_lines.append(f"Erfolgreich: {import_results['successful_imports']}")
            report_lines.append(f"Fehlgeschlagen: {import_results['failed_imports']}")
            
        elif 'total_sources' in import_results:
            # Konfiguration-basierter Import
            report_lines.append(f"Gesamte Quellen: {import_results['total_sources']}")
            report_lines.append(f"Erfolgreich: {import_results['successful_imports']}")
            report_lines.append(f"Fehlgeschlagen: {import_results['failed_imports']}")
        
        else:
            # Einzelner Import
            report_lines.append(f"Import-Status: {'Erfolgreich' if import_results.get('success') else 'Fehlgeschlagen'}")
            if import_results.get('imported_records'):
                report_lines.append(f"Importierte Datensätze: {import_results['imported_records']}")
        
        report_lines.append("")
        report_lines.append("DETAILS:")
        report_lines.append("-" * 40)
        
        if 'details' in import_results:
            for detail in import_results['details']:
                status = "✅" if detail['success'] else "❌"
                report_lines.append(f"{status} {detail.get('file', detail.get('source', 'N/A'))}")
                if detail.get('records'):
                    report_lines.append(f"    Datensätze: {detail['records']}")
                if detail.get('error'):
                    report_lines.append(f"    Fehler: {detail['error']}")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)

def main():
    """Hauptfunktion für CLI-Interface"""
    parser = argparse.ArgumentParser(
        description="Universelles Datenimport-Tool für Gmunden Transparenz-System"
    )
    
    parser.add_argument(
        'command',
        choices=['file', 'directory', 'api', 'config', 'validate'],
        help='Import-Kommando'
    )
    
    parser.add_argument(
        'source',
        nargs='?',
        help='Quelle (Datei, Verzeichnis, URL oder Konfigurationsdatei)'
    )
    
    parser.add_argument(
        '--type',
        help='Dateityp (optional, wird automatisch erkannt)'
    )
    
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Rekursiv durch Unterverzeichnisse (nur bei directory)'
    )
    
    parser.add_argument(
        '--api-key',
        help='API-Schlüssel für Web-API-Zugriff'
    )
    
    parser.add_argument(
        '--output',
        help='Ausgabedatei für Bericht'
    )
    
    args = parser.parse_args()
    
    # Initialisiere Importer
    importer = UniversalDataImporter()
    
    # Führe entsprechendes Kommando aus
    if args.command == 'file':
        if not args.source:
            print("Fehler: Dateipfad erforderlich")
            sys.exit(1)
        
        result = importer.import_from_file(args.source, args.type)
        
    elif args.command == 'directory':
        if not args.source:
            print("Fehler: Verzeichnispfad erforderlich")
            sys.exit(1)
        
        result = importer.import_directory(args.source, args.recursive)
        
    elif args.command == 'api':
        if not args.source:
            print("Fehler: API-URL erforderlich")
            sys.exit(1)
        
        result = importer.import_from_web_api(args.source, args.api_key)
        
    elif args.command == 'config':
        if not args.source:
            print("Fehler: Konfigurationsdatei erforderlich")
            sys.exit(1)
        
        result = importer.import_from_config(args.source)
        
    elif args.command == 'validate':
        result = importer.validate_imported_data()
    
    # Generiere und zeige Bericht
    if args.command != 'validate':
        from datetime import datetime
        result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = importer.generate_import_report(result)
    print(report)
    
    # Speichere Bericht falls gewünscht
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nBericht gespeichert: {args.output}")

if __name__ == "__main__":
    main()