"""Clientes para APIs de ofertas de juegos."""

import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from src.config import CHEAPSHARK_API_BASE, ITAD_API_BASE


@dataclass
class GameDeal:
    """Representa una oferta de juego."""
    title: str
    store: str
    price: float
    original_price: float
    discount_percent: float
    url: str
    deal_id: str
    timestamp: datetime


@dataclass
class PriceHistory:
    """Historial de precios de un juego."""
    game_id: str
    store: str
    price: float
    timestamp: datetime
    is_historical_low: bool = False


class CheapSharkClient:
    """Cliente para la API de CheapShark."""
    
    def __init__(self):
        self.base_url = CHEAPSHARK_API_BASE
    
    async def search_game(self, query: str) -> List[Dict[str, Any]]:
        """Busca juegos por nombre."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/games"
            params = {"title": query, "limit": 20}
            
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data if isinstance(data, list) else []
                    return []
            except Exception as e:
                print(f"Error en CheapShark search: {e}")
                return []
    
    async def get_deals(self, store_id: Optional[str] = None, 
                       upper_price: Optional[float] = None,
                       lower_price: Optional[float] = None) -> List[GameDeal]:
        """Obtiene ofertas de juegos."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/deals"
            params = {}
            
            if store_id:
                params["storeID"] = store_id
            if upper_price:
                params["upperPrice"] = str(int(upper_price))
            if lower_price:
                params["lowerPrice"] = str(int(lower_price))
            
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        deals = []
                        
                        for deal in data:
                            try:
                                game_deal = GameDeal(
                                    title=deal.get("title", "Unknown"),
                                    store=deal.get("storeID", "Unknown"),
                                    price=float(deal.get("salePrice", 0)),
                                    original_price=float(deal.get("normalPrice", 0)),
                                    discount_percent=float(deal.get("savings", 0)),
                                    url=f"https://www.cheapshark.com/redirect?dealID={deal.get('dealID')}",
                                    deal_id=deal.get("dealID", ""),
                                    timestamp=datetime.now()
                                )
                                deals.append(game_deal)
                            except (ValueError, KeyError) as e:
                                continue
                        
                        return deals
                    return []
            except Exception as e:
                print(f"Error en CheapShark get_deals: {e}")
                return []
    
    async def get_game_info(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información detallada de un juego."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/games"
            params = {"id": game_id}
            
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data if isinstance(data, dict) else None
                    return None
            except Exception as e:
                print(f"Error en CheapShark get_game_info: {e}")
                return None
    
    async def get_price_history(self, game_id: str) -> List[PriceHistory]:
        """Obtiene historial de precios de un juego."""
        # CheapShark no tiene endpoint directo de historial
        # Usaremos ITAD para esto
        return []


class ITADClient:
    """Cliente para la API de IsThereAnyDeal."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = ITAD_API_BASE
        self.api_key = api_key or ""
    
    async def search_game(self, query: str) -> List[Dict[str, Any]]:
        """Busca juegos por nombre."""
        if not self.api_key:
            return []
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/search/search"
            params = {
                "key": self.api_key,
                "q": query,
                "limit": 20
            }
            
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get(".meta", {}).get("match") == "found":
                            return data.get(".data", {}).get("list", [])
                        return []
                    return []
            except Exception as e:
                print(f"Error en ITAD search: {e}")
                return []
    
    async def get_current_prices(self, game_id: str) -> List[GameDeal]:
        """Obtiene precios actuales de un juego en todas las tiendas."""
        if not self.api_key:
            return []
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/game/prices"
            params = {
                "key": self.api_key,
                "plains": game_id,
                "region": "us",
                "country": "US"
            }
            
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        deals = []
                        
                        game_data = data.get(".data", {}).get(game_id, {})
                        stores = game_data.get("list", [])
                        
                        for store in stores:
                            try:
                                price_new = float(store.get("price_new", 0))
                                price_old = float(store.get("price_old", 0))
                                discount = ((price_old - price_new) / price_old * 100) if price_old > 0 else 0
                                
                                game_deal = GameDeal(
                                    title=game_data.get("title", "Unknown"),
                                    store=store.get("shop", {}).get("name", "Unknown"),
                                    price=price_new,
                                    original_price=price_old,
                                    discount_percent=discount,
                                    url=store.get("url", ""),
                                    deal_id=store.get("id", ""),
                                    timestamp=datetime.now()
                                )
                                deals.append(game_deal)
                            except (ValueError, KeyError) as e:
                                continue
                        
                        return deals
                    return []
            except Exception as e:
                print(f"Error en ITAD get_current_prices: {e}")
                return []
    
    async def get_price_history(self, game_id: str, shop: Optional[str] = None) -> List[PriceHistory]:
        """Obtiene historial de precios de un juego."""
        if not self.api_key:
            return []
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/game/history"
            params = {
                "key": self.api_key,
                "plains": game_id,
                "region": "us",
                "country": "US"
            }
            
            if shop:
                params["shops"] = shop
            
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        history = []
                        
                        game_data = data.get(".data", {}).get(game_id, {})
                        shops = game_data.get("list", [])
                        
                        for shop_data in shops:
                            shop_name = shop_data.get("shop", {}).get("name", "Unknown")
                            prices = shop_data.get("history", [])
                            
                            # Encontrar el precio mínimo histórico
                            min_price = min((p.get("price", float('inf')) for p in prices), default=float('inf'))
                            
                            for price_point in prices:
                                try:
                                    price = float(price_point.get("price", 0))
                                    timestamp_str = price_point.get("time", 0)
                                    timestamp = datetime.fromtimestamp(timestamp_str)
                                    
                                    price_history = PriceHistory(
                                        game_id=game_id,
                                        store=shop_name,
                                        price=price,
                                        timestamp=timestamp,
                                        is_historical_low=(price == min_price and min_price != float('inf'))
                                    )
                                    history.append(price_history)
                                except (ValueError, KeyError) as e:
                                    continue
                        
                        return history
                    return []
            except Exception as e:
                print(f"Error en ITAD get_price_history: {e}")
                return []
    
    async def get_historical_low(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el precio histórico más bajo de un juego."""
        if not self.api_key:
            return None
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/game/lowest"
            params = {
                "key": self.api_key,
                "plains": game_id,
                "region": "us",
                "country": "US"
            }
            
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get(".data", {}).get(game_id)
                    return None
            except Exception as e:
                print(f"Error en ITAD get_historical_low: {e}")
                return None


class APIManager:
    """Gestor unificado de APIs."""
    
    def __init__(self, itad_api_key: Optional[str] = None):
        self.cheapshark = CheapSharkClient()
        self.itad = ITADClient(itad_api_key)
    
    async def search_game_global(self, query: str) -> List[GameDeal]:
        """Busca un juego en todas las plataformas disponibles."""
        all_deals = []
        
        # Buscar en CheapShark - obtener deals directamente
        try:
            cheapshark_deals = await self.cheapshark.get_deals()
            # Filtrar por título (búsqueda aproximada)
            query_lower = query.lower()
            for deal in cheapshark_deals:
                if query_lower in deal.title.lower():
                    all_deals.append(deal)
        except Exception as e:
            print(f"Error buscando en CheapShark: {e}")
        
        # Buscar en ITAD
        try:
            itad_games = await self.itad.search_game(query)
            for game in itad_games:
                game_id = game.get("id", "")
                if game_id:
                    deals = await self.itad.get_current_prices(game_id)
                    all_deals.extend(deals)
        except Exception as e:
            print(f"Error buscando en ITAD: {e}")
        
        # Eliminar duplicados basados en título y tienda
        seen = set()
        unique_deals = []
        for deal in all_deals:
            key = (deal.title.lower(), deal.store.lower())
            if key not in seen:
                seen.add(key)
                unique_deals.append(deal)
        
        return unique_deals

