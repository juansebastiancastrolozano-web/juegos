@echo off
REM Script para inicializar el repositorio Git en Windows

echo Inicializando repositorio Git...

REM Inicializar Git si no está inicializado
if not exist .git (
    git init
    echo ✓ Repositorio Git inicializado
)

REM Agregar todos los archivos
git add .

REM Crear commit inicial
git commit -m "Initial commit: Game Deal Hunter - Sistema de monitoreo de ofertas de juegos"

echo.
echo ✓ Repositorio Git configurado
echo.
echo Para conectar con GitHub:
echo   git remote add origin https://github.com/juansebastiancastrolozano-web/juegos.git
echo   git branch -M main
echo   git push -u origin main

pause

