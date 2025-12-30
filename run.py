#!/usr/bin/env python
"""Script de inicio rápido para Game Deal Hunter."""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from src.main import main

if __name__ == "__main__":
    main()

