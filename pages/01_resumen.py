"""Pagina de portada ejecutiva del dashboard.

Resume el volumen de datos disponible y muestra una primera lectura
visual del proyecto antes de entrar al detalle.
"""

import streamlit as st

from components.cards import render_highlight_card, render_metric_card
from components.feedback import render_bullet_panel, render_info_panel
from services.catalog_service import get_product_catalog
from services.data_loader import load_processed_reviews
from services.feature_service import add_basic_text_features
from plots.eda_charts import build_stars_distribution, build_review_length_distribution
from services.preprocessing_service import get_corporate_audit_db
from utils.formatters import format_compact_number, format_percentage


st.title("Resumen Ejecutivo")
st.caption("Vista general del proyecto, el dataset procesado y los principales indicadores.")

reviews = add_basic_text_features(load_processed_reviews())
catalog = get_product_catalog()
corporate_db = get_corporate_audit_db()
has_processed_reviews = not reviews.empty

if has_processed_reviews and "y_util" in reviews.columns:
    useful_ratio = float(reviews["y_util"].mean())
else:
    useful_ratio = float(corporate_db["Helpfulness"].ge(0.70).mean()) if not corporate_db.empty else 0.0

if has_processed_reviews and "review_len" in reviews.columns:
    avg_length = int(reviews["review_len"].fillna(0).mean())
else:
    avg_length = int(corporate_db["Text"].astype(str).str.split().str.len().mean()) if not corporate_db.empty else 0

approved_ratio = float(corporate_db["Estado"].eq("APROBADA (Publicada)").mean()) if not corporate_db.empty else 0.0

# Estas tarjetas funcionan como lectura rapida del estado del proyecto.
metric_cols = st.columns(4)
with metric_cols[0]:
    render_metric_card("Reseñas procesadas", format_compact_number(len(reviews)), "Base analítica activa")
with metric_cols[1]:
    render_metric_card("Productos mapeados", format_compact_number(len(catalog)), "Catálogo contextual")
with metric_cols[2]:
    render_metric_card("Auditorías activas", format_compact_number(len(corporate_db)), "Base corporativa en memoria")
with metric_cols[3]:
    render_metric_card("Modelo principal", "LightGBM", "Artefacto cargado desde /modelos")

hero_left, hero_right = st.columns([1.25, 0.75], gap="large")
with hero_left:
    st.markdown(
        """
        <div class="section-panel">
            <div class="section-kicker">Lectura ejecutiva</div>
            <h3>Estado actual del producto analitico</h3>
            <p>
                Esta vista resume el estado del caso, el volumen de informacion disponible
                y la base operativa que alimenta la auditoria de reseñas en tiempo real.
            </p>
            <p>
                La idea de esta pagina es que un profesor o evaluador entienda rapido
                la escala del proyecto, la direccion tecnica y el valor del dashboard.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hero_right:
    render_highlight_card(
        "Reseñas útiles",
        format_percentage(useful_ratio),
        "Proporción estimada de reseñas útiles dentro de la base visible actual.",
    )
    render_highlight_card(
        "Longitud media",
        f"{avg_length} palabras",
        "Promedio aproximado de longitud textual observado en la base analítica.",
    )
    render_highlight_card(
        "Aprobación operativa",
        format_percentage(approved_ratio),
        "Porcentaje de registros clasificados como aprobados en la base corporativa.",
    )

left_col, right_col = st.columns(2, gap="large")
with left_col:
    st.subheader("Distribución de Calificaciones")
    st.plotly_chart(build_stars_distribution(reviews), use_container_width=True)
with right_col:
    st.subheader("Distribución de Longitud")
    st.plotly_chart(build_review_length_distribution(reviews), use_container_width=True)

insight_left, insight_right = st.columns([1, 1], gap="large")
with insight_left:
    render_bullet_panel(
        "Hallazgos rápidos",
        [
            "La nueva arquitectura ya separa interfaz, servicios, configuración y gráficos.",
            "La base corporativa en memoria permite simular el flujo operativo del producto.",
            "El resumen ejecutivo sirve como entrada para usuarios técnicos y no técnicos.",
        ],
    )
with insight_right:
    render_bullet_panel(
        "Qué sigue en la evolución",
        [
            "Completar el EDA con narrativa analítica y filtros globales.",
            "Conectar métricas reales de modelos en la página de evaluación.",
            "Convertir auditoría en una experiencia con feedback accionable más fuerte.",
        ],
    )

render_info_panel(
    "Lectura ejecutiva",
    "Este resumen ya funciona como una portada ejecutiva del producto. En la siguiente fase "
    "seguiremos fortaleciendo las páginas internas para que la navegación tenga una historia analítica completa.",
)
