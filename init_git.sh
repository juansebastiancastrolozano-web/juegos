#!/bin/bash
# Script para inicializar el repositorio Git

echo "Inicializando repositorio Git..."

# Inicializar Git si no está inicializado
if [ ! -d .git ]; then
    git init
    echo "✓ Repositorio Git inicializado"
fi

# Agregar todos los archivos
git add .

# Crear commit inicial
git commit -m "Initial commit: Game Deal Hunter - Sistema de monitoreo de ofertas de juegos"

echo ""
echo "✓ Repositorio Git configurado"
echo ""
echo "Para conectar con GitHub:"
echo "  git remote add origin https://github.com/juansebastiancastrolozano-web/juegos.git"
echo "  git branch -M main"
echo "  git push -u origin main"

