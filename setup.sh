#!/bin/bash
# Script de instalación para producción

# Actualizar pip
python3 -m pip install --upgrade pip setuptools wheel

# Instalar dependencias
python3 -m pip install -r requirements.txt

# Instalar Playwright (opcional, puede fallar en algunos entornos)
python3 -m playwright install chromium --with-deps || echo "Playwright installation skipped"

