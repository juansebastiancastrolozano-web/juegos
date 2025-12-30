"""Configuración centralizada del proyecto."""

import os
from pathlib import Path
from typing import Optional

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Crear directorios si no existen
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Base de datos
DB_PATH = DATA_DIR / "game_deals.db"

# APIs
CHEAPSHARK_API_BASE = "https://www.cheapshark.com/api/1.0"
ITAD_API_BASE = "https://api.isthereanydeal.com/v01"

# Configuración de ofertas
MIN_DISCOUNT_FOR_DEAL = 75  # Descuento mínimo para oferta imperdible (%)
PRICE_TOLERANCE_PERCENT = 5  # Tolerancia para considerar precio cercano al mínimo histórico (%)

# Configuración de notificaciones
TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

# Configuración de scraping
PLAYWRIGHT_HEADLESS = True
PLAYWRIGHT_TIMEOUT = 30000  # 30 segundos

# Scheduler
CHECK_INTERVAL_HOURS = 6

