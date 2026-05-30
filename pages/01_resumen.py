"""Resumen ejecutivo del proyecto.

Indicadores compactos: solo título + valor + caption breve.
Sin emojis, sin texto de relleno, sin badges redundantes.
"""

import streamlit as st

from components.cards import render_metric_card
from services.catalog_service import get_product_catalog
from services.data_loader import load_processed_reviews
from services.feature_service import add_basic_text_features
from plots.eda_charts import build_stars_distribution, build_review_length_distribution
from services.preprocessing_service import get_corporate_audit_db
from utils.formatters import format_compact_number, format_percentage


st.title("Resumen Ejecutivo")
st.caption("Indicadores del dataset, hipótesis verificadas y pipeline de datos aplicado.")

reviews      = add_basic_text_features(load_processed_reviews())
catalog      = get_product_catalog()
corporate_db = get_corporate_audit_db()
has_reviews  = not reviews.empty

# ── Indicadores ────────────────────────────────────────────────────────────────

useful_ratio = (
    float(reviews["y_util"].mean())
    if has_reviews and "y_util" in reviews.columns
    else float(corporate_db["Helpfulness"].ge(0.70).mean()) if not corporate_db.empty
    else 0.0
)
avg_length = (
    int(reviews["review_len"].fillna(0).mean())
    if has_reviews and "review_len" in reviews.columns
    else 0
)
approved_ratio = (
    float(corporate_db["Estado"].eq("APROBADA (Publicada)").mean())
    if not corporate_db.empty else 0.0
)

# ── Pregunta de negocio ────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="insight-panel">
        <div class="insight-title">Pregunta de negocio</div>
        <p>
            ¿Qué hace que una reseña sea percibida como útil por otros compradores?
            La utilidad no depende solo de las estrellas — depende de la <strong>longitud</strong>,
            el <strong>sentimiento</strong> del texto y la <strong>coherencia</strong> entre ambos.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Dataset ────────────────────────────────────────────────────────────────────

st.markdown("### Dataset")
m1, m2, m3, m4 = st.columns(4, gap="medium")
with m1:
    render_metric_card("Dataset original", "568.454", "Reseñas en bruto")
with m2:
    render_metric_card(
        "Base analítica",
        format_compact_number(len(reviews)) if has_reviews else "—",
        "Con ≥ 5 votos, sin duplicados",
    )
with m3:
    render_metric_card("Catálogo", format_compact_number(len(catalog)), "Productos con categoría")
with m4:
    render_metric_card(
        "Base operativa",
        format_compact_number(len(corporate_db)),
        "Registros para auditoría",
    )

# ── Indicadores clave ──────────────────────────────────────────────────────────

st.markdown("### Indicadores clave")
k1, k2, k3 = st.columns(3, gap="medium")

with k1:
    render_metric_card(
        "Reseñas útiles (≥ 0.70)",
        format_percentage(useful_ratio),
        "Variable objetivo del modelo binario",
    )

with k2:
    render_metric_card(
        "Longitud media",
        f"{avg_length} palabras",
        "Feature #1 del modelo predictivo",
    )

with k3:
    render_metric_card(
        "Reseñas aprobadas",
        format_percentage(approved_ratio),
        "Clasificadas como publicadas en la base corporativa",
    )

# ── Hipótesis verificadas ──────────────────────────────────────────────────────

st.markdown("### Hipótesis verificadas")
h1, h2, h3 = st.columns(3, gap="medium")

hypotheses = [
    (
        "Hipótesis 1 — Longitud",
        "Confirmada",
        "confirmed",
        "Las reseñas más largas son más útiles. <code>review_len</code> es el feature de mayor peso en el modelo.",
    ),
    (
        "Hipótesis 2 — Coherencia",
        "Confirmada",
        "confirmed",
        "Un texto positivo con nota baja activa el flag <code>incoherente</code> y penaliza la predicción.",
    ),
    (
        "Hipótesis 3 — Sentimiento",
        "Parcial",
        "partial",
        "VADER contribuye al modelo, pero con menor peso que la longitud. El tono positivo solo no garantiza utilidad.",
    ),
]

status_styles = {
    "confirmed": ("metric-badge-good", "Confirmada"),
    "partial":   ("metric-badge-warn", "Parcial"),
}

for col, (title, _, status_key, body) in zip([h1, h2, h3], hypotheses):
    badge_class, badge_label = status_styles[status_key]
    with col:
        st.markdown(
            f"""
            <div class="highlight-card">
                <div class="highlight-title">{title}</div>
                <span class="metric-badge {badge_class}" style="margin-bottom:0.5rem;display:inline-block">{badge_label}</span>
                <div class="highlight-body">{body}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Distribuciones ─────────────────────────────────────────────────────────────

st.markdown("### Distribuciones del dataset")
st.caption(
    "Izquierda: concentración en 4–5 estrellas genera desbalance de clases. "
    "Derecha: distribución sesgada — pocas reseñas son muy largas y suelen ser las más útiles."
)

left_col, right_col = st.columns(2, gap="large")
with left_col:
    fig = build_stars_distribution(reviews)
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    fig2 = build_review_length_distribution(reviews)
    fig2.add_vline(
        x=avg_length, line_dash="dash", line_color="#0f9f74",
        annotation_text=f"Media: {avg_length} palabras",
        annotation_position="top right",
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Pipeline de datos ──────────────────────────────────────────────────────────

st.markdown("### Pipeline de datos")
st.markdown(
    """
    <div class="info-panel">
        <strong>Pasos reproducibles</strong>
        <ul class="info-list">
            <li>Filtro de calidad: <code>HelpfulnessDenominator ≥ 5</code> — elimina tasas poco representativas</li>
            <li>Deduplicación: <code>drop_duplicates(subset=['UserId', 'ProductId', 'Time'])</code></li>
            <li>Variable objetivo: tasa ≥ 0.70 → útil (1), menor → no útil (0)</li>
            <li>Features: longitud en palabras, sentimiento VADER, coherencia texto-estrellas</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)