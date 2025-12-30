"""Análisis de ofertas para identificar ofertas imperdibles."""

from typing import Optional, Tuple
from src.api_clients import GameDeal
from src.config import MIN_DISCOUNT_FOR_DEAL, PRICE_TOLERANCE_PERCENT
from src.database import Database


class DealAnalyzer:
    """Analiza ofertas para determinar si son imperdibles."""
    
    def __init__(self, db: Database):
        self.db = db
        self.min_discount = MIN_DISCOUNT_FOR_DEAL
        self.price_tolerance = PRICE_TOLERANCE_PERCENT
    
    def is_amazing_deal(self, deal: GameDeal, game_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Determina si una oferta es imperdible.
        
        Retorna: (es_imperdible, razón)
        """
        reasons = []
        
        # Criterio 1: Descuento > 75%
        if deal.discount_percent >= self.min_discount:
            reasons.append(f"Descuento del {deal.discount_percent:.1f}%")
        
        # Criterio 2: Precio dentro del 5% del mínimo histórico
        historical_low = self.db.get_historical_low(game_id or deal.deal_id, deal.store)
        
        if historical_low:
            lowest_price = historical_low.get("lowest_price", float('inf'))
            if lowest_price != float('inf') and lowest_price > 0:
                price_diff_percent = abs(deal.price - lowest_price) / lowest_price * 100
                
                if price_diff_percent <= self.price_tolerance:
                    reasons.append(f"Precio cercano al mínimo histórico (${lowest_price:.2f})")
        
        # Si no hay historial, verificar si el precio actual es muy bajo
        if not historical_low and deal.price < 5.0 and deal.discount_percent > 50:
            reasons.append(f"Precio muy bajo (${deal.price:.2f}) con buen descuento")
        
        if reasons:
            reason = " | ".join(reasons)
            return True, reason
        
        return False, None
    
    def check_target_price(self, deal: GameDeal, target_price: float) -> bool:
        """Verifica si un precio cumple con el precio objetivo."""
        return deal.price <= target_price
    
    def analyze_deal(self, deal: GameDeal, game_id: Optional[str] = None,
                    target_price: Optional[float] = None) -> dict:
        """
        Análisis completo de una oferta.
        
        Retorna un diccionario con información del análisis.
        """
        is_amazing, reason = self.is_amazing_deal(deal, game_id)
        
        result = {
            "deal": deal,
            "is_amazing_deal": is_amazing,
            "reason": reason,
            "meets_target": None,
            "historical_low": None
        }
        
        # Verificar precio objetivo si se proporciona
        if target_price is not None:
            result["meets_target"] = self.check_target_price(deal, target_price)
        
        # Obtener precio histórico
        historical_low = self.db.get_historical_low(game_id or deal.deal_id, deal.store)
        if historical_low:
            result["historical_low"] = {
                "price": historical_low.get("lowest_price"),
                "store": historical_low.get("store"),
                "timestamp": historical_low.get("timestamp")
            }
        
        return result

