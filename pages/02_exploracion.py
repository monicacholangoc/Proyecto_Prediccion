"""Exploración de datos."""
# ── Guard: redirige a main.py si se accede directamente sin sesión ──────────
try:
    import streamlit as _st
    if not _st.session_state.get("app_initialized"):
        _st.switch_page("main.py")
except Exception:
    pass
# ────────────────────────────────────────────────────────────────────────────


import pandas as pd
import streamlit as st
from shared_sidebar import render_sidebar
from components.cards import render_metric_card
from plots.eda_charts import (build_correlation_heatmap, build_helpfulness_distribution,
    build_incoherence_distribution, build_length_vs_helpfulness, build_review_length_distribution,
    build_stars_distribution, build_stars_vs_helpfulness, build_sentiment_vs_score, build_target_balance)
from services.catalog_service import map_product_metadata
from services.data_loader import load_processed_reviews
from services.feature_service import add_basic_text_features
from services.preprocessing_service import get_corporate_audit_db
from utils.formatters import format_compact_number, format_percentage

with open("styles/styles.css", "r", encoding="utf-8") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
render_sidebar()

st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #16213b 0%, #1746a2 60%, #0f4c5c 100%);
        border-radius: 16px;
        padding: 1.4rem 2rem;
        margin-bottom: 1.4rem;
        color: #ffffff;
    ">
        <div style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                    color:rgba(255,255,255,0.55);text-transform:uppercase;margin-bottom:0.35rem">
            Seminario Predictivo 2026 · Caso 06
        </div>
        <div style="font-size:clamp(1.4rem,3vw,1.9rem);font-weight:800;
                    letter-spacing:-0.02em;line-height:1.2;margin-bottom:0.3rem">
            Exploración de Datos
        </div>
        <div style="font-size:0.82rem;color:rgba(255,255,255,0.65)">Análisis exploratorio con filtros interactivos sobre las variables clave del modelo</div>
    </div>
    """,
    unsafe_allow_html=True,
)


reviews  = add_basic_text_features(load_processed_reviews())
fallback = add_basic_text_features(get_corporate_audit_db().rename(columns={"Stars": "Score"}))
source   = reviews if not reviews.empty else fallback
source   = map_product_metadata(source)

if "Helpfulness" not in source.columns:
    if "HelpfulnessNumerator" in source.columns and "HelpfulnessDenominator" in source.columns:
        source["Helpfulness"] = (source["HelpfulnessNumerator"] / source["HelpfulnessDenominator"].replace(0, pd.NA)).fillna(0)
    elif "y_util" in source.columns:
        source["Helpfulness"] = source["y_util"].astype(float)

score_col       = "Score" if "Score" in source.columns else ("Stars" if "Stars" in source.columns else None)
category_col    = "Categoria_Real" if "Categoria_Real" in source.columns else None
helpfulness_col = "Helpfulness" if "Helpfulness" in source.columns else None

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
if score_col and sel_score != "Todas":       df = df[df[score_col].astype(str) == sel_score]
if category_col and sel_cat != "Todas":      df = df[df[category_col] == sel_cat]
if "review_len" in df.columns:               df = df[df["review_len"].between(sel_len[0], sel_len[1])]
if helpfulness_col and sel_util != "Todas":  df = df[df[helpfulness_col] >= 0.70] if "Útiles" in sel_util else df[df[helpfulness_col] < 0.70]

n       = len(df)
products= int(df["ProductId"].astype(str).nunique()) if "ProductId" in df.columns else 0
ratio   = float(df[helpfulness_col].ge(0.70).mean()) if helpfulness_col and n > 0 else 0.0
avg_len = int(df["review_len"].fillna(0).mean()) if "review_len" in df.columns and n > 0 else 0

st.markdown('<div class="section-label">Indicadores del corte</div>', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="stat-row">
        <div class="stat-pill"><div class="stat-pill-icon stat-pill-icon-blue"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/></svg></div><div><div class="stat-pill-value">{format_compact_number(n)}</div><div class="stat-pill-label">Reseñas en corte</div></div></div>
        <div class="stat-pill"><div class="stat-pill-icon stat-pill-icon-teal"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2" stroke-linecap="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/></svg></div><div><div class="stat-pill-value">{format_compact_number(products)}</div><div class="stat-pill-label">Productos únicos</div></div></div>
        <div class="stat-pill"><div class="stat-pill-icon stat-pill-icon-green"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#15803d" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div><div><div class="stat-pill-value">{format_percentage(ratio)}</div><div class="stat-pill-label">Ratio de útiles</div></div></div>
        <div class="stat-pill"><div class="stat-pill-icon stat-pill-icon-amber"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b45309" stroke-width="2" stroke-linecap="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/></svg></div><div><div class="stat-pill-value">{avg_len} palabras</div><div class="stat-pill-label">Longitud media</div></div></div>
    </div>
    """, unsafe_allow_html=True,
)

st.markdown('<div class="section-label">Distribuciones</div>', unsafe_allow_html=True)
d1, d2 = st.columns(2, gap="large")
with d1:
    st.caption("**Calificaciones** — Concentración en 4–5 estrellas genera desbalance.")
    st.plotly_chart(build_stars_distribution(df), use_container_width=True)
with d2:
    st.caption("**Longitud** — Las reseñas largas son minoría y suelen ser más útiles.")
    st.plotly_chart(build_review_length_distribution(df), use_container_width=True)

d3, d4 = st.columns(2, gap="large")
with d3:
    st.caption("**Utilidad observada**")
    st.plotly_chart(build_helpfulness_distribution(df), use_container_width=True)
with d4:
    st.caption("**Variable objetivo** — Desbalance que justifica F1 sobre Accuracy.")
    st.plotly_chart(build_target_balance(df), use_container_width=True)

st.markdown('<div class="section-label">Relaciones con la utilidad</div>', unsafe_allow_html=True)
r1, r2 = st.columns(2, gap="large")
with r1:
    st.caption("**Estrellas vs. utilidad**")
    st.plotly_chart(build_stars_vs_helpfulness(df), use_container_width=True)
with r2:
    st.caption("**Longitud vs. utilidad** — Relación más fuerte del dataset.")
    st.plotly_chart(build_length_vs_helpfulness(df), use_container_width=True)

r3, r4 = st.columns(2, gap="large")
with r3:
    st.caption("**Sentimiento por estrellas**")
    st.plotly_chart(build_sentiment_vs_score(df), use_container_width=True)
with r4:
    st.caption("**Coherencia texto-estrellas**")
    st.plotly_chart(build_incoherence_distribution(df), use_container_width=True)

st.markdown('<div class="section-label">Correlación entre variables</div>', unsafe_allow_html=True)
st.plotly_chart(build_correlation_heatmap(df), use_container_width=True)