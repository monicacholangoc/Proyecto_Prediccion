"""Resumen ejecutivo."""
import streamlit as st
from shared_sidebar import render_sidebar
from components.cards import render_metric_card
from services.data_loader import load_processed_reviews
from services.feature_service import add_basic_text_features
from plots.eda_charts import build_stars_distribution, build_review_length_distribution
from utils.formatters import format_compact_number, format_percentage

with open("styles/styles.css", "r", encoding="utf-8") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
render_sidebar()

st.title("Resumen Ejecutivo")
st.caption("Indicadores del dataset, hipótesis verificadas y distribuciones clave.")

reviews      = add_basic_text_features(load_processed_reviews())
has_reviews  = not reviews.empty

useful_ratio   = float(reviews["y_util"].mean()) if has_reviews and "y_util" in reviews.columns else 0.0
avg_length     = int(reviews["review_len"].fillna(0).mean()) if has_reviews and "review_len" in reviews.columns else 0

st.markdown('<div class="section-label">Calidad del pipeline de datos</div>', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="stat-row">
        <div class="stat-pill">
            <div class="stat-pill-icon stat-pill-icon-blue">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/></svg>
            </div>
            <div><div class="stat-pill-value">568.454</div><div class="stat-pill-label">Reseñas originales</div></div>
        </div>
        <div class="stat-pill">
            <div class="stat-pill-icon stat-pill-icon-amber">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b45309" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
            </div>
            <div><div class="stat-pill-value">174.918</div><div class="stat-pill-label">Duplicados eliminados</div></div>
        </div>
        <div class="stat-pill">
            <div class="stat-pill-icon stat-pill-icon-teal">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            </div>
            <div><div class="stat-pill-value">{format_compact_number(len(reviews)) if has_reviews else '—'}</div><div class="stat-pill-label">Base analítica final (≥ 5 votos)</div></div>
        </div>
        <div class="stat-pill">
            <div class="stat-pill-icon stat-pill-icon-green">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#15803d" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
            <div><div class="stat-pill-value">14</div><div class="stat-pill-label">Nulos eliminados</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True,
)

st.markdown('<div class="section-label">Indicadores clave del dataset</div>', unsafe_allow_html=True)
k1, k2, k3 = st.columns(3, gap="medium")
with k1: render_metric_card("Reseñas útiles (≥ 0.70)", format_percentage(useful_ratio), "Proporción de la variable objetivo — confirma el desbalance de clases")
with k2: render_metric_card("Longitud media", f"{avg_length} palabras", "Feature #1 del modelo — las reseñas largas tienden a ser más útiles")
with k3: render_metric_card("Desbalance de clases", f"{format_percentage(1 - useful_ratio)} no útiles", "Justifica usar F1 y ROC-AUC en lugar de Accuracy")

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
            f"""<div class="highlight-card">
                <div class="highlight-title">Hipótesis — {title}</div>
                <span class="metric-badge {badge_class}" style="margin-bottom:0.5rem;display:inline-block">{result}</span>
                <div class="highlight-body">{body}</div>
            </div>""", unsafe_allow_html=True,
        )

st.markdown('<div class="section-label">Distribuciones clave</div>', unsafe_allow_html=True)
lc, rc = st.columns(2, gap="large")
with lc:
    st.caption("**Calificaciones** — El 63 % de las reseñas tienen 4–5 estrellas. Esta concentración genera desbalance de clases y es la razón principal por la que Accuracy no es una métrica válida aquí.")
    st.plotly_chart(build_stars_distribution(reviews), use_container_width=True)
with rc:
    fig2 = build_review_length_distribution(reviews)
    if avg_length > 0:
        fig2.add_vline(x=avg_length, line_dash="dash", line_color="#0f9f74",
                       annotation_text=f"Media: {avg_length} palabras", annotation_position="top right")
    st.caption("**Longitud** — La distribución es asimétrica: pocas reseñas son muy largas, pero son consistentemente las más útiles. Esto confirma la hipótesis H1 del caso.")
    st.plotly_chart(fig2, use_container_width=True)