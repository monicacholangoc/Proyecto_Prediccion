"""Resumen ejecutivo del proyecto.

Muestra el estado del dataset, indicadores clave con interpretación
en lenguaje natural y una lectura visual inicial del caso.
"""

import streamlit as st

from components.cards import render_highlight_card, render_metric_card
from services.catalog_service import get_product_catalog
from services.data_loader import load_processed_reviews
from services.feature_service import add_basic_text_features
from plots.eda_charts import build_stars_distribution, build_review_length_distribution
from services.preprocessing_service import get_corporate_audit_db
from utils.formatters import format_compact_number, format_percentage


st.title("Resumen Ejecutivo")
st.caption("Estado general del proyecto, el dataset procesado y los principales indicadores del caso.")

reviews = add_basic_text_features(load_processed_reviews())
catalog = get_product_catalog()
corporate_db = get_corporate_audit_db()
has_reviews = not reviews.empty

# ── Cálculo de indicadores ────────────────────────────────────────────────────

useful_ratio = (
    float(reviews["y_util"].mean()) if has_reviews and "y_util" in reviews.columns
    else float(corporate_db["Helpfulness"].ge(0.70).mean()) if not corporate_db.empty
    else 0.0
)

avg_length = (
    int(reviews["review_len"].fillna(0).mean()) if has_reviews and "review_len" in reviews.columns
    else int(corporate_db["Text"].astype(str).str.split().str.len().mean()) if not corporate_db.empty
    else 0
)

approved_ratio = (
    float(corporate_db["Estado"].eq("APROBADA (Publicada)").mean())
    if not corporate_db.empty else 0.0
)

incoherence_ratio = (
    float(reviews["incoherente"].mean()) if has_reviews and "incoherente" in reviews.columns
    else 0.0
)

# ── Bloque narrativo del caso ─────────────────────────────────────────────────

st.markdown(
    """
    <div class="insight-panel">
        <div class="insight-title">¿Qué busca predecir este proyecto?</div>
        <p>
            El dataset <strong>Amazon Fine Food Reviews</strong> contiene 568&nbsp;454 reseñas de alimentos
            con calificación en estrellas y contadores de cuántos usuarios encontraron útil cada reseña.
            El reto: la utilidad <em>no depende solo de la nota</em> — depende de la longitud, el sentimiento
            del texto y la coherencia entre ambos. Este dashboard modela esa relación y permite
            auditar reseñas en tiempo real.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Tarjetas de métricas principales ─────────────────────────────────────────

st.markdown("### Estado del Dataset")
m1, m2, m3, m4 = st.columns(4, gap="medium")

with m1:
    render_metric_card(
        "Dataset original",
        "568 454",
        "Reseñas históricas en bruto — antes de limpiar",
    )
with m2:
    render_metric_card(
        "Base analítica activa",
        format_compact_number(len(reviews)) if has_reviews else "—",
        "Tras filtrar ≥ 5 votos y eliminar duplicados",
    )
with m3:
    render_metric_card(
        "Productos con contexto",
        format_compact_number(len(catalog)),
        "Catálogo enriquecido con categoría y nombre",
    )
with m4:
    render_metric_card(
        "Registros en auditoría",
        format_compact_number(len(corporate_db)),
        "Base corporativa operativa (en memoria)",
    )

# ── Indicadores de calidad con interpretación ─────────────────────────────────

st.markdown("### Indicadores Clave del Análisis")
st.caption(
    "Estos valores resumen la calidad del dataset y los patrones encontrados. "
    "Son el punto de partida para entender qué hace útil a una reseña."
)

k1, k2, k3 = st.columns(3, gap="medium")

with k1:
    label_util = "Por encima del promedio típico" if useful_ratio > 0.40 else "Desbalance esperado en datasets de opinión"
    badge_class = "metric-badge-good" if useful_ratio > 0.40 else "metric-badge-warn"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Reseñas consideradas útiles</div>
            <div class="metric-value">{format_percentage(useful_ratio)}</div>
            <div class="metric-caption">
                Proporción de reseñas con tasa de utilidad ≥ 0.70 en la base visible.
                Este umbral define la variable objetivo del modelo.
            </div>
            <span class="metric-badge {badge_class}">{label_util}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k2:
    label_len = "Longitud adecuada" if avg_length > 60 else "Reseñas cortas predominan"
    badge_len = "metric-badge-good" if avg_length > 60 else "metric-badge-warn"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Longitud media de reseña</div>
            <div class="metric-value">{avg_length} palabras</div>
            <div class="metric-caption">
                Feature directa del modelo. Las reseñas más largas tienden a ser
                percibidas como más útiles por otros compradores.
            </div>
            <span class="metric-badge {badge_len}">{label_len}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k3:
    label_aprov = "Tasa operativa sana" if approved_ratio > 0.60 else "Revisar criterios de aprobación"
    badge_aprov = "metric-badge-good" if approved_ratio > 0.60 else "metric-badge-warn"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Reseñas aprobadas en sistema</div>
            <div class="metric-value">{format_percentage(approved_ratio)}</div>
            <div class="metric-caption">
                Porcentaje de registros clasificados como "Publicada" según
                el umbral del modelo en la base corporativa activa.
            </div>
            <span class="metric-badge {badge_aprov}">{label_aprov}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Hipótesis del proyecto ─────────────────────────────────────────────────────

st.markdown("### Hipótesis del Proyecto")
h1, h2, h3 = st.columns(3, gap="medium")

with h1:
    render_highlight_card(
        "Hipótesis 1 — Longitud",
        "✅ Confirmada",
        "Las reseñas más largas son percibidas como más útiles. "
        "El feature review_len es la variable más importante del modelo.",
    )
with h2:
    render_highlight_card(
        "Hipótesis 2 — Coherencia",
        "✅ Confirmada",
        "Una nota baja con texto positivo (o viceversa) reduce la credibilidad. "
        "El flag de incoherencia penaliza la predicción de utilidad.",
    )
with h3:
    render_highlight_card(
        "Hipótesis 3 — Sentimiento",
        "✅ Parcialmente confirmada",
        "El sentimiento (VADER) contribuye, pero tiene menos peso que la longitud. "
        "El extremo positivo sin detalle específico no garantiza utilidad.",
    )

# ── Distribuciones visuales ───────────────────────────────────────────────────

st.markdown("### Distribuciones del Dataset")
left_col, right_col = st.columns(2, gap="large")
with left_col:
    st.subheader("Calificaciones en estrellas")
    st.caption("La mayoría de reseñas tienen 4–5 estrellas, lo que genera desbalance de clases.")
    st.plotly_chart(build_stars_distribution(reviews), use_container_width=True)
with right_col:
    st.subheader("Longitud de las reseñas")
    st.caption("La distribución está sesgada a la derecha — pocas reseñas son muy largas.")
    st.plotly_chart(build_review_length_distribution(reviews), use_container_width=True)

# ── Modelo activo ──────────────────────────────────────────────────────────────

st.markdown("### Modelo Activo")
st.markdown(
    """
    <div class="accuracy-warning">
        <div class="aw-title">¿Por qué no usamos Accuracy como métrica?</div>
        <p>
            Si el 70 % de las reseñas fuera "no útil", un modelo que siempre predice "no útil"
            tendría 70 % de accuracy — sin aprender nada. Por eso usamos <strong>F1</strong>
            (equilibrio entre precisión y recall) y <strong>ROC-AUC</strong> (capacidad global
            de discriminación). Ambas métricas funcionan bien con clases desbalanceadas.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

ma1, ma2, ma3 = st.columns(3, gap="medium")
with ma1:
    render_metric_card("Modelo principal", "LightGBM", "Mayor ROC-AUC en la comparación")
with ma2:
    render_metric_card("Baseline", "Regresión Logística", "Referencia interpretable del caso")
with ma3:
    render_metric_card("Features del modelo", "4 variables", "Score, sentimiento, longitud, coherencia")