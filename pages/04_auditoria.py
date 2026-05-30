"""Auditoria en tiempo real.

Version simplificada:
- Gauge + desglose visual de los 4 features (lo que pide el caso)
- 3 metricas de resultado (no 7)
- Recomendacion + vista previa de la resena
- Sin historial operativo ni archivo de reseñas guardadas
"""

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


# ── API helpers ───────────────────────────────────────────────────────────────

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


def _get_api_status() -> dict:
    try:
        r = requests.get(_api_url() + "/", timeout=35)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"status": "error", "detalle": str(exc)}


# ── App ───────────────────────────────────────────────────────────────────────

st.title("Auditoría en Tiempo Real")
st.caption("Ingresa una reseña para obtener su probabilidad de utilidad y el desglose de las características calculadas.")

with st.sidebar:
    st.markdown("#### Estado API (Render)")
    with st.spinner("Verificando..."):
        api_status = _get_api_status()
    if api_status.get("status") == "ok":
        lgb_ok = "✓" in api_status.get("modelos", {}).get("lgb_model", "")
        st.success("API activa ✓")
        st.caption(f"LightGBM: {'✅ cargado' if lgb_ok else '⚠️ heurística'}")
    else:
        st.warning("⚠️ API no responde")
        st.caption(api_status.get("detalle", "")[:80])
    st.caption("proyecto-prediccion-v9qk.onrender.com")

product_options = get_product_options()
if not product_options:
    st.warning("No hay productos disponibles en el catálogo para auditar.")
    st.stop()

left_col, right_col = st.columns([1.1, 1], gap="large")

with left_col:
    selected_product = st.selectbox("Producto", options=product_options)
    product_detail   = get_product_detail(selected_product)
    pd1, pd2 = st.columns(2)
    pd1.metric("Producto",  product_detail["ProductName"][:28])
    pd2.metric("Categoría", product_detail["Categoria_Real"][:22])

    validate_context = st.toggle(
        "Activar validación de contexto / punto ciego",
        value=True,
        help="Revisa si la reseña habla del producto o categoría seleccionados.",
    )
    stars       = st.slider("Calificación en estrellas", min_value=1, max_value=5, value=5)
    user_name   = st.text_input("Perfil de usuario", value="Auditor_Seminario")
    review_text = st.text_area("Texto de la reseña", height=200)
    analyze_btn = st.button("Analizar reseña", type="primary")

    if analyze_btn:
        if not is_non_empty_text(review_text):
            st.warning("Ingresa una reseña antes de analizar.")
        else:
            with st.spinner("Consultando API en Render..."):
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

    st.markdown("#### Carga masiva")
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
        api_result["probability"]
        if api_result and "error" not in api_result
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
            "Diagnóstico",
            decision,
            f"Estado: {latest_result['status']} · Utilidad: {format_percentage(probability)}",
            tone=tone,
        )

        if latest_result.get("context_validation_enabled"):
            ctx  = ", ".join(latest_result["context_hits"]) or "ninguna"
            tech = ", ".join(latest_result["tech_hits"])  or "ninguno"
            c1, c2 = st.columns(2)
            c1.metric("Contexto detectado", ctx[:30])
            c2.metric("Términos ajenos",    tech[:30])
    else:
        st.info("Introduce una reseña y presiona Analizar.")

# ── Desglose de features — lo que pide el caso ───────────────────────────────

st.markdown("### Desglose de características calculadas")
st.caption(
    "Estas son las 4 variables que el modelo usa para predecir la utilidad. "
    "Cada una es calculada directamente del texto — sin modelos de lenguaje."
)

latest_result = st.session_state.get("latest_audit_result")
api_result    = st.session_state.get("_api_result")
probability   = (
    api_result["probability"]
    if api_result and "error" not in api_result
    else (latest_result["probability"] if latest_result else 0.0)
)

review_len  = latest_result["review_len"]  if latest_result else 0
incoherence = latest_result["incoherente"] if latest_result else False

# Intentar extraer sentimiento del api_result si está disponible
sentiment_val = None
if api_result and "features" in api_result:
    sentiment_val = api_result["features"].get("sentiment_score")
elif api_result and "sentiment_score" in api_result:
    sentiment_val = api_result["sentiment_score"]

f1, f2, f3, f4 = st.columns(4, gap="medium")

with f1:
    len_badge = "metric-badge-good" if review_len > 60 else "metric-badge-warn"
    len_label = "Longitud útil" if review_len > 60 else "Muy corta"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Longitud (review_len)</div>
            <div class="metric-value">{review_len} palabras</div>
            <div class="metric-caption">Feature #1. Umbral recomendado: ≥ 80 palabras.</div>
            <span class="metric-badge {len_badge}">{len_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with f2:
    stars_val = st.session_state.get("latest_stars", 5)
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Calificación (Score)</div>
            <div class="metric-value">{"★" * int(stars_val)}{"☆" * max(0, 5-int(stars_val))}</div>
            <div class="metric-caption">Estrellas asignadas por el usuario. Input del modelo.</div>
            <span class="metric-badge metric-badge-info">{stars_val} de 5</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with f3:
    if sentiment_val is not None:
        s_label = "Positivo" if sentiment_val > 0.05 else ("Negativo" if sentiment_val < -0.05 else "Neutro")
        s_badge = "metric-badge-good" if sentiment_val > 0.05 else ("metric-badge-warn" if sentiment_val < -0.05 else "metric-badge-info")
        s_display = f"{sentiment_val:.2f}"
    else:
        s_label, s_badge, s_display = "Pendiente", "metric-badge-info", "—"

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Sentimiento VADER</div>
            <div class="metric-value">{s_display}</div>
            <div class="metric-caption">Score compuesto VADER (−1 a +1). Calculado sin entrenamiento.</div>
            <span class="metric-badge {s_badge}">{s_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with f4:
    inc_badge = "metric-badge-warn" if incoherence else "metric-badge-good"
    inc_label = "Incoherente — penaliza" if incoherence else "Coherente"
    inc_val   = "Sí" if incoherence else "No"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Coherencia (incoherente)</div>
            <div class="metric-value">{inc_val}</div>
            <div class="metric-caption">¿El tono del texto contradice las estrellas asignadas?</div>
            <span class="metric-badge {inc_badge}">{inc_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Benchmark del producto ────────────────────────────────────────────────────

st.markdown("### Benchmark del producto")
product_benchmark = get_product_benchmark(selected_product)
b1, b2, b3, b4 = st.columns(4, gap="medium")
b1.metric("Promedio producto", format_percentage(product_benchmark["avg_helpfulness"]))
b2.metric("Top producto",      format_percentage(product_benchmark["top_helpfulness"]))
b3.metric("Total reseñas",     str(product_benchmark["count"]))
if latest_result:
    delta = latest_result["probability"] - product_benchmark["avg_helpfulness"]
    b4.metric("vs. promedio", f"{delta:+.1%}", delta_color="normal")

# ── Recomendaciones ───────────────────────────────────────────────────────────

if latest_result:
    recommendations = generate_review_recommendations(latest_result)
    st.markdown("### Cómo mejorar esta reseña")
    r1, r2 = st.columns(2, gap="large")
    with r1:
        st.markdown(
            f"""
            <div class="highlight-card">
                <div class="highlight-title">Acción principal</div>
                <div class="highlight-body">{recommendations[0]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with r2:
        if len(recommendations) > 1:
            st.markdown(
                f"""
                <div class="highlight-card">
                    <div class="highlight-title">Acción adicional</div>
                    <div class="highlight-body">{recommendations[1]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Guardar reseña
    sv1, sv2 = st.columns([0.35, 0.65])
    with sv1:
        if st.button("💾 Guardar reseña", use_container_width=True):
            ok, msg = save_latest_review_to_file(selected_product)
            (st.success if ok else st.warning)(msg)

    # Vista previa
    st.markdown("### Vista previa de la reseña")
    render_review_card(
        user_name=user_name,
        stars=stars,
        review_text=review_text,
        meta_line=f"{product_detail['ProductName']} | {product_detail['Categoria_Real']} | {pd.Timestamp.now().strftime('%d/%m/%Y')}",
        badge=latest_result["status"],
        helpfulness=format_percentage(probability),
        highlighted=True,
    )

# Guardar estado para la pagina de ranking
st.session_state["selected_product_id"]  = selected_product
st.session_state["latest_stars"]         = stars
st.session_state["latest_review_text"]   = review_text