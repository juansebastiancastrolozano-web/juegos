"""Sistema de notificaciones (Telegram y Desktop)."""

import asyncio
from typing import Optional, List
from datetime import datetime

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

import aiohttp
TELEGRAM_AVAILABLE = True

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.api_clients import GameDeal


class Notifier:
    """Sistema de notificaciones unificado."""
    
    def __init__(self):
        self.telegram_token = TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = TELEGRAM_CHAT_ID
        self.telegram_enabled = bool(self.telegram_token and self.telegram_chat_id)
        self.desktop_enabled = PLYER_AVAILABLE
    
    async def send_telegram_message(self, message: str) -> bool:
        """Envía un mensaje a través de Telegram."""
        if not self.telegram_enabled:
            return False
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": self.telegram_chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                
                async with session.post(url, json=payload) as response:
                    return response.status == 200
        except Exception as e:
            print(f"Error enviando mensaje de Telegram: {e}")
            return False
    
    def send_desktop_notification(self, title: str, message: str) -> bool:
        """Envía una notificación de escritorio."""
        if not self.desktop_enabled:
            return False
        
        try:
            notification.notify(
                title=title,
                message=message,
                timeout=10
            )
            return True
        except Exception as e:
            print(f"Error enviando notificación de escritorio: {e}")
            return False
    
    def format_deal_message(self, deal: GameDeal, reason: Optional[str] = None) -> str:
        """Formatea un mensaje de oferta."""
        message = f"🎮 <b>{deal.title}</b>\n"
        message += f"🏪 Tienda: {deal.store}\n"
        message += f"💰 Precio: ${deal.price:.2f}"
        
        if deal.original_price > deal.price:
            message += f" (antes ${deal.original_price:.2f})\n"
            message += f"🎯 Descuento: {deal.discount_percent:.1f}%\n"
        else:
            message += "\n"
        
        if reason:
            message += f"✨ {reason}\n"
        
        message += f"🔗 {deal.url}"
        
        return message
    
    async def notify_amazing_deal(self, deal: GameDeal, reason: Optional[str] = None):
        """Notifica una oferta imperdible."""
        message = self.format_deal_message(deal, reason)
        title = f"🔥 Oferta Imperdible: {deal.title}"
        
        # Enviar notificaciones en paralelo
        tasks = []
        
        if self.telegram_enabled:
            tasks.append(self.send_telegram_message(message))
        
        if self.desktop_enabled:
            # Desktop notification es síncrona, la ejecutamos directamente
            self.send_desktop_notification(title, f"{deal.title} - ${deal.price:.2f} ({deal.discount_percent:.1f}% off)")
        
        if tasks:
            await asyncio.gather(*tasks)
    
    async def notify_target_price(self, deal: GameDeal, target_price: float):
        """Notifica cuando se alcanza un precio objetivo."""
        message = self.format_deal_message(deal, f"¡Precio objetivo alcanzado! (${target_price:.2f})")
        title = f"🎯 Precio Objetivo: {deal.title}"
        
        tasks = []
        
        if self.telegram_enabled:
            tasks.append(self.send_telegram_message(message))
        
        if self.desktop_enabled:
            self.send_desktop_notification(
                title,
                f"{deal.title} - ${deal.price:.2f} (objetivo: ${target_price:.2f})"
            )
        
        if tasks:
            await asyncio.gather(*tasks)
    
    async def notify_multiple_deals(self, deals: List[GameDeal], title: str = "Ofertas Encontradas"):
        """Notifica múltiples ofertas en un solo mensaje."""
        if not deals:
            return
        
        message = f"<b>{title}</b>\n\n"
        
        for i, deal in enumerate(deals[:10], 1):  # Limitar a 10 ofertas
            message += f"{i}. <b>{deal.title}</b> - {deal.store}\n"
            message += f"   ${deal.price:.2f} ({deal.discount_percent:.1f}% off)\n"
            message += f"   {deal.url}\n\n"
        
        if len(deals) > 10:
            message += f"... y {len(deals) - 10} ofertas más"
        
        tasks = []
        
        if self.telegram_enabled:
            tasks.append(self.send_telegram_message(message))
        
        if self.desktop_enabled:
            self.send_desktop_notification(
                title,
                f"Se encontraron {len(deals)} ofertas"
            )
        
        if tasks:
            await asyncio.gather(*tasks)

