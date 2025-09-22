#!/usr/bin/env python3
"""
Datenmanager für das Gmunden Transparenz-System
Unterstützt alle Datenquellen: DB, Web, PDF, Bilder, etc.
"""

import os
import json
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import pymongo
from datetime import datetime
import requests
import fitz  # PyMuPDF für PDF-Verarbeitung
from PIL import Image
import pytesseract
import yaml
import logging

class DataManager:
    """
    Zentraler Datenmanager für alle Datenquellen
    """
    
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.init_database()
        self.setup_data_sources()
    
    def setup_logging(self):
        """Setup Logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """Lade Konfiguration"""
        try:
            config_path = Path(__file__).parent.parent / "config" / "system_settings.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Konfiguration konnte nicht geladen werden: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self):
        """Standard-Konfiguration"""
        return {
            'database': {
                'mongodb': {
                    'host': 'localhost',
                    'port': 27017,
                    'database': 'gmunden_transparenz'
                }
            },
            'data_integration': {
                'sources': {
                    'files': {
                        'supported_formats': ['pdf', 'docx', 'xlsx', 'csv', 'txt', 'json'],
                        'max_file_size': '100MB'
                    }
                }
            }
        }
    
    def init_database(self):
        """Initialisiere Datenbankverbindung"""
        try:
            db_config = self.config.get('database', {}).get('mongodb', {})
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 27017)
            database = db_config.get('database', 'gmunden_transparenz')
            
            # Für All-Hands.dev: Fallback auf Mock-Datenbank wenn MongoDB nicht verfügbar
            try:
                self.mongo_client = pymongo.MongoClient(host, port, serverSelectionTimeoutMS=2000)
                self.mongo_client.server_info()  # Test connection
                self.db = self.mongo_client[database]
                self.use_mongodb = True
                self.logger.info("MongoDB-Verbindung erfolgreich")
            except Exception:
                self.logger.warning("MongoDB nicht verfügbar, verwende Mock-Datenbank")
                self.use_mongodb = False
                self.mock_db = self.create_mock_database()
                
        except Exception as e:
            self.logger.error(f"Datenbankinitialisierung fehlgeschlagen: {e}")
            self.use_mongodb = False
            self.mock_db = self.create_mock_database()
    
    def create_mock_database(self):
        """Erstelle Mock-Datenbank für Entwicklung/Demo"""
        return {
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
                    'jahr': 2022,
                    'kategorie': 'kultur',
                    'beschreibung': 'Stadtfest Organisation',
                    'betrag': 15000.00,
                    'datum': '2022-08-20',
                    'quelle': 'veranstaltungsbudget'
                }
            ],
            'dokumente': [
                {
                    'filename': 'gemeinderat_2023_06.pdf',
                    'jahr': 2023,
                    'typ': 'protokoll',
                    'pdf_title': 'Gemeinderatssitzung Juni 2023',
                    'ocr_text': 'Protokoll der ordentlichen Gemeinderatssitzung vom 15. Juni 2023...',
                    'filesize': 2048576,
                    'tags': ['protokoll', 'gemeinderat', '2023']
                }
            ],
            'protokolle': [
                {
                    'datum': '2023-06-15',
                    'typ': 'gemeinderat',
                    'titel': 'Ordentliche Gemeinderatssitzung',
                    'beschluesse': [
                        {
                            'nummer': '2023-06-01',
                            'titel': 'Budget-Nachtragsvoranschlag',
                            'ergebnis': 'einstimmig angenommen'
                        }
                    ],
                    'anwesende': ['Bürgermeister', 'Vizebürgermeister']
                }
            ]
        }
    
    def setup_data_sources(self):
        """Setup für verschiedene Datenquellen"""
        self.data_sources = {
            'mongodb': self.use_mongodb,
            'files': True,
            'web_scraping': True,
            'api_endpoints': True,
            'ocr_processing': True
        }
    
    def search(self, nlp_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Hauptsuchfunktion basierend auf NLP-Analyse
        
        Args:
            nlp_result: Ergebnis der NLP-Verarbeitung
            
        Returns:
            Liste der Suchergebnisse
        """
        try:
            query_type = nlp_result.get('query_type', 'general')
            entities = nlp_result.get('entities', {})
            filters = nlp_result.get('filters', {})
            search_terms = nlp_result.get('search_terms', [])
            
            results = []
            
            # Finanzsuche
            if query_type == 'financial' or entities.get('amounts'):
                financial_results = self.search_financial_data(entities, filters, search_terms)
                results.extend(financial_results)
            
            # Dokumentensuche
            if query_type == 'documents' or 'dokument' in nlp_result.get('original_query', '').lower():
                document_results = self.search_documents(entities, filters, search_terms)
                results.extend(document_results)
            
            # Allgemeine Suche
            if query_type == 'general' or not results:
                general_results = self.search_general(entities, filters, search_terms)
                results.extend(general_results)
            
            # Entferne Duplikate
            results = self.remove_duplicates(results)
            
            # Sortiere Ergebnisse
            results = self.sort_results(results, filters)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Suchfehler: {e}")
            return []
    
    def search_financial_data(self, entities: Dict, filters: Dict, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Suche in Finanzdaten"""
        if self.use_mongodb:
            collection = self.db['finanzen']
            query = {}
            
            # Jahr-Filter
            if entities.get('years'):
                if len(entities['years']) == 1:
                    query['jahr'] = entities['years'][0]
                else:
                    query['jahr'] = {'$in': entities['years']}
            
            # Kategorie-Filter
            if entities.get('categories'):
                query['kategorie'] = {'$in': entities['categories']}
            
            # Betrag-Filter
            if filters.get('amount_min') or filters.get('amount_max'):
                betrag_filter = {}
                if filters.get('amount_min'):
                    betrag_filter['$gte'] = filters['amount_min']
                if filters.get('amount_max'):
                    betrag_filter['$lte'] = filters['amount_max']
                query['betrag'] = betrag_filter
            
            # Text-Suche
            if search_terms:
                query['$text'] = {'$search': ' '.join(search_terms)}
            
            results = list(collection.find(query))
            
        else:
            # Mock-Datenbank Suche
            results = self.mock_db['finanzen'].copy()
            
            # Jahr-Filter
            if entities.get('years'):
                results = [r for r in results if r.get('jahr') in entities['years']]
            
            # Kategorie-Filter
            if entities.get('categories'):
                results = [r for r in results if r.get('kategorie') in entities['categories']]
            
            # Betrag-Filter
            if filters.get('amount_min'):
                results = [r for r in results if r.get('betrag', 0) >= filters['amount_min']]
            if filters.get('amount_max'):
                results = [r for r in results if r.get('betrag', 0) <= filters['amount_max']]
            
            # Text-Suche
            if search_terms:
                filtered_results = []
                for result in results:
                    text_content = ' '.join(str(v) for v in result.values()).lower()
                    if any(term.lower() in text_content for term in search_terms):
                        filtered_results.append(result)
                results = filtered_results
        
        return results
    
    def search_documents(self, entities: Dict, filters: Dict, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Suche in Dokumenten"""
        if self.use_mongodb:
            collection = self.db['dokumente']
            query = {}
            
            if entities.get('years'):
                if len(entities['years']) == 1:
                    query['jahr'] = entities['years'][0]
                else:
                    query['jahr'] = {'$in': entities['years']}
            
            if search_terms:
                query['$text'] = {'$search': ' '.join(search_terms)}
            
            results = list(collection.find(query))
        else:
            results = self.mock_db['dokumente'].copy()
            
            if entities.get('years'):
                results = [r for r in results if r.get('jahr') in entities['years']]
            
            if search_terms:
                filtered_results = []
                for result in results:
                    searchable_text = f"{result.get('filename', '')} {result.get('ocr_text', '')} {result.get('pdf_title', '')}".lower()
                    if any(term.lower() in searchable_text for term in search_terms):
                        filtered_results.append(result)
                results = filtered_results
        
        return results
    
    def search_general(self, entities: Dict, filters: Dict, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Allgemeine Suche über alle Collections"""
        results = []
        
        # Suche in allen verfügbaren Collections
        financial_results = self.search_financial_data(entities, filters, search_terms)
        document_results = self.search_documents(entities, filters, search_terms)
        
        results.extend(financial_results)
        results.extend(document_results)
        
        return results
    
    def import_data_from_file(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """
        Importiere Daten aus Datei
        
        Args:
            file_path: Pfad zur Datei
            file_type: Typ der Datei (optional, wird automatisch erkannt)
            
        Returns:
            Import-Ergebnis
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {'success': False, 'error': 'Datei nicht gefunden'}
            
            # Automatische Typ-Erkennung
            if not file_type:
                file_type = file_path.suffix.lower()
            
            if file_type in ['.pdf']:
                return self.import_pdf(file_path)
            elif file_type in ['.csv']:
                return self.import_csv(file_path)
            elif file_type in ['.xlsx', '.xls']:
                return self.import_excel(file_path)
            elif file_type in ['.json']:
                return self.import_json(file_path)
            elif file_type in ['.jpg', '.jpeg', '.png', '.tiff']:
                return self.import_image_with_ocr(file_path)
            else:
                return {'success': False, 'error': f'Dateityp {file_type} nicht unterstützt'}
                
        except Exception as e:
            self.logger.error(f"Import-Fehler: {e}")
            return {'success': False, 'error': str(e)}
    
    def import_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Importiere PDF mit OCR"""
        try:
            doc = fitz.open(file_path)
            text_content = ""
            
            for page in doc:
                text_content += page.get_text()
            
            doc.close()
            
            # Extrahiere Metadaten
            metadata = {
                'filename': file_path.name,
                'filesize': file_path.stat().st_size,
                'import_date': datetime.now(),
                'ocr_text': text_content,
                'typ': 'pdf_dokument'
            }
            
            # Versuche Jahr zu extrahieren
            import re
            year_match = re.search(r'\b(20\d{2})\b', text_content)
            if year_match:
                metadata['jahr'] = int(year_match.group(1))
            
            # Speichere in Datenbank
            if self.use_mongodb:
                self.db['dokumente'].insert_one(metadata)
            else:
                self.mock_db['dokumente'].append(metadata)
            
            return {
                'success': True,
                'imported_records': 1,
                'metadata': metadata
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def import_csv(self, file_path: Path) -> Dict[str, Any]:
        """Importiere CSV-Datei"""
        try:
            df = pd.read_csv(file_path)
            records = df.to_dict('records')
            
            # Bestimme Collection basierend auf Spalten
            columns = df.columns.tolist()
            if 'betrag' in columns or 'kosten' in columns:
                collection_name = 'finanzen'
            else:
                collection_name = 'allgemeine_daten'
            
            # Speichere in Datenbank
            if self.use_mongodb:
                self.db[collection_name].insert_many(records)
            else:
                if collection_name not in self.mock_db:
                    self.mock_db[collection_name] = []
                self.mock_db[collection_name].extend(records)
            
            return {
                'success': True,
                'imported_records': len(records),
                'collection': collection_name
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def import_excel(self, file_path: Path) -> Dict[str, Any]:
        """Importiere Excel-Datei"""
        try:
            df = pd.read_excel(file_path)
            return self.import_csv(file_path)  # Verwende CSV-Logik
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def import_json(self, file_path: Path) -> Dict[str, Any]:
        """Importiere JSON-Datei"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                records = data
            else:
                records = [data]
            
            # Speichere in allgemeine Daten
            if self.use_mongodb:
                self.db['allgemeine_daten'].insert_many(records)
            else:
                if 'allgemeine_daten' not in self.mock_db:
                    self.mock_db['allgemeine_daten'] = []
                self.mock_db['allgemeine_daten'].extend(records)
            
            return {
                'success': True,
                'imported_records': len(records)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def import_image_with_ocr(self, file_path: Path) -> Dict[str, Any]:
        """Importiere Bild mit OCR-Texterkennung"""
        try:
            # OCR mit Tesseract
            image = Image.open(file_path)
            ocr_text = pytesseract.image_to_string(image, lang='deu')
            
            metadata = {
                'filename': file_path.name,
                'filesize': file_path.stat().st_size,
                'import_date': datetime.now(),
                'ocr_text': ocr_text,
                'typ': 'bild_mit_ocr'
            }
            
            # Speichere in Datenbank
            if self.use_mongodb:
                self.db['dokumente'].insert_one(metadata)
            else:
                self.mock_db['dokumente'].append(metadata)
            
            return {
                'success': True,
                'imported_records': 1,
                'ocr_text_length': len(ocr_text)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def import_from_web_api(self, api_url: str, api_key: str = None) -> Dict[str, Any]:
        """Importiere Daten von Web-API"""
        try:
            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, list):
                records = data
            else:
                records = [data]
            
            # Speichere in API-Daten
            if self.use_mongodb:
                self.db['api_daten'].insert_many(records)
            else:
                if 'api_daten' not in self.mock_db:
                    self.mock_db['api_daten'] = []
                self.mock_db['api_daten'].extend(records)
            
            return {
                'success': True,
                'imported_records': len(records),
                'source': api_url
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_data_sources_status(self) -> Dict[str, bool]:
        """Gebe Status aller Datenquellen zurück"""
        return self.data_sources.copy()
    
    def remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Entferne Duplikate aus Ergebnissen"""
        seen = set()
        unique_results = []
        
        for result in results:
            # Erstelle Hash basierend auf wichtigen Feldern
            key_fields = ['beschreibung', 'betrag', 'datum', 'filename']
            key_values = []
            
            for field in key_fields:
                if field in result:
                    key_values.append(str(result[field]))
            
            result_hash = hash(tuple(key_values))
            
            if result_hash not in seen:
                seen.add(result_hash)
                unique_results.append(result)
        
        return unique_results
    
    def sort_results(self, results: List[Dict[str, Any]], filters: Dict) -> List[Dict[str, Any]]:
        """Sortiere Ergebnisse"""
        if not results:
            return results
        
        sort_order = filters.get('sort', 'desc')
        
        # Sortiere nach Betrag wenn vorhanden
        if any('betrag' in result for result in results):
            results.sort(
                key=lambda x: x.get('betrag', 0),
                reverse=(sort_order == 'desc')
            )
        # Sonst nach Datum
        elif any('datum' in result for result in results):
            results.sort(
                key=lambda x: x.get('datum', ''),
                reverse=(sort_order == 'desc')
            )
        
        return results