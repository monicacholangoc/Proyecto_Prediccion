"""Punto de entrada de la aplicacion Streamlit.

Este archivo solo se encarga de preparar la experiencia global:
- configurar la pagina
- cargar estilos compartidos
- inicializar session state
- renderizar la portada general

La logica de datos, modelos y graficos vive en otras capas.
"""

import streamlit as st

from components.cards import render_metric_card, render_nav_card
from components.headers import render_app_hero
from config.constants import DEFAULT_METRICS
from config.theme import PAGE_CONFIG
from services.catalog_service import get_product_catalog
from services.data_loader import load_processed_reviews
from services.preprocessing_service import get_corporate_audit_db
from utils.formatters import format_compact_number
from utils.state import initialize_state


def load_css() -> None:
    """Carga el CSS global para mantener el estilo fuera de la UI."""
    with open("styles/styles.css", "r", encoding="utf-8") as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)


def main() -> None:
    """Orquesta la configuracion base antes de que Streamlit cargue paginas."""
    st.set_page_config(**PAGE_CONFIG)
    load_css()
    initialize_state()
    reviews = load_processed_reviews()
    catalog = get_product_catalog()
    corporate_db = get_corporate_audit_db()

    render_app_hero(
        title="Plataforma Analítica de Utilidad de Reseñas",
        subtitle=(
            "Proyecto de ciencia de datos para explorar, modelar y auditar la "
            "utilidad percibida de reseñas de Amazon Fine Food Reviews."
        ),
        tag="Seminario Predictivo 2026",
    )



    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-mark">SP</div>
                <div>
                    <div class="sidebar-brand-title">Seminario Predictivo</div>
                    <div class="sidebar-brand-subtitle">Dashboard analítico</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="sidebar-panel">
                <div class="sidebar-panel-title">Ruta recomendada</div>
                <div class="sidebar-panel-item">1. Resumen ejecutivo</div>
                <div class="sidebar-panel-item">2. Exploracion de datos</div>
                <div class="sidebar-panel-item">3. Modelos y evaluacion</div>
                <div class="sidebar-panel-item">4. Auditoria de reseñas</div>
                <div class="sidebar-panel-item">5. Ranking y benchmark</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Vista General")
    m1, m2, m3, m4 = st.columns(4, gap="medium")
    with m1:
        render_metric_card(
            "Dataset bruto",
            format_compact_number(DEFAULT_METRICS["registros_iniciales"]),
            "Registros historicos del caso",
        )
    with m2:
        render_metric_card(
            "Datos procesados",
            format_compact_number(len(reviews)),
            "Base disponible para exploracion",
        )
    with m3:
        render_metric_card(
            "Catalogo",
            format_compact_number(len(catalog)),
            "Productos con contexto",
        )
    with m4:
        render_metric_card(
            "Auditorias activas",
            format_compact_number(len(corporate_db)),
            "Base operativa de la app",
        )

    st.markdown("### Mapa de la Aplicacion")
    card_cols = st.columns(4, gap="medium")
    with card_cols[0]:
        render_nav_card("Resumen", "Lectura ejecutiva del caso, estado del dataset y panorama general.")
    with card_cols[1]:
        render_nav_card("Exploracion", "EDA estructurado con distribuciones, relaciones e insights.")
    with card_cols[2]:
        render_nav_card("Modelos", "Comparacion de clasificadores, metricas y criterio tecnico.")
    with card_cols[3]:
        render_nav_card("Auditoria", "Prediccion en tiempo real con retroalimentacion para el usuario.")




if __name__ == "__main__":
    main()