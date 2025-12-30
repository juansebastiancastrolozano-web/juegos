"""Gestión de base de datos SQLite."""

import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import json

from src.config import DB_PATH
from src.api_clients import GameDeal, PriceHistory


class Database:
    """Gestor de base de datos SQLite."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa las tablas de la base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de historial de precios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                game_title TEXT NOT NULL,
                store TEXT NOT NULL,
                price REAL NOT NULL,
                original_price REAL NOT NULL,
                discount_percent REAL NOT NULL,
                deal_id TEXT,
                url TEXT,
                timestamp DATETIME NOT NULL,
                UNIQUE(game_id, store, timestamp)
            )
        """)
        
        # Tabla de watchlist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_title TEXT NOT NULL,
                game_id TEXT,
                target_price REAL,
                store TEXT,
                created_at DATETIME NOT NULL,
                last_checked DATETIME,
                is_active INTEGER DEFAULT 1,
                UNIQUE(game_title, store)
            )
        """)
        
        # Tabla de ofertas imperdibles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS amazing_deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_title TEXT NOT NULL,
                store TEXT NOT NULL,
                price REAL NOT NULL,
                original_price REAL NOT NULL,
                discount_percent REAL NOT NULL,
                url TEXT NOT NULL,
                deal_id TEXT,
                reason TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                notified INTEGER DEFAULT 0
            )
        """)
        
        # Tabla de precios históricos mínimos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_lows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                game_title TEXT NOT NULL,
                store TEXT NOT NULL,
                lowest_price REAL NOT NULL,
                timestamp DATETIME NOT NULL,
                UNIQUE(game_id, store)
            )
        """)
        
        # Índices para mejorar rendimiento
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_price_history_game_store 
            ON price_history(game_id, store)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_price_history_timestamp 
            ON price_history(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_watchlist_active 
            ON watchlist(is_active)
        """)
        
        conn.commit()
        conn.close()
    
    def add_price_history(self, deal: GameDeal, game_id: Optional[str] = None) -> bool:
        """Agrega un registro al historial de precios."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO price_history 
                (game_id, game_title, store, price, original_price, discount_percent, 
                 deal_id, url, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game_id or deal.deal_id,
                deal.title,
                deal.store,
                deal.price,
                deal.original_price,
                deal.discount_percent,
                deal.deal_id,
                deal.url,
                deal.timestamp
            ))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error agregando historial de precios: {e}")
            return False
        finally:
            conn.close()
    
    def get_price_history(self, game_id: str, store: Optional[str] = None, 
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene el historial de precios de un juego."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if store:
                cursor.execute("""
                    SELECT * FROM price_history
                    WHERE game_id = ? AND store = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (game_id, store, limit))
            else:
                cursor.execute("""
                    SELECT * FROM price_history
                    WHERE game_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (game_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error obteniendo historial: {e}")
            return []
        finally:
            conn.close()
    
    def get_lowest_price(self, game_id: str, store: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Obtiene el precio más bajo registrado para un juego."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if store:
                cursor.execute("""
                    SELECT * FROM price_history
                    WHERE game_id = ? AND store = ?
                    ORDER BY price ASC
                    LIMIT 1
                """, (game_id, store))
            else:
                cursor.execute("""
                    SELECT * FROM price_history
                    WHERE game_id = ?
                    ORDER BY price ASC
                    LIMIT 1
                """, (game_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error obteniendo precio mínimo: {e}")
            return None
        finally:
            conn.close()
    
    def add_to_watchlist(self, game_title: str, game_id: Optional[str] = None,
                        target_price: Optional[float] = None, store: Optional[str] = None) -> bool:
        """Agrega un juego a la watchlist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO watchlist 
                (game_title, game_id, target_price, store, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (game_title, game_id, target_price, store, datetime.now()))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error agregando a watchlist: {e}")
            return False
        finally:
            conn.close()
    
    def get_watchlist(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Obtiene la lista de juegos en watchlist."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if active_only:
                cursor.execute("""
                    SELECT * FROM watchlist
                    WHERE is_active = 1
                    ORDER BY created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT * FROM watchlist
                    ORDER BY created_at DESC
                """)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error obteniendo watchlist: {e}")
            return []
        finally:
            conn.close()
    
    def remove_from_watchlist(self, game_title: str, store: Optional[str] = None) -> bool:
        """Elimina un juego de la watchlist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if store:
                cursor.execute("""
                    UPDATE watchlist
                    SET is_active = 0
                    WHERE game_title = ? AND store = ?
                """, (game_title, store))
            else:
                cursor.execute("""
                    UPDATE watchlist
                    SET is_active = 0
                    WHERE game_title = ?
                """, (game_title,))
            
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error eliminando de watchlist: {e}")
            return False
        finally:
            conn.close()
    
    def update_watchlist_check(self, game_title: str, store: Optional[str] = None):
        """Actualiza la fecha de última verificación de un juego en watchlist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if store:
                cursor.execute("""
                    UPDATE watchlist
                    SET last_checked = ?
                    WHERE game_title = ? AND store = ? AND is_active = 1
                """, (datetime.now(), game_title, store))
            else:
                cursor.execute("""
                    UPDATE watchlist
                    SET last_checked = ?
                    WHERE game_title = ? AND is_active = 1
                """, (datetime.now(), game_title))
            
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error actualizando check de watchlist: {e}")
        finally:
            conn.close()
    
    def save_amazing_deal(self, deal: GameDeal, reason: str) -> bool:
        """Guarda una oferta imperdible."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO amazing_deals 
                (game_title, store, price, original_price, discount_percent, 
                 url, deal_id, reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                deal.title,
                deal.store,
                deal.price,
                deal.original_price,
                deal.discount_percent,
                deal.url,
                deal.deal_id,
                reason,
                deal.timestamp
            ))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error guardando oferta imperdible: {e}")
            return False
        finally:
            conn.close()
    
    def get_amazing_deals(self, limit: int = 50, notified_only: bool = False) -> List[Dict[str, Any]]:
        """Obtiene ofertas imperdibles."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if notified_only:
                cursor.execute("""
                    SELECT * FROM amazing_deals
                    WHERE notified = 1
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            else:
                cursor.execute("""
                    SELECT * FROM amazing_deals
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"Error obteniendo ofertas imperdibles: {e}")
            return []
        finally:
            conn.close()
    
    def mark_deal_notified(self, deal_id: int):
        """Marca una oferta como notificada."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE amazing_deals
                SET notified = 1
                WHERE id = ?
            """, (deal_id,))
            
            conn.commit()
        except sqlite3.Error as e:
            print(f"Error marcando oferta como notificada: {e}")
        finally:
            conn.close()
    
    def update_historical_low(self, game_id: str, game_title: str, store: str, 
                             lowest_price: float) -> bool:
        """Actualiza el precio histórico más bajo de un juego."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO historical_lows
                (game_id, game_title, store, lowest_price, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (game_id, game_title, store, lowest_price, datetime.now()))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error actualizando precio histórico: {e}")
            return False
        finally:
            conn.close()
    
    def get_historical_low(self, game_id: str, store: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Obtiene el precio histórico más bajo de un juego."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if store:
                cursor.execute("""
                    SELECT * FROM historical_lows
                    WHERE game_id = ? AND store = ?
                """, (game_id, store))
            else:
                cursor.execute("""
                    SELECT * FROM historical_lows
                    WHERE game_id = ?
                    ORDER BY lowest_price ASC
                    LIMIT 1
                """, (game_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"Error obteniendo precio histórico: {e}")
            return None
        finally:
            conn.close()

