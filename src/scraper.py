"""Web scraper usando Playwright para tiendas sin API."""

from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page
from dataclasses import dataclass
from datetime import datetime

from src.config import PLAYWRIGHT_HEADLESS, PLAYWRIGHT_TIMEOUT
from src.api_clients import GameDeal


@dataclass
class ScrapedPrice:
    """Precio obtenido mediante scraping."""
    title: str
    store: str
    price: float
    original_price: float
    discount_percent: float
    url: str
    timestamp: datetime


class GameStoreScraper:
    """Scraper genérico para tiendas de juegos."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.headless = PLAYWRIGHT_HEADLESS
        self.timeout = PLAYWRIGHT_TIMEOUT
    
    async def __aenter__(self):
        """Context manager entry."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.browser:
            await self.browser.close()
    
    async def scrape_steam_price(self, game_url: str) -> Optional[ScrapedPrice]:
        """Scrapea el precio de un juego en Steam."""
        if not self.browser:
            return None
        
        page = await self.browser.new_page()
        
        try:
            await page.goto(game_url, wait_until="networkidle", timeout=self.timeout)
            
            # Selectores comunes de Steam
            title_selector = "h1.apphub_AppName"
            price_selector = ".game_purchase_price, .discount_final_price"
            original_price_selector = ".discount_original_price"
            
            title = await page.text_content(title_selector) or "Unknown"
            
            # Intentar obtener precio con descuento
            discount_price_elem = await page.query_selector(price_selector)
            original_price_elem = await page.query_selector(original_price_selector)
            
            if discount_price_elem:
                price_text = await discount_price_elem.text_content() or "0"
                price = self._parse_price(price_text)
                
                if original_price_elem:
                    original_price_text = await original_price_elem.text_content() or "0"
                    original_price = self._parse_price(original_price_text)
                else:
                    original_price = price
                
                discount = ((original_price - price) / original_price * 100) if original_price > 0 else 0
            else:
                # Sin descuento
                price_elem = await page.query_selector(".game_purchase_price")
                if price_elem:
                    price_text = await price_elem.text_content() or "0"
                    price = self._parse_price(price_text)
                    original_price = price
                    discount = 0
                else:
                    return None
            
            return ScrapedPrice(
                title=title.strip(),
                store="Steam",
                price=price,
                original_price=original_price,
                discount_percent=discount,
                url=game_url,
                timestamp=datetime.now()
            )
        
        except Exception as e:
            print(f"Error scraping Steam: {e}")
            return None
        finally:
            await page.close()
    
    async def scrape_epic_price(self, game_url: str) -> Optional[ScrapedPrice]:
        """Scrapea el precio de un juego en Epic Games Store."""
        if not self.browser:
            return None
        
        page = await self.browser.new_page()
        
        try:
            await page.goto(game_url, wait_until="networkidle", timeout=self.timeout)
            
            # Selectores de Epic Games Store
            title_selector = "h1"
            price_selector = "[data-testid='purchase-price']"
            original_price_selector = "[data-testid='original-price']"
            
            title_elem = await page.query_selector(title_selector)
            title = await title_elem.text_content() if title_elem else "Unknown"
            
            price_elem = await page.query_selector(price_selector)
            original_price_elem = await page.query_selector(original_price_selector)
            
            if price_elem:
                price_text = await price_elem.text_content() or "0"
                price = self._parse_price(price_text)
                
                if original_price_elem:
                    original_price_text = await original_price_elem.text_content() or "0"
                    original_price = self._parse_price(original_price_text)
                else:
                    original_price = price
                
                discount = ((original_price - price) / original_price * 100) if original_price > 0 else 0
                
                return ScrapedPrice(
                    title=title.strip(),
                    store="Epic Games",
                    price=price,
                    original_price=original_price,
                    discount_percent=discount,
                    url=game_url,
                    timestamp=datetime.now()
                )
            
            return None
        
        except Exception as e:
            print(f"Error scraping Epic: {e}")
            return None
        finally:
            await page.close()
    
    def _parse_price(self, price_text: str) -> float:
        """Parsea texto de precio a float."""
        import re
        
        # Remover símbolos y espacios
        price_text = price_text.replace("$", "").replace("€", "").replace("£", "").strip()
        
        # Buscar número con decimales
        match = re.search(r'(\d+[.,]\d+|\d+)', price_text)
        if match:
            price_str = match.group(1).replace(",", ".")
            try:
                return float(price_str)
            except ValueError:
                return 0.0
        
        return 0.0
    
    async def verify_price(self, game_url: str, store: str) -> Optional[ScrapedPrice]:
        """Verifica el precio actual de un juego en una tienda específica."""
        store_lower = store.lower()
        
        if "steam" in store_lower:
            return await self.scrape_steam_price(game_url)
        elif "epic" in store_lower:
            return await self.scrape_epic_price(game_url)
        else:
            # Intentar scraping genérico
            return await self._generic_scrape(game_url, store)
    
    async def _generic_scrape(self, game_url: str, store: str) -> Optional[ScrapedPrice]:
        """Scraping genérico para tiendas desconocidas."""
        if not self.browser:
            return None
        
        page = await self.browser.new_page()
        
        try:
            await page.goto(game_url, wait_until="networkidle", timeout=self.timeout)
            
            # Intentar encontrar precio usando selectores comunes
            price_selectors = [
                "[data-price]",
                ".price",
                ".product-price",
                "[class*='price']",
                "[id*='price']"
            ]
            
            price = 0.0
            original_price = 0.0
            
            for selector in price_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    price_text = await elements[0].text_content()
                    if price_text:
                        price = self._parse_price(price_text)
                        original_price = price
                        break
            
            if price > 0:
                title_elem = await page.query_selector("h1, .title, [class*='title']")
                title = await title_elem.text_content() if title_elem else "Unknown"
                
                return ScrapedPrice(
                    title=title.strip(),
                    store=store,
                    price=price,
                    original_price=original_price,
                    discount_percent=0.0,
                    url=game_url,
                    timestamp=datetime.now()
                )
            
            return None
        
        except Exception as e:
            print(f"Error en scraping genérico: {e}")
            return None
        finally:
            await page.close()

