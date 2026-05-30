"""Resumen ejecutivo — todo en tarjetas, sin texto de relleno."""

import streamlit as st

from components.cards import render_metric_card
from services.catalog_service import get_product_catalog
from services.data_loader import load_processed_reviews
from services.feature_service import add_basic_text_features
from plots.eda_charts import build_stars_distribution, build_review_length_distribution
from services.preprocessing_service import get_corporate_audit_db
from utils.formatters import format_compact_number, format_percentage
import os


def load_css() -> None:
    with open("styles/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def _render_logo() -> str:
    return """
    <svg class="sidebar-logo-svg" width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="38" height="38" rx="10" fill="url(#lg1r)"/>
      <path d="M10 26 L19 12 L28 26 Z" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.5)" stroke-width="1.2"/>
      <path d="M14 26 L19 17 L24 26 Z" fill="rgba(255,255,255,0.9)"/>
      <circle cx="19" cy="11" r="2.5" fill="#7dd3fc"/>
      <defs>
        <linearGradient id="lg1r" x1="0" y1="0" x2="38" y2="38" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#1e3a8a"/>
          <stop offset="100%" stop-color="#0f4c5c"/>
        </linearGradient>
      </defs>
    </svg>
    """


load_css()

with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-logo-wrap">
            {_render_logo()}
            <div>
                <div class="sidebar-logo-text-main">Seminario<br>Predictivo</div>
                <div class="sidebar-logo-text-sub">Caso 06 · Amazon Reviews</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="sidebar-panel">
            <div class="sidebar-panel-title">Navegación</div>
            <div class="sidebar-panel-item">1. Resumen Ejecutivo</div>
            <div class="sidebar-panel-item">2. Exploración de Datos</div>
            <div class="sidebar-panel-item">3. Modelos y Evaluación</div>
            <div class="sidebar-panel-item">4. Auditoría en Tiempo Real</div>
            <div class="sidebar-panel-item">5. Ranking y Benchmark</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.title("Resumen Ejecutivo")
st.caption("Indicadores del dataset, hipótesis verificadas y distribuciones clave.")

reviews      = add_basic_text_features(load_processed_reviews())
catalog      = get_product_catalog()
corporate_db = get_corporate_audit_db()
has_reviews  = not reviews.empty

useful_ratio = (
    float(reviews["y_util"].mean())
    if has_reviews and "y_util" in reviews.columns
    else float(corporate_db["Helpfulness"].ge(0.70).mean()) if not corporate_db.empty else 0.0
)
avg_length = (
    int(reviews["review_len"].fillna(0).mean())
    if has_reviews and "review_len" in reviews.columns else 0
)
approved_ratio = (
    float(corporate_db["Estado"].eq("APROBADA (Publicada)").mean())
    if not corporate_db.empty else 0.0
)

# ── Dataset ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Dataset</div>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4, gap="medium")
with m1:
    render_metric_card("Dataset original", "568.454", "Reseñas en bruto")
with m2:
    render_metric_card("Base analítica", format_compact_number(len(reviews)) if has_reviews else "—", "Con ≥ 5 votos, sin duplicados")
with m3:
    render_metric_card("Catálogo", format_compact_number(len(catalog)), "Productos con categoría")
with m4:
    render_metric_card("Base operativa", format_compact_number(len(corporate_db)), "Registros para auditoría")

# ── Indicadores clave ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Indicadores clave</div>', unsafe_allow_html=True)
k1, k2, k3 = st.columns(3, gap="medium")
with k1:
    render_metric_card("Reseñas útiles (≥ 0.70)", format_percentage(useful_ratio), "Variable objetivo del modelo")
with k2:
    render_metric_card("Longitud media", f"{avg_length} palabras", "Feature #1 del modelo predictivo")
with k3:
    render_metric_card("Reseñas aprobadas", format_percentage(approved_ratio), "Clasificadas como publicadas")

# ── Hipótesis ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Hipótesis verificadas</div>', unsafe_allow_html=True)
h1, h2, h3 = st.columns(3, gap="medium")

hypotheses = [
    ("Longitud",    "Confirmada", "metric-badge-good", "Las reseñas más largas son más útiles. <code>review_len</code> es el feature de mayor peso."),
    ("Coherencia",  "Confirmada", "metric-badge-good", "La incoherencia tono-estrellas activa <code>incoherente</code> y penaliza la predicción."),
    ("Sentimiento", "Parcial",    "metric-badge-warn",  "VADER contribuye, pero con menor peso que la longitud."),
]
for col, (title, result, badge_class, body) in zip([h1, h2, h3], hypotheses):
    with col:
        st.markdown(
            f"""
            <div class="highlight-card">
                <div class="highlight-title">Hipótesis — {title}</div>
                <span class="metric-badge {badge_class}" style="margin-bottom:0.5rem;display:inline-block">{result}</span>
                <div class="highlight-body">{body}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Distribuciones ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Distribuciones</div>', unsafe_allow_html=True)
left_col, right_col = st.columns(2, gap="large")
with left_col:
    st.caption("**Calificaciones** — Concentración en 4–5 estrellas genera desbalance de clases.")
    st.plotly_chart(build_stars_distribution(reviews), use_container_width=True)
with right_col:
    fig2 = build_review_length_distribution(reviews)
    if avg_length > 0:
        fig2.add_vline(x=avg_length, line_dash="dash", line_color="#0f9f74",
                       annotation_text=f"Media: {avg_length} palabras", annotation_position="top right")
    st.caption("**Longitud** — Pocas reseñas son muy largas; suelen ser las más útiles.")
    st.plotly_chart(fig2, use_container_width=True)