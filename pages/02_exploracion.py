"""Exploración de datos — indicadores en tarjetas, filtros, gráficos clave."""

import pandas as pd
import streamlit as st

from components.cards import render_metric_card
from plots.eda_charts import (
    build_correlation_heatmap,
    build_helpfulness_distribution,
    build_incoherence_distribution,
    build_length_vs_helpfulness,
    build_review_length_distribution,
    build_stars_distribution,
    build_stars_vs_helpfulness,
    build_sentiment_vs_score,
    build_target_balance,
)
from services.catalog_service import map_product_metadata
from services.data_loader import load_processed_reviews
from services.feature_service import add_basic_text_features
from services.preprocessing_service import get_corporate_audit_db
from utils.formatters import format_compact_number, format_percentage


def load_css() -> None:
    with open("styles/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def _render_logo() -> str:
    return """
    <svg class="sidebar-logo-svg" width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="38" height="38" rx="10" fill="url(#lg1e)"/>
      <path d="M10 26 L19 12 L28 26 Z" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.5)" stroke-width="1.2"/>
      <path d="M14 26 L19 17 L24 26 Z" fill="rgba(255,255,255,0.9)"/>
      <circle cx="19" cy="11" r="2.5" fill="#7dd3fc"/>
      <defs>
        <linearGradient id="lg1e" x1="0" y1="0" x2="38" y2="38" gradientUnits="userSpaceOnUse">
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

st.title("Exploración de Datos")
st.caption("Análisis exploratorio con filtros interactivos sobre las variables clave del modelo.")

reviews  = add_basic_text_features(load_processed_reviews())
fallback = add_basic_text_features(
    get_corporate_audit_db().rename(columns={"Stars": "Score", "Text": "Text"})
)
source = reviews if not reviews.empty else fallback
source = map_product_metadata(source)

if "Helpfulness" not in source.columns:
    if "HelpfulnessNumerator" in source.columns and "HelpfulnessDenominator" in source.columns:
        denom = source["HelpfulnessDenominator"].replace(0, pd.NA)
        source["Helpfulness"] = (source["HelpfulnessNumerator"] / denom).fillna(0)
    elif "y_util" in source.columns:
        source["Helpfulness"] = source["y_util"].astype(float)

score_col       = "Score" if "Score" in source.columns else ("Stars" if "Stars" in source.columns else None)
category_col    = "Categoria_Real" if "Categoria_Real" in source.columns else None
helpfulness_col = "Helpfulness" if "Helpfulness" in source.columns else None

# ── Filtros ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Filtros</div>', unsafe_allow_html=True)
f1, f2, f3, f4 = st.columns(4, gap="medium")
with f1:
    score_opts = ["Todas"] + ([str(x) for x in sorted(source[score_col].dropna().astype(int).unique())] if score_col else [])
    sel_score = st.selectbox("Estrellas", options=score_opts)
with f2:
    cat_opts = ["Todas"] + (sorted(source[category_col].dropna().astype(str).unique().tolist()) if category_col else [])
    sel_cat = st.selectbox("Categoría", options=cat_opts)
with f3:
    min_l = int(source["review_len"].min()) if "review_len" in source.columns and not source.empty else 0
    max_l = int(source["review_len"].max()) if "review_len" in source.columns and not source.empty else 500
    max_l = max_l if max_l > min_l else min_l + 1
    sel_len = st.slider("Rango de longitud", min_value=min_l, max_value=max_l, value=(min_l, max_l))
with f4:
    sel_util = st.selectbox("Utilidad", options=["Todas", "Útiles (≥ 0.70)", "No útiles (< 0.70)"])

df = source.copy()
if score_col and sel_score != "Todas":
    df = df[df[score_col].astype(str) == sel_score]
if category_col and sel_cat != "Todas":
    df = df[df[category_col] == sel_cat]
if "review_len" in df.columns:
    df = df[df["review_len"].between(sel_len[0], sel_len[1])]
if helpfulness_col and sel_util != "Todas":
    df = df[df[helpfulness_col] >= 0.70] if "Útiles" in sel_util else df[df[helpfulness_col] < 0.70]

# ── Indicadores del corte ──────────────────────────────────────────────────────
n        = len(df)
products = int(df["ProductId"].astype(str).nunique()) if "ProductId" in df.columns else 0
ratio    = float(df[helpfulness_col].ge(0.70).mean()) if helpfulness_col and n > 0 else 0.0
avg_len  = int(df["review_len"].fillna(0).mean()) if "review_len" in df.columns and n > 0 else 0

st.markdown('<div class="section-label">Indicadores del corte</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4, gap="medium")
with c1:
    render_metric_card("Reseñas", format_compact_number(n), "Tras aplicar los filtros")
with c2:
    render_metric_card("Productos únicos", format_compact_number(products), "Cobertura del subconjunto")
with c3:
    render_metric_card("Ratio de útiles", format_percentage(ratio), "Utilidad ≥ 0.70")
with c4:
    render_metric_card("Longitud media", f"{avg_len} palabras", "Feature #1 del modelo")

# ── Distribuciones ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Distribuciones</div>', unsafe_allow_html=True)
d1, d2 = st.columns(2, gap="large")
with d1:
    st.caption("**Calificaciones** — Concentración en 4–5 estrellas genera desbalance.")
    st.plotly_chart(build_stars_distribution(df), use_container_width=True)
with d2:
    st.caption("**Longitud** — Distribución sesgada; las reseñas largas son minoría y más útiles.")
    st.plotly_chart(build_review_length_distribution(df), use_container_width=True)

d3, d4 = st.columns(2, gap="large")
with d3:
    st.caption("**Utilidad observada** — Muchos valores en 0 o 1, sin intermedios.")
    st.plotly_chart(build_helpfulness_distribution(df), use_container_width=True)
with d4:
    st.caption("**Variable objetivo** — El desbalance justifica usar F1 en lugar de Accuracy.")
    st.plotly_chart(build_target_balance(df), use_container_width=True)

# ── Relaciones ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Relaciones con la utilidad</div>', unsafe_allow_html=True)
r1, r2 = st.columns(2, gap="large")
with r1:
    st.caption("**Estrellas vs. utilidad** — Las 3 estrellas tienen mayor dispersión.")
    st.plotly_chart(build_stars_vs_helpfulness(df), use_container_width=True)
with r2:
    st.caption("**Longitud vs. utilidad** — Relación más fuerte del dataset.")
    st.plotly_chart(build_length_vs_helpfulness(df), use_container_width=True)

r3, r4 = st.columns(2, gap="large")
with r3:
    st.caption("**Sentimiento por estrellas** — Las 5 estrellas tienen mayor varianza.")
    st.plotly_chart(build_sentiment_vs_score(df), use_container_width=True)
with r4:
    st.caption("**Coherencia texto-estrellas** — Subgrupo pequeño pero relevante.")
    st.plotly_chart(build_incoherence_distribution(df), use_container_width=True)

# ── Correlación ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Correlación entre variables</div>', unsafe_allow_html=True)
st.plotly_chart(build_correlation_heatmap(df), use_container_width=True)