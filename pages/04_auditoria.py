"""Auditoría en tiempo real — características en tarjetas, sin texto de relleno."""

import os

import pandas as pd
import requests
import streamlit as st

from components.cards import render_metric_card, render_review_card
from components.feedback import render_status_panel
from plots.audit_charts import build_helpfulness_gauge
from services.catalog_service import get_product_detail, get_product_options
from services.ml_service import generate_review_recommendations
from services.preprocessing_service import (
    append_audited_review,
    get_product_benchmark,
    process_uploaded_audit_file,
    save_latest_review_to_file,
)
from utils.formatters import format_percentage
from utils.validators import is_non_empty_text


def load_css() -> None:
    with open("styles/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def _render_logo() -> str:
    return """
    <svg class="sidebar-logo-svg" width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="38" height="38" rx="10" fill="url(#lg1a)"/>
      <path d="M10 26 L19 12 L28 26 Z" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.5)" stroke-width="1.2"/>
      <path d="M14 26 L19 17 L24 26 Z" fill="rgba(255,255,255,0.9)"/>
      <circle cx="19" cy="11" r="2.5" fill="#7dd3fc"/>
      <defs>
        <linearGradient id="lg1a" x1="0" y1="0" x2="38" y2="38" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#1e3a8a"/>
          <stop offset="100%" stop-color="#0f4c5c"/>
        </linearGradient>
      </defs>
    </svg>
    """


def _api_url() -> str:
    try:
        return st.secrets["API_URL"].rstrip("/")
    except Exception:
        return os.getenv("API_URL", "https://proyecto-prediccion-v9qk.onrender.com").rstrip("/")


def _call_predict(review_text: str, stars: int) -> dict:
    try:
        r = requests.post(
            _api_url() + "/reviews/predict_helpfulness",
            json={"review_text": review_text, "stars": stars},
            timeout=35,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        return {"error": "Timeout — Render free tarda ~30 s en arrancar. Reintenta."}
    except Exception as exc:
        return {"error": str(exc)}


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

st.title("Auditoría en Tiempo Real")
st.caption("Ingresa una reseña para obtener su probabilidad de utilidad y el desglose de las 4 características calculadas.")

product_options = get_product_options()
if not product_options:
    st.warning("No hay productos disponibles en el catálogo.")
    st.stop()

left_col, right_col = st.columns([1.1, 1], gap="large")

with left_col:
    selected_product = st.selectbox("Producto", options=product_options)
    product_detail   = get_product_detail(selected_product)
    pd1, pd2 = st.columns(2)
    pd1.metric("Producto",  product_detail["ProductName"][:28])
    pd2.metric("Categoría", product_detail["Categoria_Real"][:22])

    validate_context = st.toggle("Validación de contexto / punto ciego", value=True)
    stars            = st.slider("Calificación en estrellas", min_value=1, max_value=5, value=5)
    user_name        = st.text_input("Perfil de usuario", value="Auditor_Seminario")
    review_text      = st.text_area("Texto de la reseña", height=200)
    analyze_btn      = st.button("Analizar reseña", type="primary")

    if analyze_btn:
        if not is_non_empty_text(review_text):
            st.warning("Ingresa una reseña antes de analizar.")
        else:
            with st.spinner("Consultando API..."):
                api_result = _call_predict(review_text.strip(), stars)
            if "error" not in api_result:
                st.session_state["_api_result"] = api_result
            else:
                st.error(f"API no disponible: {api_result['error']}")
                st.session_state["_api_result"] = None
            audit_result = append_audited_review(
                selected_product, user_name, stars,
                review_text.strip(), validate_context=validate_context,
            )
            st.session_state["latest_audit_result"] = audit_result

    st.markdown('<div class="section-label">Carga masiva</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("CSV con ProductId, ProfileName, Score, Text", type=["csv"])
    if st.button("Procesar lote CSV"):
        if uploaded_file is None:
            st.warning("Selecciona un archivo CSV antes de procesar.")
        else:
            batch_df, error_msg = process_uploaded_audit_file(uploaded_file)
            if error_msg:
                st.error(error_msg)
            else:
                st.success(f"Lote procesado: {len(batch_df)} reseñas agregadas.")
                st.dataframe(batch_df.head(20), use_container_width=True)

with right_col:
    latest_result = st.session_state.get("latest_audit_result")
    api_result    = st.session_state.get("_api_result")
    probability   = (
        api_result["probability"] if api_result and "error" not in api_result
        else (latest_result["probability"] if latest_result else 0.0)
    )

    st.plotly_chart(build_helpfulness_gauge(probability), use_container_width=True)

    if latest_result:
        if "Punto Ciego" in latest_result["status"]:
            tone, decision = "danger", "Revisión obligatoria"
        elif probability >= 0.70:
            tone, decision = "success", "Lista para publicar"
        else:
            tone, decision = "warning", "Conviene mejorarla"

        render_status_panel(
            "Diagnóstico", decision,
            f"Estado: {latest_result['status']} · Utilidad: {format_percentage(probability)}",
            tone=tone,
        )

        if latest_result.get("context_validation_enabled"):
            ctx  = ", ".join(latest_result["context_hits"]) or "ninguna"
            tech = ", ".join(latest_result["tech_hits"])    or "ninguno"
            c1, c2 = st.columns(2)
            c1.metric("Contexto detectado", ctx[:30])
            c2.metric("Términos ajenos", tech[:30])
    else:
        st.info("Introduce una reseña y presiona Analizar.")

# ── Características calculadas ─────────────────────────────────────────────────
st.markdown('<div class="section-label">Características calculadas</div>', unsafe_allow_html=True)

latest_result = st.session_state.get("latest_audit_result")
api_result    = st.session_state.get("_api_result")
probability   = (
    api_result["probability"] if api_result and "error" not in api_result
    else (latest_result["probability"] if latest_result else 0.0)
)

review_len  = latest_result["review_len"]  if latest_result else 0
incoherence = latest_result["incoherente"] if latest_result else False

sentiment_val = None
if api_result and "features" in api_result:
    sentiment_val = api_result["features"].get("sentiment_score")
elif api_result and "sentiment_score" in api_result:
    sentiment_val = api_result["sentiment_score"]

stars_val = st.session_state.get("latest_stars", 5)
f1, f2, f3, f4 = st.columns(4, gap="medium")

with f1:
    len_badge = "metric-badge-good" if review_len > 60 else "metric-badge-warn"
    len_label = "Adecuada" if review_len > 60 else "Muy corta"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Longitud</div>
            <div class="metric-value">{review_len} palabras</div>
            <div class="metric-caption">Umbral recomendado: ≥ 80 palabras</div>
            <span class="metric-badge {len_badge}">{len_label}</span>
        </div>
        """, unsafe_allow_html=True,
    )

with f2:
    filled = "&#9733;" * int(stars_val)
    empty  = "&#9734;" * max(0, 5 - int(stars_val))
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Calificación</div>
            <div class="metric-value" style="font-size:1.4rem;color:#f59e0b">{filled}{empty}</div>
            <div class="metric-caption">Estrellas asignadas por el usuario</div>
            <span class="metric-badge metric-badge-info">{stars_val} de 5</span>
        </div>
        """, unsafe_allow_html=True,
    )

with f3:
    if sentiment_val is not None:
        s_label   = "Positivo" if sentiment_val > 0.05 else ("Negativo" if sentiment_val < -0.05 else "Neutro")
        s_badge   = "metric-badge-good" if sentiment_val > 0.05 else ("metric-badge-warn" if sentiment_val < -0.05 else "metric-badge-info")
        s_display = f"{sentiment_val:.2f}"
    else:
        s_label, s_badge, s_display = "Pendiente", "metric-badge-info", "—"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Sentimiento VADER</div>
            <div class="metric-value">{s_display}</div>
            <div class="metric-caption">Score compuesto (−1 a +1)</div>
            <span class="metric-badge {s_badge}">{s_label}</span>
        </div>
        """, unsafe_allow_html=True,
    )

with f4:
    inc_badge = "metric-badge-warn" if incoherence else "metric-badge-good"
    inc_label = "Incoherente" if incoherence else "Coherente"
    inc_val   = "Sí" if incoherence else "No"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Coherencia</div>
            <div class="metric-value">{inc_val}</div>
            <div class="metric-caption">¿El tono contradice las estrellas?</div>
            <span class="metric-badge {inc_badge}">{inc_label}</span>
        </div>
        """, unsafe_allow_html=True,
    )

# ── Benchmark ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Benchmark del producto</div>', unsafe_allow_html=True)
product_benchmark = get_product_benchmark(selected_product)
b1, b2, b3, b4 = st.columns(4, gap="medium")
with b1:
    render_metric_card("Promedio del producto", format_percentage(product_benchmark["avg_helpfulness"]), "Utilidad media")
with b2:
    render_metric_card("Top del producto", format_percentage(product_benchmark["top_helpfulness"]), "Mejor score observado")
with b3:
    render_metric_card("Total reseñas", str(product_benchmark["count"]), "Historial del producto")
with b4:
    if latest_result:
        delta = latest_result["probability"] - product_benchmark["avg_helpfulness"]
        render_metric_card("vs. promedio", f"{delta:+.1%}", "Tu reseña vs. media del producto")

# ── Recomendaciones ────────────────────────────────────────────────────────────
if latest_result:
    recommendations = generate_review_recommendations(latest_result)
    st.markdown('<div class="section-label">Cómo mejorar esta reseña</div>', unsafe_allow_html=True)
    r1, r2 = st.columns(2, gap="large")
    with r1:
        st.markdown(
            f"""
            <div class="highlight-card">
                <div class="highlight-title">Acción principal</div>
                <div class="highlight-body">{recommendations[0]}</div>
            </div>
            """, unsafe_allow_html=True,
        )
    with r2:
        if len(recommendations) > 1:
            st.markdown(
                f"""
                <div class="highlight-card">
                    <div class="highlight-title">Acción adicional</div>
                    <div class="highlight-body">{recommendations[1]}</div>
                </div>
                """, unsafe_allow_html=True,
            )

    sv1, _ = st.columns([0.35, 0.65])
    with sv1:
        if st.button("Guardar reseña", use_container_width=True):
            ok, msg = save_latest_review_to_file(selected_product)
            (st.success if ok else st.warning)(msg)

    st.markdown('<div class="section-label">Vista previa</div>', unsafe_allow_html=True)
    render_review_card(
        user_name=user_name, stars=stars, review_text=review_text,
        meta_line=f"{product_detail['ProductName']} | {product_detail['Categoria_Real']} | {pd.Timestamp.now().strftime('%d/%m/%Y')}",
        badge=latest_result["status"],
        helpfulness=format_percentage(probability),
        highlighted=True,
    )

st.session_state["selected_product_id"] = selected_product
st.session_state["latest_stars"]        = stars
st.session_state["latest_review_text"]  = review_text