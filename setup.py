"""Script de configuración inicial del proyecto."""

import subprocess
import sys
from pathlib import Path


def install_dependencies():
    """Instala las dependencias del proyecto."""
    print("Instalando dependencias...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✓ Dependencias instaladas")


def install_playwright():
    """Instala los navegadores de Playwright."""
    print("Instalando navegadores de Playwright...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    print("✓ Playwright configurado")


def create_directories():
    """Crea los directorios necesarios."""
    directories = ["data", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Directorio '{directory}' creado/verificado")


def main():
    """Función principal de setup."""
    print("=" * 50)
    print("Game Deal Hunter - Setup")
    print("=" * 50)
    print()
    
    try:
        create_directories()
        print()
        install_dependencies()
        print()
        install_playwright()
        print()
        print("=" * 50)
        print("✓ Setup completado exitosamente!")
        print("=" * 50)
        print()
        print("Próximos pasos:")
        print("1. (Opcional) Crea un archivo .env con tus API keys:")
        print("   - ITAD_API_KEY=tu_api_key")
        print("   - TELEGRAM_BOT_TOKEN=tu_token (opcional)")
        print("   - TELEGRAM_CHAT_ID=tu_chat_id (opcional)")
        print()
        print("2. Ejecuta la aplicación:")
        print("   python -m src.main")
        print()
    except Exception as e:
        print(f"✗ Error durante el setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

