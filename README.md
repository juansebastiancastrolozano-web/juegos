# Game Deal Hunter 🎮

Sistema de monitoreo de ofertas de juegos de alto rendimiento que rastrea precios en múltiples plataformas (Steam, Epic Games, GOG, Humble Bundle, Fanatical) y alerta sobre ofertas históricas.

## Características

- 🔍 **Búsqueda Global**: Busca juegos y compara precios en todas las plataformas
- 🔥 **Detección de Ofertas Imperdibles**: Identifica ofertas con descuentos >75% o precios cercanos al mínimo histórico
- 📋 **Watchlist**: Sistema de seguimiento con precios objetivo
- 🔔 **Notificaciones**: Soporte para Telegram Bot y notificaciones de escritorio
- 🤖 **Automatización**: Scheduler que verifica la watchlist cada 6 horas
- 🎨 **CLI Moderna**: Interfaz de línea de comandos con Rich
- 🌐 **Interfaz Web**: Dashboard interactivo con Streamlit para visualizar watchlist y gráficos de precios

## Requisitos

- Python 3.12+
- Playwright (se instalará automáticamente)

## Instalación

### Opción 1: Setup Automático (Recomendado)

```bash
python setup.py
```

Este script automáticamente:
- Crea los directorios necesarios
- Instala todas las dependencias
- Configura Playwright

### Opción 2: Instalación Manual

1. Crea un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Instala los navegadores de Playwright:
```bash
playwright install chromium
```

4. (Opcional) Configura variables de entorno:
```bash
# Copia env_example.txt como .env
# Edita .env con tus API keys
```

## Uso

### 🌐 Interfaz Web (Streamlit) - Recomendado

```bash
streamlit run src/streamlit_app.py
```

O usando el script de inicio:
```bash
python streamlit_run.py
```

La interfaz web incluye:
- 📋 Visualización de tu Watchlist
- 📈 Gráficos interactivos de historial de precios
- 🔥 Ofertas imperdibles guardadas
- 🔍 Búsqueda y agregado de juegos a la watchlist

### 💻 Modo CLI (Interactivo)

```bash
python -m src.main --mode cli
```

O usando el script de inicio rápido:
```bash
python run.py
```

O simplemente:
```bash
python -m src.main
```

### 🤖 Modo Scheduler (Automático)

```bash
python -m src.main --mode scheduler --itad-key TU_API_KEY
```

O usando variable de entorno:
```bash
export ITAD_API_KEY=tu_api_key
python -m src.main --mode scheduler
```

## Configuración de APIs

### CheapShark
No requiere API key, funciona directamente.

### IsThereAnyDeal (ITAD)
1. Regístrate en [IsThereAnyDeal](https://isthereanydeal.com/)
2. Obtén tu API key desde tu perfil
3. Configúrala en `.env` o pásala como argumento

### Telegram Bot (Opcional)
1. Crea un bot con [@BotFather](https://t.me/botfather)
2. Obtén el token del bot
3. Obtén tu chat ID (puedes usar [@userinfobot](https://t.me/userinfobot))
4. Configúralos en `.env`

## Estructura del Proyecto

```
ofertas/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuración centralizada
│   ├── api_clients.py     # Clientes de APIs (CheapShark, ITAD)
│   ├── scraper.py         # Web scraping con Playwright
│   ├── database.py        # Gestión de SQLite
│   ├── deal_analyzer.py   # Lógica de análisis de ofertas
│   ├── watchlist.py       # Gestión de watchlist
│   ├── notifier.py        # Sistema de notificaciones
│   ├── cli.py             # Interfaz de línea de comandos
│   ├── scheduler.py       # Scheduler automático
│   └── main.py            # Punto de entrada
├── data/                  # Base de datos SQLite
├── logs/                  # Logs (si se implementan)
├── requirements.txt
├── .env.example
└── README.md
```

## Funcionalidades Detalladas

### Búsqueda de Juegos
Busca un juego en todas las plataformas y muestra una tabla comparativa de precios.

### Watchlist
- Agrega juegos a tu lista de seguimiento
- Establece precios objetivo
- El sistema verifica automáticamente y notifica cuando se alcanzan

### Ofertas Imperdibles
Una oferta se considera "imperdible" si:
- Tiene un descuento ≥75%, O
- El precio está dentro del 5% del mínimo histórico

### Notificaciones
- **Telegram**: Envía mensajes formateados con información de la oferta
- **Desktop**: Notificaciones nativas del sistema operativo

## Base de Datos

La aplicación usa SQLite para almacenar:
- Historial de precios
- Watchlist
- Ofertas imperdibles
- Precios históricos mínimos

La base de datos se crea automáticamente en `data/game_deals.db`.

## Desarrollo

El código está estructurado de forma modular para facilitar el mantenimiento y extensión. Cada módulo tiene responsabilidades claras:

- **API Clients**: Abstracción de las APIs externas
- **Scraper**: Web scraping para tiendas sin API
- **Database**: Capa de acceso a datos
- **Deal Analyzer**: Lógica de negocio para identificar ofertas
- **Watchlist Manager**: Gestión de la lista de seguimiento
- **Notifier**: Sistema de notificaciones unificado
- **CLI**: Interfaz de usuario
- **Scheduler**: Automatización

## Subir a GitHub

Para subir el proyecto a GitHub:

### Opción 1: Script Automático

**Windows:**
```bash
init_git.bat
```

**Linux/Mac:**
```bash
chmod +x init_git.sh
./init_git.sh
```

### Opción 2: Manual

```bash
# Inicializar Git (si no está inicializado)
git init

# Agregar archivos
git add .

# Crear commit inicial
git commit -m "Initial commit: Game Deal Hunter"

# Conectar con GitHub
git remote add origin https://github.com/juansebastiancastrolozano-web/juegos.git
git branch -M main
git push -u origin main
```

## Estructura del Proyecto

```
ofertas/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuración centralizada
│   ├── api_clients.py     # Clientes de APIs (CheapShark, ITAD)
│   ├── scraper.py         # Web scraping con Playwright
│   ├── database.py        # Gestión de SQLite
│   ├── deal_analyzer.py   # Lógica de análisis de ofertas
│   ├── watchlist.py       # Gestión de watchlist
│   ├── notifier.py        # Sistema de notificaciones
│   ├── cli.py             # Interfaz de línea de comandos
│   ├── scheduler.py        # Scheduler automático
│   ├── streamlit_app.py   # Interfaz web Streamlit
│   └── main.py            # Punto de entrada
├── data/                  # Base de datos SQLite
├── logs/                  # Logs (si se implementan)
├── requirements.txt
├── setup.py               # Script de instalación
├── streamlit_run.py       # Script para ejecutar Streamlit
├── run.py                 # Script de inicio rápido
├── init_git.sh            # Script de inicialización Git (Linux/Mac)
├── init_git.bat           # Script de inicialización Git (Windows)
├── env_example.txt        # Ejemplo de variables de entorno
└── README.md
```

## Licencia

Este proyecto es de código abierto y está disponible para uso personal.

