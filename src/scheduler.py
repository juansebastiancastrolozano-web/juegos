"""Scheduler para ejecución automática de verificaciones."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from src.database import Database
from src.watchlist import WatchlistManager
from src.api_clients import APIManager
from src.notifier import Notifier
from src.config import CHECK_INTERVAL_HOURS


class Scheduler:
    """Scheduler para verificación automática de watchlist."""
    
    def __init__(self, itad_api_key: Optional[str] = None):
        self.db = Database()
        self.api_manager = APIManager(itad_api_key)
        self.watchlist_manager = WatchlistManager(self.db, self.api_manager)
        self.notifier = Notifier()
        self.running = False
        self.interval_hours = CHECK_INTERVAL_HOURS
    
    async def check_and_notify(self):
        """Verifica la watchlist y envía notificaciones."""
        print(f"[{datetime.now()}] Verificando watchlist...")
        
        results = await self.watchlist_manager.check_all_games()
        
        amazing_deals = []
        target_deals = []
        
        for result in results:
            deal = result["deal"]
            analysis = result["analysis"]
            
            # Ofertas imperdibles
            if result["is_amazing_deal"]:
                amazing_deals.append((deal, analysis["reason"]))
                await self.notifier.notify_amazing_deal(deal, analysis["reason"])
            
            # Precios objetivo alcanzados
            elif result["meets_target"]:
                target_price = result["watchlist_item"].get("target_price")
                if target_price:
                    target_deals.append(deal)
                    await self.notifier.notify_target_price(deal, target_price)
        
        if amazing_deals or target_deals:
            print(f"[{datetime.now()}] Se encontraron {len(amazing_deals)} ofertas imperdibles y {len(target_deals)} precios objetivo")
        else:
            print(f"[{datetime.now()}] No se encontraron ofertas destacadas")
    
    async def run_forever(self):
        """Ejecuta el scheduler indefinidamente."""
        self.running = True
        print(f"Scheduler iniciado. Verificando cada {self.interval_hours} horas.")
        print(f"Primera verificación en 1 minuto...")
        
        # Esperar 1 minuto antes de la primera verificación
        await asyncio.sleep(60)
        
        while self.running:
            try:
                await self.check_and_notify()
            except Exception as e:
                print(f"[{datetime.now()}] Error en verificación: {e}")
            
            # Esperar hasta la próxima verificación
            next_check = datetime.now() + timedelta(hours=self.interval_hours)
            print(f"Próxima verificación: {next_check}")
            
            await asyncio.sleep(self.interval_hours * 3600)
    
    def stop(self):
        """Detiene el scheduler."""
        self.running = False
        print("Scheduler detenido.")


async def run_scheduler(itad_api_key: Optional[str] = None):
    """Función helper para ejecutar el scheduler."""
    scheduler = Scheduler(itad_api_key)
    
    try:
        await scheduler.run_forever()
    except KeyboardInterrupt:
        scheduler.stop()
        print("Scheduler interrumpido por el usuario.")

