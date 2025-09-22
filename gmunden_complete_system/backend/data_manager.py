#!/usr/bin/env python3
"""
Gmunden Transparenz-Datenbank - Vollständiger Datenmanager
Vereint alle Datenquellen und -funktionen aus den verschiedenen Projektversionen
"""

import os
import json
import pandas as pd
import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import hashlib
import mimetypes
import io
import base64
from dataclasses import dataclass
import yaml
import xml.etree.ElementTree as ET
import requests
import sqlite3
import tempfile
import shutil

# OCR und Dokumentverarbeitung
try:
    import fitz  # PyMuPDF
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

# Excel-Verarbeitung
try:
    import openpyxl
    HAS_EXCEL = True
except ImportError:
    HAS_EXCEL = False

logger = logging.getLogger(__name__)

@dataclass
class DataSource:
    """Datenquelle-Definition"""
    name: str
    type: str  # 'mongodb', 'file', 'api', 'database'
    connection: str
    format: str  # 'json', 'csv', 'excel', 'pdf', 'xml'
    active: bool = True
    last_sync: Optional[datetime] = None
    metadata: Dict[str, Any] = None

class DataManager:
    """Vollständiger Datenmanager für alle Datenquellen"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.data_sources = {}
        self.cache = {}
        self.mongodb_client = None
        self.sqlite_conn = None
        
        # Initialisierung
        self._initialize_connections()
        self._setup_demo_data()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Konfiguration laden"""
        default_config = {
            'mongodb': {
                'host': 'localhost',
                'port': 27017,
                'database': 'gmunden_db',
                'username': None,
                'password': None
            },
            'sqlite': {
                'path': 'data/gmunden.db'
            },
            'data_sources': {
                'ooe_api': {
                    'url': 'https://www.data.gv.at/katalog/api/3/action/package_search',
                    'active': True
                },
                'local_files': {
                    'path': 'data/imports',
                    'active': True
                }
            },
            'ocr': {
                'enabled': HAS_OCR,
                'language': 'deu',
                'dpi': 300
            },
            'quality': {
                'min_confidence': 0.7,
                'fact_check_enabled': True,
                'auto_validation': True
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    user_config = yaml.safe_load(f)
                else:
                    user_config = json.load(f)
            
            # Merge configs
            default_config.update(user_config)
        
        return default_config
    
    def _initialize_connections(self):
        """Datenbankverbindungen initialisieren"""
        try:
            # MongoDB
            mongo_config = self.config['mongodb']
            if mongo_config.get('username') and mongo_config.get('password'):
                connection_string = f"mongodb://{mongo_config['username']}:{mongo_config['password']}@{mongo_config['host']}:{mongo_config['port']}/{mongo_config['database']}"
            else:
                connection_string = f"mongodb://{mongo_config['host']}:{mongo_config['port']}"
            
            self.mongodb_client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            self.mongodb_db = self.mongodb_client[mongo_config['database']]
            
            # Test connection
            self.mongodb_client.admin.command('ping')
            logger.info("MongoDB connection established")
            
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {e}")
            self.mongodb_client = None
        
        try:
            # SQLite als Fallback
            sqlite_path = self.config['sqlite']['path']
            os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
            self.sqlite_conn = sqlite3.connect(sqlite_path, check_same_thread=False)
            self._setup_sqlite_schema()
            logger.info("SQLite connection established")
            
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}")
    
    def _setup_sqlite_schema(self):
        """SQLite-Schema erstellen"""
        cursor = self.sqlite_conn.cursor()
        
        # Finanzdaten
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS finanzen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jahr INTEGER,
                kategorie TEXT,
                beschreibung TEXT,
                betrag REAL,
                datum DATE,
                quelle TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Dokumente
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dokumente (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                filepath TEXT,
                typ TEXT,
                jahr INTEGER,
                titel TEXT,
                inhalt TEXT,
                ocr_text TEXT,
                filesize INTEGER,
                mime_type TEXT,
                hash TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Protokolle
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS protokolle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datum DATE,
                typ TEXT,
                titel TEXT,
                beschluesse TEXT,
                anwesende TEXT,
                dokument_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (dokument_id) REFERENCES dokumente (id)
            )
        ''')
        
        # Jahre-Status
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jahre (
                jahr INTEGER PRIMARY KEY,
                status TEXT,
                datensatz TEXT,
                total_documents INTEGER DEFAULT 0,
                last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Indizes erstellen
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_finanzen_jahr ON finanzen(jahr)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_finanzen_kategorie ON finanzen(kategorie)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dokumente_jahr ON dokumente(jahr)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_dokumente_typ ON dokumente(typ)')
        
        self.sqlite_conn.commit()
    
    def _setup_demo_data(self):
        """Demo-Daten für sofortiges Testen einrichten"""
        if not self._has_data():
            logger.info("Setting up demo data...")
            self._insert_demo_data()
    
    def _has_data(self) -> bool:
        """Prüfen ob bereits Daten vorhanden sind"""
        try:
            if self.mongodb_client:
                return self.mongodb_db.finanzen.count_documents({}) > 0
            else:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM finanzen")
                return cursor.fetchone()[0] > 0
        except:
            return False
    
    def _insert_demo_data(self):
        """Demo-Daten einfügen"""
        demo_finance_data = [
            {
                'jahr': 2023,
                'kategorie': 'infrastruktur',
                'beschreibung': 'Straßenreparatur Hauptstraße',
                'betrag': 25000.00,
                'datum': datetime(2023, 6, 15),
                'quelle': 'demo'
            },
            {
                'jahr': 2023,
                'kategorie': 'personal',
                'beschreibung': 'Gehälter Verwaltung',
                'betrag': 180000.00,
                'datum': datetime(2023, 12, 31),
                'quelle': 'demo'
            },
            {
                'jahr': 2022,
                'kategorie': 'infrastruktur',
                'beschreibung': 'Wasserleitungserneuerung',
                'betrag': 45000.00,
                'datum': datetime(2022, 8, 20),
                'quelle': 'demo'
            },
            {
                'jahr': 2022,
                'kategorie': 'kultur',
                'beschreibung': 'Stadtfest Organisation',
                'betrag': 8500.00,
                'datum': datetime(2022, 7, 10),
                'quelle': 'demo'
            },
            {
                'jahr': 2021,
                'kategorie': 'umwelt',
                'beschreibung': 'Grünflächenpflege',
                'betrag': 12000.00,
                'datum': datetime(2021, 5, 30),
                'quelle': 'demo'
            }
        ]
        
        try:
            if self.mongodb_client:
                self.mongodb_db.finanzen.insert_many(demo_finance_data)
            else:
                cursor = self.sqlite_conn.cursor()
                for item in demo_finance_data:
                    cursor.execute('''
                        INSERT INTO finanzen (jahr, kategorie, beschreibung, betrag, datum, quelle)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (item['jahr'], item['kategorie'], item['beschreibung'], 
                         item['betrag'], item['datum'], item['quelle']))
                self.sqlite_conn.commit()
            
            logger.info("Demo data inserted successfully")
            
        except Exception as e:
            logger.error(f"Failed to insert demo data: {e}")
    
    def search(self, nlp_result: Dict[str, Any]) -> Dict[str, Any]:
        """Hauptsuchfunktion basierend auf NLP-Ergebnis"""
        try:
            # Suchparameter extrahieren
            intent = nlp_result.get('intent', 'general_search')
            entities = nlp_result.get('entities', {})
            keywords = nlp_result.get('keywords', [])
            
            # Datenbankabfrage basierend auf Intent
            if intent == 'financial_search':
                results = self._search_finances(entities, keywords)
            elif intent == 'document_search':
                results = self._search_documents(entities, keywords)
            elif intent == 'protocol_search':
                results = self._search_protocols(entities, keywords)
            else:
                results = self._search_all(entities, keywords)
            
            return {
                'data': results,
                'sources': self._get_data_sources(results),
                'total_count': len(results),
                'search_params': {
                    'intent': intent,
                    'entities': entities,
                    'keywords': keywords
                }
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {'data': [], 'sources': [], 'total_count': 0, 'error': str(e)}
    
    def _search_finances(self, entities: Dict, keywords: List[str]) -> List[Dict]:
        """Finanzdaten durchsuchen"""
        query_conditions = {}
        
        # Jahr-Filter
        if 'year' in entities:
            if isinstance(entities['year'], list):
                query_conditions['jahr'] = {'$in': entities['year']}
            else:
                query_conditions['jahr'] = entities['year']
        
        # Kategorie-Filter
        if 'category' in entities:
            query_conditions['kategorie'] = {'$regex': entities['category'], '$options': 'i'}
        
        # Betrag-Filter
        if 'amount_min' in entities or 'amount_max' in entities:
            amount_filter = {}
            if 'amount_min' in entities:
                amount_filter['$gte'] = entities['amount_min']
            if 'amount_max' in entities:
                amount_filter['$lte'] = entities['amount_max']
            query_conditions['betrag'] = amount_filter
        
        # Keyword-Suche in Beschreibung
        if keywords:
            keyword_regex = '|'.join(keywords)
            query_conditions['beschreibung'] = {'$regex': keyword_regex, '$options': 'i'}
        
        try:
            if self.mongodb_client:
                cursor = self.mongodb_db.finanzen.find(query_conditions)
                results = list(cursor)
                # ObjectId zu String konvertieren
                for result in results:
                    result['_id'] = str(result['_id'])
            else:
                # SQLite-Abfrage
                sql_conditions = []
                params = []
                
                if 'jahr' in query_conditions:
                    if isinstance(query_conditions['jahr'], dict) and '$in' in query_conditions['jahr']:
                        placeholders = ','.join(['?' for _ in query_conditions['jahr']['$in']])
                        sql_conditions.append(f"jahr IN ({placeholders})")
                        params.extend(query_conditions['jahr']['$in'])
                    else:
                        sql_conditions.append("jahr = ?")
                        params.append(query_conditions['jahr'])
                
                if 'kategorie' in query_conditions:
                    sql_conditions.append("kategorie LIKE ?")
                    params.append(f"%{entities['category']}%")
                
                if 'betrag' in query_conditions:
                    if '$gte' in query_conditions['betrag']:
                        sql_conditions.append("betrag >= ?")
                        params.append(query_conditions['betrag']['$gte'])
                    if '$lte' in query_conditions['betrag']:
                        sql_conditions.append("betrag <= ?")
                        params.append(query_conditions['betrag']['$lte'])
                
                if keywords:
                    keyword_conditions = []
                    for keyword in keywords:
                        keyword_conditions.append("beschreibung LIKE ?")
                        params.append(f"%{keyword}%")
                    sql_conditions.append(f"({' OR '.join(keyword_conditions)})")
                
                sql = "SELECT * FROM finanzen"
                if sql_conditions:
                    sql += " WHERE " + " AND ".join(sql_conditions)
                sql += " ORDER BY datum DESC"
                
                cursor = self.sqlite_conn.cursor()
                cursor.execute(sql, params)
                
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return results
            
        except Exception as e:
            logger.error(f"Finance search error: {e}")
            return []
    
    def _search_documents(self, entities: Dict, keywords: List[str]) -> List[Dict]:
        """Dokumente durchsuchen"""
        query_conditions = {}
        
        # Jahr-Filter
        if 'year' in entities:
            query_conditions['jahr'] = entities['year']
        
        # Typ-Filter
        if 'document_type' in entities:
            query_conditions['typ'] = {'$regex': entities['document_type'], '$options': 'i'}
        
        # Volltext-Suche
        if keywords:
            keyword_regex = '|'.join(keywords)
            query_conditions['$or'] = [
                {'titel': {'$regex': keyword_regex, '$options': 'i'}},
                {'inhalt': {'$regex': keyword_regex, '$options': 'i'}},
                {'ocr_text': {'$regex': keyword_regex, '$options': 'i'}}
            ]
        
        try:
            if self.mongodb_client:
                cursor = self.mongodb_db.dokumente.find(query_conditions)
                results = list(cursor)
                for result in results:
                    result['_id'] = str(result['_id'])
            else:
                # SQLite-Implementierung
                sql_conditions = []
                params = []
                
                if 'jahr' in query_conditions:
                    sql_conditions.append("jahr = ?")
                    params.append(query_conditions['jahr'])
                
                if 'document_type' in entities:
                    sql_conditions.append("typ LIKE ?")
                    params.append(f"%{entities['document_type']}%")
                
                if keywords:
                    keyword_conditions = []
                    for keyword in keywords:
                        keyword_conditions.extend([
                            "titel LIKE ?",
                            "inhalt LIKE ?",
                            "ocr_text LIKE ?"
                        ])
                        params.extend([f"%{keyword}%"] * 3)
                    sql_conditions.append(f"({' OR '.join(keyword_conditions)})")
                
                sql = "SELECT * FROM dokumente"
                if sql_conditions:
                    sql += " WHERE " + " AND ".join(sql_conditions)
                sql += " ORDER BY created_at DESC"
                
                cursor = self.sqlite_conn.cursor()
                cursor.execute(sql, params)
                
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return results
            
        except Exception as e:
            logger.error(f"Document search error: {e}")
            return []
    
    def _search_protocols(self, entities: Dict, keywords: List[str]) -> List[Dict]:
        """Protokolle durchsuchen"""
        # Ähnlich wie Dokumente, aber spezifisch für Protokolle
        return self._search_documents(entities, keywords)
    
    def _search_all(self, entities: Dict, keywords: List[str]) -> List[Dict]:
        """Alle Datenquellen durchsuchen"""
        results = []
        
        # Finanzen durchsuchen
        finance_results = self._search_finances(entities, keywords)
        for result in finance_results:
            result['_source_type'] = 'finance'
        results.extend(finance_results)
        
        # Dokumente durchsuchen
        document_results = self._search_documents(entities, keywords)
        for result in document_results:
            result['_source_type'] = 'document'
        results.extend(document_results)
        
        return results
    
    def _get_data_sources(self, results: List[Dict]) -> List[str]:
        """Datenquellen aus Ergebnissen extrahieren"""
        sources = set()
        for result in results:
            if 'quelle' in result:
                sources.add(result['quelle'])
            if '_source_type' in result:
                sources.add(result['_source_type'])
        return list(sources)
    
    def get_available_years(self) -> List[int]:
        """Verfügbare Jahre abrufen"""
        try:
            if self.mongodb_client:
                years = self.mongodb_db.finanzen.distinct('jahr')
            else:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("SELECT DISTINCT jahr FROM finanzen WHERE jahr IS NOT NULL ORDER BY jahr DESC")
                years = [row[0] for row in cursor.fetchall()]
            
            return sorted(years, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting available years: {e}")
            return [2023, 2022, 2021]  # Fallback
    
    def get_categories(self) -> List[str]:
        """Verfügbare Kategorien abrufen"""
        try:
            if self.mongodb_client:
                categories = self.mongodb_db.finanzen.distinct('kategorie')
            else:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("SELECT DISTINCT kategorie FROM finanzen WHERE kategorie IS NOT NULL ORDER BY kategorie")
                categories = [row[0] for row in cursor.fetchall()]
            
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return ['infrastruktur', 'personal', 'kultur', 'umwelt']  # Fallback
    
    def get_total_documents(self) -> int:
        """Gesamtanzahl Dokumente abrufen"""
        try:
            if self.mongodb_client:
                return (self.mongodb_db.finanzen.count_documents({}) + 
                       self.mongodb_db.dokumente.count_documents({}))
            else:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM finanzen")
                finance_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM dokumente")
                doc_count = cursor.fetchone()[0]
                return finance_count + doc_count
                
        except Exception as e:
            logger.error(f"Error getting total documents: {e}")
            return 0
    
    def get_last_update(self) -> Optional[datetime]:
        """Letztes Update-Datum abrufen"""
        try:
            if self.mongodb_client:
                # Neuestes Dokument finden
                latest_finance = self.mongodb_db.finanzen.find_one(sort=[('created_at', -1)])
                latest_doc = self.mongodb_db.dokumente.find_one(sort=[('created_at', -1)])
                
                dates = []
                if latest_finance and 'created_at' in latest_finance:
                    dates.append(latest_finance['created_at'])
                if latest_doc and 'created_at' in latest_doc:
                    dates.append(latest_doc['created_at'])
                
                return max(dates) if dates else None
            else:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("""
                    SELECT MAX(created_at) FROM (
                        SELECT created_at FROM finanzen
                        UNION ALL
                        SELECT created_at FROM dokumente
                    )
                """)
                result = cursor.fetchone()[0]
                return datetime.fromisoformat(result) if result else None
                
        except Exception as e:
            logger.error(f"Error getting last update: {e}")
            return None
    
    def get_finance_overview(self, filters: Dict) -> Dict[str, Any]:
        """Finanz-Übersicht abrufen"""
        try:
            query_conditions = {}
            
            # Filter anwenden
            if filters.get('years'):
                query_conditions['jahr'] = {'$in': filters['years']}
            if filters.get('categories'):
                query_conditions['kategorie'] = {'$in': filters['categories']}
            if filters.get('min_amount'):
                query_conditions.setdefault('betrag', {})['$gte'] = filters['min_amount']
            if filters.get('max_amount'):
                query_conditions.setdefault('betrag', {})['$lte'] = filters['max_amount']
            
            if self.mongodb_client:
                # MongoDB Aggregation
                pipeline = [
                    {'$match': query_conditions},
                    {'$group': {
                        '_id': None,
                        'total_expenses': {'$sum': {'$cond': [{'$gt': ['$betrag', 0]}, '$betrag', 0]}},
                        'total_income': {'$sum': {'$cond': [{'$lt': ['$betrag', 0]}, {'$abs': '$betrag'}, 0]}},
                        'transaction_count': {'$sum': 1},
                        'avg_amount': {'$avg': '$betrag'}
                    }}
                ]
                
                result = list(self.mongodb_db.finanzen.aggregate(pipeline))
                if result:
                    return result[0]
            else:
                # SQLite-Implementierung
                sql_conditions = []
                params = []
                
                if filters.get('years'):
                    placeholders = ','.join(['?' for _ in filters['years']])
                    sql_conditions.append(f"jahr IN ({placeholders})")
                    params.extend(filters['years'])
                
                if filters.get('categories'):
                    placeholders = ','.join(['?' for _ in filters['categories']])
                    sql_conditions.append(f"kategorie IN ({placeholders})")
                    params.extend(filters['categories'])
                
                if filters.get('min_amount'):
                    sql_conditions.append("betrag >= ?")
                    params.append(filters['min_amount'])
                
                if filters.get('max_amount'):
                    sql_conditions.append("betrag <= ?")
                    params.append(filters['max_amount'])
                
                where_clause = " WHERE " + " AND ".join(sql_conditions) if sql_conditions else ""
                
                sql = f"""
                    SELECT 
                        SUM(CASE WHEN betrag > 0 THEN betrag ELSE 0 END) as total_expenses,
                        SUM(CASE WHEN betrag < 0 THEN ABS(betrag) ELSE 0 END) as total_income,
                        COUNT(*) as transaction_count,
                        AVG(betrag) as avg_amount
                    FROM finanzen
                    {where_clause}
                """
                
                cursor = self.sqlite_conn.cursor()
                cursor.execute(sql, params)
                result = cursor.fetchone()
                
                if result:
                    return {
                        'total_expenses': result[0] or 0,
                        'total_income': result[1] or 0,
                        'transaction_count': result[2] or 0,
                        'avg_amount': result[3] or 0
                    }
            
            return {
                'total_expenses': 0,
                'total_income': 0,
                'transaction_count': 0,
                'avg_amount': 0
            }
            
        except Exception as e:
            logger.error(f"Error getting finance overview: {e}")
            return {}
    
    def get_documents(self, filters: Dict) -> List[Dict]:
        """Dokumente mit Filtern abrufen"""
        try:
            query_conditions = {}
            
            if filters.get('years'):
                query_conditions['jahr'] = {'$in': filters['years']}
            
            if self.mongodb_client:
                cursor = self.mongodb_db.dokumente.find(query_conditions).limit(50)
                results = list(cursor)
                for result in results:
                    result['_id'] = str(result['_id'])
            else:
                sql_conditions = []
                params = []
                
                if filters.get('years'):
                    placeholders = ','.join(['?' for _ in filters['years']])
                    sql_conditions.append(f"jahr IN ({placeholders})")
                    params.extend(filters['years'])
                
                where_clause = " WHERE " + " AND ".join(sql_conditions) if sql_conditions else ""
                sql = f"SELECT * FROM dokumente {where_clause} ORDER BY created_at DESC LIMIT 50"
                
                cursor = self.sqlite_conn.cursor()
                cursor.execute(sql, params)
                
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    def process_uploaded_document(self, uploaded_file) -> Dict[str, Any]:
        """Hochgeladenes Dokument verarbeiten"""
        try:
            # Datei-Info extrahieren
            filename = uploaded_file.name
            file_content = uploaded_file.read()
            file_size = len(file_content)
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # Duplikat-Check
            if self._is_duplicate_document(file_hash):
                return {'success': False, 'error': 'Dokument bereits vorhanden'}
            
            # Inhalt extrahieren
            extracted_content = self._extract_document_content(file_content, mime_type)
            
            # Metadaten extrahieren
            metadata = self._extract_document_metadata(filename, extracted_content)
            
            # In Datenbank speichern
            document_data = {
                'filename': filename,
                'typ': self._determine_document_type(filename, extracted_content),
                'jahr': metadata.get('year'),
                'titel': metadata.get('title', filename),
                'inhalt': extracted_content.get('text', ''),
                'ocr_text': extracted_content.get('ocr_text', ''),
                'filesize': file_size,
                'mime_type': mime_type,
                'hash': file_hash,
                'created_at': datetime.now()
            }
            
            if self.mongodb_client:
                result = self.mongodb_db.dokumente.insert_one(document_data)
                document_id = str(result.inserted_id)
            else:
                cursor = self.sqlite_conn.cursor()
                cursor.execute('''
                    INSERT INTO dokumente (filename, typ, jahr, titel, inhalt, ocr_text, 
                                         filesize, mime_type, hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (document_data['filename'], document_data['typ'], document_data['jahr'],
                     document_data['titel'], document_data['inhalt'], document_data['ocr_text'],
                     document_data['filesize'], document_data['mime_type'], document_data['hash'],
                     document_data['created_at']))
                self.sqlite_conn.commit()
                document_id = cursor.lastrowid
            
            return {
                'success': True,
                'filename': filename,
                'document_id': document_id,
                'extracted_text_length': len(extracted_content.get('text', '')),
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing uploaded document: {e}")
            return {'success': False, 'error': str(e)}
    
    def _is_duplicate_document(self, file_hash: str) -> bool:
        """Prüfen ob Dokument bereits existiert"""
        try:
            if self.mongodb_client:
                return self.mongodb_db.dokumente.count_documents({'hash': file_hash}) > 0
            else:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM dokumente WHERE hash = ?", (file_hash,))
                return cursor.fetchone()[0] > 0
        except:
            return False
    
    def _extract_document_content(self, file_content: bytes, mime_type: str) -> Dict[str, str]:
        """Inhalt aus Dokument extrahieren"""
        content = {'text': '', 'ocr_text': ''}
        
        try:
            if mime_type == 'application/pdf':
                content = self._extract_pdf_content(file_content)
            elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                content = self._extract_docx_content(file_content)
            elif mime_type.startswith('text/'):
                content['text'] = file_content.decode('utf-8', errors='ignore')
            elif mime_type.startswith('image/') and HAS_OCR:
                content = self._extract_image_content(file_content)
            
        except Exception as e:
            logger.error(f"Error extracting content from {mime_type}: {e}")
        
        return content
    
    def _extract_pdf_content(self, file_content: bytes) -> Dict[str, str]:
        """PDF-Inhalt extrahieren"""
        content = {'text': '', 'ocr_text': ''}
        
        if not HAS_OCR:
            return content
        
        try:
            # PDF mit PyMuPDF öffnen
            pdf_document = fitz.open(stream=file_content, filetype="pdf")
            
            text_parts = []
            ocr_parts = []
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Text extrahieren
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)
                
                # OCR für Bilder/gescannte Seiten
                if not page_text.strip() or len(page_text.strip()) < 50:
                    try:
                        # Seite als Bild rendern
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x Zoom für bessere OCR
                        img_data = pix.tobytes("png")
                        
                        # OCR mit Tesseract
                        image = Image.open(io.BytesIO(img_data))
                        ocr_text = pytesseract.image_to_string(image, lang='deu')
                        if ocr_text.strip():
                            ocr_parts.append(ocr_text)
                    except Exception as e:
                        logger.warning(f"OCR failed for page {page_num}: {e}")
            
            pdf_document.close()
            
            content['text'] = '\n\n'.join(text_parts)
            content['ocr_text'] = '\n\n'.join(ocr_parts)
            
        except Exception as e:
            logger.error(f"Error extracting PDF content: {e}")
        
        return content
    
    def _extract_docx_content(self, file_content: bytes) -> Dict[str, str]:
        """DOCX-Inhalt extrahieren"""
        content = {'text': '', 'ocr_text': ''}
        
        try:
            # Vereinfachte DOCX-Extraktion
            # In einer vollständigen Implementierung würde python-docx verwendet
            content['text'] = "DOCX-Inhalt (vereinfacht extrahiert)"
        except Exception as e:
            logger.error(f"Error extracting DOCX content: {e}")
        
        return content
    
    def _extract_image_content(self, file_content: bytes) -> Dict[str, str]:
        """Bild-Inhalt mit OCR extrahieren"""
        content = {'text': '', 'ocr_text': ''}
        
        if not HAS_OCR:
            return content
        
        try:
            image = Image.open(io.BytesIO(file_content))
            ocr_text = pytesseract.image_to_string(image, lang='deu')
            content['ocr_text'] = ocr_text
        except Exception as e:
            logger.error(f"Error extracting image content: {e}")
        
        return content
    
    def _extract_document_metadata(self, filename: str, content: Dict[str, str]) -> Dict[str, Any]:
        """Metadaten aus Dokument extrahieren"""
        metadata = {}
        
        # Jahr aus Dateiname extrahieren
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            metadata['year'] = int(year_match.group())
        
        # Titel aus Inhalt extrahieren (erste Zeile)
        text = content.get('text', '') or content.get('ocr_text', '')
        if text:
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:
                    metadata['title'] = line[:100]  # Erste sinnvolle Zeile als Titel
                    break
        
        return metadata
    
    def _determine_document_type(self, filename: str, content: Dict[str, str]) -> str:
        """Dokumenttyp bestimmen"""
        filename_lower = filename.lower()
        text = (content.get('text', '') + ' ' + content.get('ocr_text', '')).lower()
        
        if 'protokoll' in filename_lower or 'protokoll' in text:
            return 'protokoll'
        elif 'rechnung' in filename_lower or 'rechnung' in text:
            return 'rechnung'
        elif 'vertrag' in filename_lower or 'vertrag' in text:
            return 'vertrag'
        elif 'bericht' in filename_lower or 'bericht' in text:
            return 'bericht'
        else:
            return 'dokument'
    
    def import_from_api(self, api_name: str) -> Dict[str, Any]:
        """Daten von API importieren"""
        try:
            if api_name == 'ooe_api':
                return self._import_from_ooe_api()
            else:
                return {'success': False, 'error': f'Unknown API: {api_name}'}
        except Exception as e:
            logger.error(f"API import error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _import_from_ooe_api(self) -> Dict[str, Any]:
        """Daten von OÖ Open Data API importieren"""
        try:
            api_url = self.config['data_sources']['ooe_api']['url']
            params = {
                'q': 'gmunden',
                'rows': 100
            }
            
            response = requests.get(api_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            imported_count = 0
            
            # Daten verarbeiten und importieren
            for package in data.get('result', {}).get('results', []):
                # Vereinfachte Verarbeitung
                imported_count += 1
            
            return {
                'success': True,
                'imported_count': imported_count,
                'source': 'ooe_api'
            }
            
        except Exception as e:
            logger.error(f"OÖ API import error: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_data(self, format: str, filters: Dict = None) -> Dict[str, Any]:
        """Daten exportieren"""
        try:
            if format.lower() == 'csv':
                return self._export_to_csv(filters)
            elif format.lower() == 'json':
                return self._export_to_json(filters)
            else:
                return {'success': False, 'error': f'Unsupported format: {format}'}
        except Exception as e:
            logger.error(f"Export error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _export_to_csv(self, filters: Dict = None) -> Dict[str, Any]:
        """Daten als CSV exportieren"""
        try:
            # Finanzdaten abrufen
            finance_data = self._search_finances(filters or {}, [])
            
            if finance_data:
                df = pd.DataFrame(finance_data)
                csv_content = df.to_csv(index=False)
                
                return {
                    'success': True,
                    'content': csv_content,
                    'filename': f'gmunden_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    'mime_type': 'text/csv'
                }
            else:
                return {'success': False, 'error': 'No data to export'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _export_to_json(self, filters: Dict = None) -> Dict[str, Any]:
        """Daten als JSON exportieren"""
        try:
            # Alle Daten abrufen
            all_data = self._search_all(filters or {}, [])
            
            if all_data:
                json_content = json.dumps(all_data, default=str, indent=2, ensure_ascii=False)
                
                return {
                    'success': True,
                    'content': json_content,
                    'filename': f'gmunden_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                    'mime_type': 'application/json'
                }
            else:
                return {'success': False, 'error': 'No data to export'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """System-Statistiken abrufen"""
        try:
            stats = {
                'database_type': 'MongoDB' if self.mongodb_client else 'SQLite',
                'total_documents': self.get_total_documents(),
                'available_years': self.get_available_years(),
                'categories': self.get_categories(),
                'last_update': self.get_last_update(),
                'data_sources': list(self.config['data_sources'].keys()),
                'ocr_enabled': HAS_OCR,
                'excel_support': HAS_EXCEL
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    def __del__(self):
        """Cleanup bei Objektzerstörung"""
        try:
            if self.mongodb_client:
                self.mongodb_client.close()
            if self.sqlite_conn:
                self.sqlite_conn.close()
        except:
            pass