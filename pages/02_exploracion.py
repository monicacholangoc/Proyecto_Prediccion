"""Pagina base del EDA.

Por ahora usa las funciones de graficos y datos centralizados; en la
siguiente fase creceremos esta vista con mas analisis y narrativa.
"""

import pandas as pd
import streamlit as st

from components.cards import render_metric_card
from plots.eda_charts import (
    build_category_distribution,
    build_correlation_heatmap,
    build_helpfulness_distribution,
    build_incoherence_distribution,
    build_length_vs_helpfulness,
    build_metric_summary_bar,
    build_review_length_distribution,
    build_stars_distribution,
    build_stars_vs_helpfulness,
    build_sentiment_distribution,
    build_sentiment_vs_score,
    build_target_balance,
)
from services.catalog_service import map_product_metadata
from services.data_loader import load_processed_reviews
from services.feature_service import add_basic_text_features
from services.preprocessing_service import get_corporate_audit_db
from utils.formatters import format_compact_number, format_percentage


st.title("Exploración de Datos")
st.caption("EDA estructurado con filtros, bloques visuales y narrativa analítica más clara.")

st.markdown(
    """
    <div class="insight-panel">
        <div class="insight-title">¿Qué explorar aquí?</div>
        <p>
            Este análisis responde tres preguntas clave: ¿cómo se distribuyen las calificaciones?
            ¿qué longitud tienen las reseñas útiles vs las no útiles? ¿hay coherencia entre
            el sentimiento del texto y la nota en estrellas? Usa los filtros para explorar
            subgrupos específicos.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

reviews = add_basic_text_features(load_processed_reviews())
fallback_reviews = add_basic_text_features(
    get_corporate_audit_db().rename(columns={"Stars": "Score", "Text": "Text"})
)
# Si no hay parquet procesado disponible, la pagina sigue viva con la base operativa.
source_reviews = reviews if not reviews.empty else fallback_reviews
source_reviews = map_product_metadata(source_reviews)

if "Helpfulness" not in source_reviews.columns:
    if "HelpfulnessNumerator" in source_reviews.columns and "HelpfulnessDenominator" in source_reviews.columns:
        denominator = source_reviews["HelpfulnessDenominator"].replace(0, pd.NA)
        source_reviews["Helpfulness"] = (
            source_reviews["HelpfulnessNumerator"] / denominator
        ).fillna(0)
    elif "y_util" in source_reviews.columns:
        source_reviews["Helpfulness"] = source_reviews["y_util"].astype(float)

score_column = "Score" if "Score" in source_reviews.columns else "Stars" if "Stars" in source_reviews.columns else None
category_column = "Categoria_Real" if "Categoria_Real" in source_reviews.columns else None
helpfulness_column = "Helpfulness" if "Helpfulness" in source_reviews.columns else None

st.markdown("### Panel de Exploración")
filter_cols = st.columns(4, gap="medium")

with filter_cols[0]:
    score_options = ["Todas"]
    if score_column:
        score_options += [str(x) for x in sorted(source_reviews[score_column].dropna().astype(int).unique().tolist())]
    selected_score = st.selectbox("Filtrar por estrellas", options=score_options)

with filter_cols[1]:
    category_options = ["Todas"]
    if category_column:
        category_options += sorted(source_reviews[category_column].dropna().astype(str).unique().tolist())
    selected_category = st.selectbox("Filtrar por categoría", options=category_options)

with filter_cols[2]:
    min_length = int(source_reviews["review_len"].min()) if not source_reviews.empty and "review_len" in source_reviews.columns else 0
    max_length = int(source_reviews["review_len"].max()) if not source_reviews.empty and "review_len" in source_reviews.columns else 200
    selected_length = st.slider(
        "Rango de longitud",
        min_value=min_length,
        max_value=max_length if max_length > min_length else min_length + 1,
        value=(min_length, max_length if max_length > min_length else min_length + 1),
    )

with filter_cols[3]:
    selected_usefulness = st.selectbox(
        "Filtrar por utilidad",
        options=["Todas", "Utiles (>= 0.70)", "No utiles (< 0.70)"],
    )

filtered_reviews = source_reviews.copy()
if score_column and selected_score != "Todas":
    filtered_reviews = filtered_reviews[filtered_reviews[score_column].astype(str) == selected_score]
if category_column and selected_category != "Todas":
    filtered_reviews = filtered_reviews[filtered_reviews[category_column] == selected_category]
if "review_len" in filtered_reviews.columns:
    filtered_reviews = filtered_reviews[
        filtered_reviews["review_len"].between(selected_length[0], selected_length[1])
    ]
if helpfulness_column and selected_usefulness != "Todas":
    if "Utiles" in selected_usefulness:
        filtered_reviews = filtered_reviews[filtered_reviews[helpfulness_column] >= 0.70]
    else:
        filtered_reviews = filtered_reviews[filtered_reviews[helpfulness_column] < 0.70]

sample_size = len(filtered_reviews)
useful_ratio = (
    float(filtered_reviews[helpfulness_column].ge(0.70).mean())
    if helpfulness_column and not filtered_reviews.empty
    else 0.0
)
avg_length = (
    int(filtered_reviews["review_len"].fillna(0).mean())
    if "review_len" in filtered_reviews.columns and not filtered_reviews.empty
    else 0
)
distinct_products = (
    int(filtered_reviews["ProductId"].astype(str).nunique())
    if "ProductId" in filtered_reviews.columns and not filtered_reviews.empty
    else 0
)

metric_cols = st.columns(4, gap="medium")
with metric_cols[0]:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Reseñas en el corte actual</div>
            <div class="metric-value">{format_compact_number(sample_size)}</div>
            <div class="metric-caption">Registros visibles tras aplicar los filtros seleccionados.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with metric_cols[1]:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Productos únicos</div>
            <div class="metric-value">{format_compact_number(distinct_products)}</div>
            <div class="metric-caption">Cobertura de productos en el subconjunto filtrado.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with metric_cols[2]:
    _badge_class = "metric-badge-good" if useful_ratio >= 0.40 else "metric-badge-warn"
    _label_util = "Proporción sana" if useful_ratio >= 0.40 else "Desbalance detectado"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Ratio de reseñas útiles</div>
            <div class="metric-value">{format_percentage(useful_ratio)}</div>
            <div class="metric-caption">Reseñas con utilidad ≥ 0.70 sobre el total visible.</div>
            <span class="metric-badge {_badge_class}">{_label_util}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with metric_cols[3]:
    _badge_len = "metric-badge-good" if avg_length > 60 else "metric-badge-warn"
    _label_len = "Longitud útil" if avg_length > 60 else "Reseñas cortas"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Longitud media</div>
            <div class="metric-value">{avg_length} palabras</div>
            <div class="metric-caption">Promedio del subconjunto. Feature clave del modelo.</div>
            <span class="metric-badge {_badge_len}">{_label_len}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown("### Distribuciones Principales")
dist_left, dist_right = st.columns(2, gap="large")
with dist_left:
    st.plotly_chart(build_stars_distribution(filtered_reviews), use_container_width=True)
with dist_right:
    st.plotly_chart(build_review_length_distribution(filtered_reviews), use_container_width=True)

mid_left, mid_right = st.columns(2, gap="large")
with mid_left:
    st.plotly_chart(build_helpfulness_distribution(filtered_reviews), use_container_width=True)
with mid_right:
    st.plotly_chart(build_category_distribution(filtered_reviews), use_container_width=True)

extra_left, extra_right = st.columns(2, gap="large")
with extra_left:
    st.plotly_chart(build_target_balance(filtered_reviews), use_container_width=True)
with extra_right:
    st.plotly_chart(build_sentiment_distribution(filtered_reviews), use_container_width=True)

st.markdown("### Relaciones Relevantes")
rel_left, rel_right = st.columns(2, gap="large")
with rel_left:
    st.plotly_chart(build_stars_vs_helpfulness(filtered_reviews), use_container_width=True)
with rel_right:
    st.plotly_chart(build_length_vs_helpfulness(filtered_reviews), use_container_width=True)

sent_left, sent_right = st.columns(2, gap="large")
with sent_left:
    st.plotly_chart(build_sentiment_vs_score(filtered_reviews), use_container_width=True)
with sent_right:
    st.plotly_chart(build_incoherence_distribution(filtered_reviews), use_container_width=True)

summary_items = [
    ("Registros", float(sample_size)),
    ("Productos", float(distinct_products)),
    ("Ratio util", useful_ratio * 100),
    ("Longitud media", float(avg_length)),
]
st.plotly_chart(build_metric_summary_bar(summary_items), use_container_width=True)

st.markdown("### Correlaciones y Lectura de Features")
st.plotly_chart(build_correlation_heatmap(filtered_reviews), use_container_width=True)