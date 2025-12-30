"""Punto de entrada principal de la aplicación."""

import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli import CLI
from src.scheduler import run_scheduler
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Game Deal Hunter - Monitorea ofertas de juegos")
    parser.add_argument(
        "--mode",
        choices=["cli", "scheduler"],
        default="cli",
        help="Modo de ejecución: cli (interactivo) o scheduler (automático)"
    )
    parser.add_argument(
        "--itad-key",
        type=str,
        help="API key de IsThereAnyDeal (opcional)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "cli":
        cli = CLI()
        asyncio.run(cli.run())
    elif args.mode == "scheduler":
        itad_key = args.itad_key or os.getenv("ITAD_API_KEY")
        print("Iniciando scheduler...")
        print("Presiona Ctrl+C para detener")
        asyncio.run(run_scheduler(itad_key))


if __name__ == "__main__":
    main()

