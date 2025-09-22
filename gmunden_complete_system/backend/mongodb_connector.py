#!/usr/bin/env python3
"""
MongoDB Connector für Gmunden Transparenz-System
Vollständige Datenbank-Integration
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logging.warning("PyMongo nicht verfügbar. Verwende Fallback-Speicherung.")

class MongoDBConnector:
    """MongoDB Connector mit Fallback auf lokale JSON-Dateien"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv(
            'MONGODB_URL', 
            'mongodb://admin:gmunden123@localhost:27017/gmunden?authSource=admin'
        )
        self.client = None
        self.db = None
        self.connected = False
        self.fallback_dir = Path("data/fallback_db")
        self.fallback_dir.mkdir(parents=True, exist_ok=True)
        
        self._connect()
    
    def _connect(self):
        """Verbindung zu MongoDB herstellen"""
        if not MONGODB_AVAILABLE:
            logging.info("MongoDB nicht verfügbar. Verwende lokale Dateien.")
            return
        
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Verbindung testen
            self.client.admin.command('ismaster')
            self.db = self.client.gmunden
            self.connected = True
            
            # Indizes erstellen
            self._create_indexes()
            
            logging.info("✅ MongoDB-Verbindung erfolgreich")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logging.warning(f"MongoDB-Verbindung fehlgeschlagen: {e}")
            logging.info("Verwende lokale JSON-Dateien als Fallback")
            self.connected = False
    
    def _create_indexes(self):
        """Erstelle optimierte Indizes"""
        if not self.connected:
            return
        
        try:
            # Dokumente-Indizes
            self.db.dokumente.create_index([("filename", 1)])
            self.db.dokumente.create_index([("jahr", 1)])
            self.db.dokumente.create_index([("kategorie", 1)])
            self.db.dokumente.create_index([("tags", 1)])
            self.db.dokumente.create_index([
                ("filename", "text"),
                ("ocr_text", "text"),
                ("tags", "text")
            ])
            
            # Finanzen-Indizes
            self.db.finanzen.create_index([("jahr", 1)])
            self.db.finanzen.create_index([("kategorie", 1)])
            self.db.finanzen.create_index([("betrag", -1)])
            
            # Protokolle-Indizes
            self.db.protokolle.create_index([("datum", -1)])
            self.db.protokolle.create_index([("typ", 1)])
            
            # Jahre-Index
            self.db.jahre.create_index([("jahr", 1)])
            
            logging.info("✅ MongoDB-Indizes erstellt")
            
        except Exception as e:
            logging.error(f"Fehler beim Erstellen der Indizes: {e}")
    
    def _fallback_read(self, collection: str, filter_dict: Dict = None) -> List[Dict]:
        """Lese aus lokaler JSON-Datei"""
        file_path = self.fallback_dir / f"{collection}.json"
        
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if filter_dict:
                # Einfache Filterung
                filtered_data = []
                for item in data:
                    match = True
                    for key, value in filter_dict.items():
                        if key not in item or item[key] != value:
                            match = False
                            break
                    if match:
                        filtered_data.append(item)
                return filtered_data
            
            return data
            
        except Exception as e:
            logging.error(f"Fehler beim Lesen von {file_path}: {e}")
            return []
    
    def _fallback_write(self, collection: str, data: List[Dict]):
        """Schreibe in lokale JSON-Datei"""
        file_path = self.fallback_dir / f"{collection}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
        except Exception as e:
            logging.error(f"Fehler beim Schreiben von {file_path}: {e}")
    
    def _fallback_insert(self, collection: str, document: Dict):
        """Füge Dokument zu lokaler JSON-Datei hinzu"""
        existing_data = self._fallback_read(collection)
        
        # ID generieren falls nicht vorhanden
        if '_id' not in document:
            document['_id'] = hashlib.md5(
                json.dumps(document, sort_keys=True, default=str).encode()
            ).hexdigest()
        
        existing_data.append(document)
        self._fallback_write(collection, existing_data)
    
    def insert_document(self, collection: str, document: Dict) -> bool:
        """Füge Dokument hinzu"""
        document['created_at'] = datetime.now()
        document['updated_at'] = datetime.now()
        
        if self.connected:
            try:
                result = self.db[collection].insert_one(document)
                return result.inserted_id is not None
            except Exception as e:
                logging.error(f"MongoDB Insert-Fehler: {e}")
                # Fallback
                self._fallback_insert(collection, document)
                return True
        else:
            self._fallback_insert(collection, document)
            return True
    
    def find_documents(self, collection: str, filter_dict: Dict = None, 
                      limit: int = None, sort: List[Tuple] = None) -> List[Dict]:
        """Finde Dokumente"""
        if self.connected:
            try:
                cursor = self.db[collection].find(filter_dict or {})
                
                if sort:
                    cursor = cursor.sort(sort)
                
                if limit:
                    cursor = cursor.limit(limit)
                
                return list(cursor)
                
            except Exception as e:
                logging.error(f"MongoDB Find-Fehler: {e}")
                # Fallback
                return self._fallback_read(collection, filter_dict)
        else:
            return self._fallback_read(collection, filter_dict)
    
    def update_document(self, collection: str, filter_dict: Dict, 
                       update_dict: Dict) -> bool:
        """Aktualisiere Dokument"""
        update_dict['updated_at'] = datetime.now()
        
        if self.connected:
            try:
                result = self.db[collection].update_one(
                    filter_dict, 
                    {'$set': update_dict}
                )
                return result.modified_count > 0
            except Exception as e:
                logging.error(f"MongoDB Update-Fehler: {e}")
                return False
        else:
            # Fallback-Update (vereinfacht)
            data = self._fallback_read(collection)
            updated = False
            
            for item in data:
                match = True
                for key, value in filter_dict.items():
                    if key not in item or item[key] != value:
                        match = False
                        break
                
                if match:
                    item.update(update_dict)
                    updated = True
            
            if updated:
                self._fallback_write(collection, data)
            
            return updated
    
    def delete_document(self, collection: str, filter_dict: Dict) -> bool:
        """Lösche Dokument"""
        if self.connected:
            try:
                result = self.db[collection].delete_one(filter_dict)
                return result.deleted_count > 0
            except Exception as e:
                logging.error(f"MongoDB Delete-Fehler: {e}")
                return False
        else:
            # Fallback-Delete
            data = self._fallback_read(collection)
            original_length = len(data)
            
            filtered_data = []
            for item in data:
                match = True
                for key, value in filter_dict.items():
                    if key not in item or item[key] != value:
                        match = False
                        break
                
                if not match:
                    filtered_data.append(item)
            
            if len(filtered_data) < original_length:
                self._fallback_write(collection, filtered_data)
                return True
            
            return False
    
    def count_documents(self, collection: str, filter_dict: Dict = None) -> int:
        """Zähle Dokumente"""
        if self.connected:
            try:
                return self.db[collection].count_documents(filter_dict or {})
            except Exception as e:
                logging.error(f"MongoDB Count-Fehler: {e}")
                # Fallback
                return len(self._fallback_read(collection, filter_dict))
        else:
            return len(self._fallback_read(collection, filter_dict))
    
    def aggregate(self, collection: str, pipeline: List[Dict]) -> List[Dict]:
        """Aggregation-Pipeline"""
        if self.connected:
            try:
                return list(self.db[collection].aggregate(pipeline))
            except Exception as e:
                logging.error(f"MongoDB Aggregation-Fehler: {e}")
                return []
        else:
            # Vereinfachte Aggregation für Fallback
            data = self._fallback_read(collection)
            
            # Nur grundlegende Aggregationen unterstützt
            for stage in pipeline:
                if '$match' in stage:
                    # Filter anwenden
                    match_filter = stage['$match']
                    filtered_data = []
                    for item in data:
                        match = True
                        for key, value in match_filter.items():
                            if key not in item or item[key] != value:
                                match = False
                                break
                        if match:
                            filtered_data.append(item)
                    data = filtered_data
                
                elif '$group' in stage:
                    # Einfache Gruppierung
                    group_spec = stage['$group']
                    if '_id' in group_spec and group_spec['_id'] is None:
                        # Count all
                        return [{'_id': None, 'count': len(data)}]
            
            return data
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Statistiken aller Collections"""
        collections = ['dokumente', 'finanzen', 'protokolle', 'jahre', 'statistiken']
        stats = {}
        
        for collection in collections:
            stats[collection] = self.count_documents(collection)
        
        return stats
    
    def search_documents(self, collection: str, search_term: str, 
                        fields: List[str] = None) -> List[Dict]:
        """Volltext-Suche"""
        if self.connected:
            try:
                # MongoDB Text-Search
                return list(self.db[collection].find(
                    {'$text': {'$search': search_term}}
                ))
            except Exception as e:
                logging.error(f"MongoDB Search-Fehler: {e}")
                # Fallback
                pass
        
        # Fallback-Suche
        data = self._fallback_read(collection)
        search_fields = fields or ['filename', 'ocr_text', 'beschreibung', 'titel']
        results = []
        
        search_term_lower = search_term.lower()
        
        for item in data:
            for field in search_fields:
                if field in item and isinstance(item[field], str):
                    if search_term_lower in item[field].lower():
                        results.append(item)
                        break
        
        return results
    
    def backup_data(self, backup_path: str) -> bool:
        """Erstelle Backup aller Daten"""
        try:
            backup_data = {}
            collections = ['dokumente', 'finanzen', 'protokolle', 'jahre', 'statistiken']
            
            for collection in collections:
                backup_data[collection] = self.find_documents(collection)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            logging.info(f"✅ Backup erstellt: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"Backup-Fehler: {e}")
            return False
    
    def restore_data(self, backup_path: str) -> bool:
        """Stelle Daten aus Backup wieder her"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            for collection, documents in backup_data.items():
                # Collection leeren
                if self.connected:
                    self.db[collection].delete_many({})
                else:
                    self._fallback_write(collection, [])
                
                # Dokumente wiederherstellen
                for document in documents:
                    self.insert_document(collection, document)
            
            logging.info(f"✅ Daten wiederhergestellt aus: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"Restore-Fehler: {e}")
            return False
    
    def close(self):
        """Verbindung schließen"""
        if self.client:
            self.client.close()
            logging.info("MongoDB-Verbindung geschlossen")

# Globale Instanz
db_connector = MongoDBConnector()