"""Gestión de la watchlist de juegos."""

from typing import List, Dict, Any, Optional
from src.database import Database
from src.api_clients import APIManager, GameDeal
from src.deal_analyzer import DealAnalyzer
from src.scraper import GameStoreScraper


class WatchlistManager:
    """Gestor de watchlist con verificación automática."""
    
    def __init__(self, db: Database, api_manager: APIManager):
        self.db = db
        self.api_manager = api_manager
        self.analyzer = DealAnalyzer(db)
    
    def add_game(self, game_title: str, game_id: Optional[str] = None,
                target_price: Optional[float] = None, store: Optional[str] = None) -> bool:
        """Agrega un juego a la watchlist."""
        return self.db.add_to_watchlist(game_title, game_id, target_price, store)
    
    def remove_game(self, game_title: str, store: Optional[str] = None) -> bool:
        """Elimina un juego de la watchlist."""
        return self.db.remove_from_watchlist(game_title, store)
    
    def get_games(self) -> List[Dict[str, Any]]:
        """Obtiene todos los juegos en la watchlist."""
        return self.db.get_watchlist(active_only=True)
    
    async def check_game(self, game_title: str, game_id: Optional[str] = None,
                        store: Optional[str] = None) -> List[GameDeal]:
        """Verifica el precio actual de un juego en la watchlist."""
        # Buscar el juego en todas las plataformas
        deals = await self.api_manager.search_game_global(game_title)
        
        # Si hay un store específico, filtrar
        if store:
            deals = [d for d in deals if store.lower() in d.store.lower()]
        
        return deals
    
    async def check_all_games(self) -> List[Dict[str, Any]]:
        """
        Verifica todos los juegos en la watchlist.
        
        Retorna una lista de resultados con ofertas encontradas.
        """
        watchlist = self.get_games()
        results = []
        
        for item in watchlist:
            game_title = item["game_title"]
            game_id = item.get("game_id")
            target_price = item.get("target_price")
            store = item.get("store")
            
            # Buscar ofertas actuales
            deals = await self.check_game(game_title, game_id, store)
            
            for deal in deals:
                # Analizar la oferta
                analysis = self.analyzer.analyze_deal(deal, game_id, target_price)
                
                # Guardar en historial
                self.db.add_price_history(deal, game_id)
                
                # Verificar si es oferta imperdible
                if analysis["is_amazing_deal"]:
                    self.db.save_amazing_deal(deal, analysis["reason"] or "Oferta imperdible")
                
                # Verificar si cumple precio objetivo
                meets_target = analysis.get("meets_target", False)
                
                result = {
                    "watchlist_item": item,
                    "deal": deal,
                    "analysis": analysis,
                    "meets_target": meets_target,
                    "is_amazing_deal": analysis["is_amazing_deal"]
                }
                
                results.append(result)
            
            # Actualizar última verificación
            self.db.update_watchlist_check(game_title, store)
        
        return results
    
    async def verify_price_with_scraper(self, game_url: str, store: str) -> Optional[GameDeal]:
        """Verifica el precio usando scraper para validación adicional."""
        async with GameStoreScraper() as scraper:
            scraped = await scraper.verify_price(game_url, store)
            
            if scraped:
                return GameDeal(
                    title=scraped.title,
                    store=scraped.store,
                    price=scraped.price,
                    original_price=scraped.original_price,
                    discount_percent=scraped.discount_percent,
                    url=scraped.url,
                    deal_id="",
                    timestamp=scraped.timestamp
                )
        
        return None

