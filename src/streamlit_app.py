"""Aplicación web Streamlit para Game Deal Hunter."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from src.database import Database
from src.watchlist import WatchlistManager
from src.api_clients import APIManager
from src.deal_analyzer import DealAnalyzer


# Configuración de la página
st.set_page_config(
    page_title="Game Deal Hunter",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar componentes
@st.cache_resource
def init_components():
    """Inicializa los componentes principales."""
    db = Database()
    api_manager = APIManager()
    watchlist_manager = WatchlistManager(db, api_manager)
    analyzer = DealAnalyzer(db)
    return db, watchlist_manager, analyzer

db, watchlist_manager, analyzer = init_components()


def main():
    """Función principal de la aplicación."""
    st.title("🎮 Game Deal Hunter")
    st.markdown("### Monitorea ofertas de juegos en múltiples plataformas")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Opción para refrescar datos
        if st.button("🔄 Refrescar Datos", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Navegación")
        page = st.radio(
            "Selecciona una sección:",
            ["📋 Watchlist", "📈 Historial de Precios", "🔥 Ofertas Imperdibles", "🔍 Buscar Juegos"],
            label_visibility="collapsed"
        )
    
    # Renderizar página según selección
    if page == "📋 Watchlist":
        render_watchlist_page()
    elif page == "📈 Historial de Precios":
        render_price_history_page()
    elif page == "🔥 Ofertas Imperdibles":
        render_amazing_deals_page()
    elif page == "🔍 Buscar Juegos":
        render_search_page()


def render_watchlist_page():
    """Renderiza la página de watchlist."""
    st.header("📋 Mi Watchlist")
    
    # Obtener watchlist
    watchlist = watchlist_manager.get_games()
    
    if not watchlist:
        st.info("Tu watchlist está vacía. Agrega juegos desde la sección de búsqueda.")
        return
    
    # Mostrar estadísticas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Juegos", len(watchlist))
    with col2:
        with_target = sum(1 for w in watchlist if w.get('target_price'))
        st.metric("Con Precio Objetivo", with_target)
    with col3:
        checked_recently = sum(1 for w in watchlist if w.get('last_checked'))
        st.metric("Verificados Recientemente", checked_recently)
    with col4:
        st.metric("Activos", sum(1 for w in watchlist if w.get('is_active')))
    
    st.markdown("---")
    
    # Tabla de watchlist
    if watchlist:
        df = pd.DataFrame(watchlist)
        
        # Formatear columnas
        display_df = df.copy()
        display_df['target_price'] = display_df['target_price'].apply(
            lambda x: f"${x:.2f}" if x else "N/A"
        )
        display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['last_checked'] = display_df['last_checked'].apply(
            lambda x: pd.to_datetime(x).strftime('%Y-%m-%d %H:%M') if x else "Nunca"
        )
        
        # Renombrar columnas
        display_df = display_df.rename(columns={
            'game_title': 'Juego',
            'game_id': 'ID',
            'target_price': 'Precio Objetivo',
            'store': 'Tienda',
            'created_at': 'Agregado',
            'last_checked': 'Última Verificación'
        })
        
        # Mostrar tabla
        st.dataframe(
            display_df[['Juego', 'Precio Objetivo', 'Tienda', 'Agregado', 'Última Verificación']],
            use_container_width=True,
            hide_index=True
        )
        
        # Opción para eliminar de watchlist
        st.markdown("### 🗑️ Eliminar de Watchlist")
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_game = st.selectbox(
                "Selecciona un juego para eliminar:",
                options=[w['game_title'] for w in watchlist],
                label_visibility="collapsed"
            )
        with col2:
            if st.button("Eliminar", type="primary"):
                if watchlist_manager.remove_game(selected_game):
                    st.success(f"✓ '{selected_game}' eliminado de la watchlist")
                    st.rerun()
                else:
                    st.error(f"✗ Error al eliminar '{selected_game}'")


def render_price_history_page():
    """Renderiza la página de historial de precios."""
    st.header("📈 Historial de Precios")
    
    # Obtener watchlist para seleccionar juego
    watchlist = watchlist_manager.get_games()
    
    if not watchlist:
        st.info("Agrega juegos a tu watchlist para ver su historial de precios.")
        return
    
    # Selector de juego
    game_options = {f"{w['game_title']} ({w.get('store', 'Cualquiera')})": w for w in watchlist}
    selected = st.selectbox("Selecciona un juego:", options=list(game_options.keys()))
    
    if selected:
        selected_item = game_options[selected]
        game_title = selected_item['game_title']
        game_id = selected_item.get('game_id')
        store = selected_item.get('store')
        
        # Obtener historial
        if game_id:
            history = db.get_price_history(game_id, store)
        else:
            # Buscar por título si no hay ID
            history = []
            # Intentar buscar en la base de datos por título
            all_history = db.get_price_history(game_title, store)
            history = all_history if all_history else []
        
        if not history:
            st.warning(f"No hay historial de precios para '{game_title}' aún.")
            st.info("El historial se generará automáticamente cuando verifiques la watchlist.")
            return
        
        # Convertir a DataFrame
        df = pd.DataFrame(history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Estadísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            current_price = df.iloc[-1]['price'] if len(df) > 0 else 0
            st.metric("Precio Actual", f"${current_price:.2f}")
        with col2:
            min_price = df['price'].min()
            st.metric("Precio Mínimo", f"${min_price:.2f}")
        with col3:
            max_price = df['price'].max()
            st.metric("Precio Máximo", f"${max_price:.2f}")
        with col4:
            avg_price = df['price'].mean()
            st.metric("Precio Promedio", f"${avg_price:.2f}")
        
        st.markdown("---")
        
        # Gráfico de línea de precios
        st.subheader("📊 Evolución de Precios")
        
        fig = go.Figure()
        
        # Línea de precio actual
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['price'],
            mode='lines+markers',
            name='Precio',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ))
        
        # Línea de precio original
        if 'original_price' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['original_price'],
                mode='lines',
                name='Precio Original',
                line=dict(color='#ff7f0e', width=1, dash='dash'),
                opacity=0.6
            ))
        
        # Línea de precio mínimo histórico
        fig.add_hline(
            y=min_price,
            line_dash="dot",
            line_color="red",
            annotation_text=f"Mínimo: ${min_price:.2f}",
            annotation_position="right"
        )
        
        # Precio objetivo si existe
        target_price = selected_item.get('target_price')
        if target_price:
            fig.add_hline(
                y=target_price,
                line_dash="dot",
                line_color="green",
                annotation_text=f"Objetivo: ${target_price:.2f}",
                annotation_position="right"
            )
        
        fig.update_layout(
            title=f"Historial de Precios: {game_title}",
            xaxis_title="Fecha",
            yaxis_title="Precio (USD)",
            hovermode='x unified',
            height=500,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de descuentos
        if 'discount_percent' in df.columns and df['discount_percent'].max() > 0:
            st.subheader("🎯 Historial de Descuentos")
            
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=df['timestamp'],
                y=df['discount_percent'],
                name='Descuento (%)',
                marker_color='#2ca02c'
            ))
            
            fig2.update_layout(
                title="Descuentos a lo largo del tiempo",
                xaxis_title="Fecha",
                yaxis_title="Descuento (%)",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        # Tabla de historial
        st.subheader("📋 Detalles del Historial")
        display_df = df.copy()
        display_df = display_df[['timestamp', 'store', 'price', 'original_price', 'discount_percent', 'url']]
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        display_df['price'] = display_df['price'].apply(lambda x: f"${x:.2f}")
        display_df['original_price'] = display_df['original_price'].apply(lambda x: f"${x:.2f}")
        display_df['discount_percent'] = display_df['discount_percent'].apply(lambda x: f"{x:.1f}%")
        
        display_df = display_df.rename(columns={
            'timestamp': 'Fecha',
            'store': 'Tienda',
            'price': 'Precio',
            'original_price': 'Precio Original',
            'discount_percent': 'Descuento',
            'url': 'URL'
        })
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_amazing_deals_page():
    """Renderiza la página de ofertas imperdibles."""
    st.header("🔥 Ofertas Imperdibles")
    
    # Obtener ofertas imperdibles
    deals = db.get_amazing_deals(limit=50)
    
    if not deals:
        st.info("No hay ofertas imperdibles guardadas aún.")
        return
    
    # Estadísticas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Ofertas", len(deals))
    with col2:
        avg_discount = sum(d['discount_percent'] for d in deals) / len(deals) if deals else 0
        st.metric("Descuento Promedio", f"{avg_discount:.1f}%")
    with col3:
        notified_count = sum(1 for d in deals if d.get('notified'))
        st.metric("Notificadas", notified_count)
    
    st.markdown("---")
    
    # Mostrar ofertas
    for deal in deals:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### 🎮 {deal['game_title']}")
                st.markdown(f"**Tienda:** {deal['store']} | **Razón:** {deal['reason']}")
            
            with col2:
                st.metric("Precio", f"${deal['price']:.2f}")
                st.metric("Descuento", f"{deal['discount_percent']:.1f}%")
            
            col3, col4 = st.columns([2, 1])
            with col3:
                st.markdown(f"**Precio Original:** ${deal['original_price']:.2f}")
                st.markdown(f"**Fecha:** {deal['timestamp']}")
            with col4:
                if st.button(f"🔗 Ver Oferta", key=f"deal_{deal['id']}"):
                    st.markdown(f"[Abrir enlace]({deal['url']})")
            
            st.markdown("---")


def render_search_page():
    """Renderiza la página de búsqueda."""
    st.header("🔍 Buscar Juegos")
    
    # Formulario de búsqueda
    query = st.text_input("Buscar juego:", placeholder="Ej: The Witcher 3")
    
    if query:
        with st.spinner(f"Buscando '{query}'..."):
            import asyncio
            deals = asyncio.run(watchlist_manager.api_manager.search_game_global(query))
        
        if deals:
            st.success(f"Se encontraron {len(deals)} ofertas")
            
            # Mostrar ofertas
            for deal in deals:
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"### {deal.title}")
                        st.markdown(f"**Tienda:** {deal.store}")
                    
                    with col2:
                        st.metric("Precio", f"${deal.price:.2f}")
                        if deal.original_price > deal.price:
                            st.caption(f"Original: ${deal.original_price:.2f}")
                    
                    with col3:
                        st.metric("Descuento", f"{deal.discount_percent:.1f}%")
                        # Formulario para agregar a watchlist
                        with st.expander("➕ Agregar a Watchlist", expanded=False):
                            target_price = st.number_input(
                                "Precio objetivo (opcional):",
                                min_value=0.0,
                                value=deal.price,
                                key=f"target_{deal.deal_id}",
                                step=0.01
                            )
                            if st.button("Agregar", key=f"btn_add_{deal.deal_id}"):
                                if watchlist_manager.add_game(
                                    deal.title,
                                    deal.deal_id,
                                    target_price if target_price > 0 else None,
                                    deal.store
                                ):
                                    st.success(f"✓ '{deal.title}' agregado a la watchlist")
                                    st.rerun()
                                else:
                                    st.error(f"✗ Error al agregar '{deal.title}'")
                    
                    st.markdown(f"[🔗 Ver oferta]({deal.url})")
                    st.markdown("---")
        else:
            st.warning(f"No se encontraron resultados para '{query}'")


if __name__ == "__main__":
    main()

