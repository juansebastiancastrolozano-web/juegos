#!/bin/bash
# Script de inicio para producción

# Crear directorios necesarios si no existen
mkdir -p data logs

# Ejecutar Streamlit
streamlit run src/streamlit_app.py --server.port=${PORT:-8501} --server.address=0.0.0.0

