"""Auditoría en tiempo real."""
# ── Guard: redirige a main.py si se accede directamente sin sesión ──────────
import streamlit as st
if not st.session_state.get("app_initialized"):
    st.switch_page("main.py")
# ────────────────────────────────────────────────────────────────────────────


import os, pandas as pd, requests, streamlit as st
from shared_sidebar import render_sidebar
from components.cards import render_metric_card, render_review_card
from components.feedback import render_status_panel
from plots.audit_charts import build_helpfulness_gauge
from services.catalog_service import get_product_detail, get_product_options
from services.ml_service import generate_review_recommendations
from services.preprocessing_service import (append_audited_review, get_product_benchmark,
    process_uploaded_audit_file, save_latest_review_to_file)
from utils.formatters import format_percentage
from utils.validators import is_non_empty_text

with open("styles/styles.css", "r", encoding="utf-8") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
render_sidebar()

def _api_url():
    try: return st.secrets["API_URL"].rstrip("/")
    except: return os.getenv("API_URL", "https://proyecto-prediccion-v9qk.onrender.com").rstrip("/")

def _call_predict(review_text, stars):
    try:
        r = requests.post(_api_url()+"/reviews/predict_helpfulness",
            json={"review_text": review_text, "stars": stars}, timeout=35)
        r.raise_for_status(); return r.json()
    except requests.exceptions.Timeout: return {"error": "Timeout — Render tarda ~30 s. Reintenta."}
    except Exception as exc: return {"error": str(exc)}

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
            Auditoría en Tiempo Real
        </div>
        <div style="font-size:0.82rem;color:rgba(255,255,255,0.65)">Probabilidad de utilidad · Desglose de las 4 características calculadas</div>
    </div>
    """,
    unsafe_allow_html=True,
)


product_options = get_product_options()
if not product_options:
    st.warning("No hay productos disponibles."); st.stop()

left_col, right_col = st.columns([1.1, 1], gap="large")
with left_col:
    selected_product = st.selectbox("Producto", options=product_options)
    product_detail   = get_product_detail(selected_product)
    pd1, pd2 = st.columns(2)
    pd1.metric("Producto",  product_detail["ProductName"][:28])
    pd2.metric("Categoría", product_detail["Categoria_Real"][:22])
    validate_context = st.toggle("Validación de contexto / punto ciego", value=True)
    stars     = st.slider("Calificación en estrellas", min_value=1, max_value=5, value=5)
    user_name = st.text_input("Perfil de usuario", value="Auditor_Seminario")
    review_text = st.text_area("Texto de la reseña", height=200)
    if st.button("Analizar reseña", type="primary"):
        if not is_non_empty_text(review_text):
            st.warning("Ingresa una reseña antes de analizar.")
        else:
            with st.spinner("Consultando API..."):
                api_r = _call_predict(review_text.strip(), stars)
            st.session_state["_api_result"] = api_r if "error" not in api_r else None
            if "error" in api_r: st.error(f"API no disponible: {api_r['error']}")
            st.session_state["latest_audit_result"] = append_audited_review(
                selected_product, user_name, stars, review_text.strip(), validate_context=validate_context)
    st.markdown('<div class="section-label">Carga masiva</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("CSV con ProductId, ProfileName, Score, Text", type=["csv"])
    if st.button("Procesar lote CSV"):
        if uploaded_file is None: st.warning("Selecciona un CSV.")
        else:
            batch_df, err = process_uploaded_audit_file(uploaded_file)
            if err: st.error(err)
            else: st.success(f"{len(batch_df)} reseñas agregadas."); st.dataframe(batch_df.head(20), use_container_width=True)

with right_col:
    lr = st.session_state.get("latest_audit_result")
    ar = st.session_state.get("_api_result")
    prob = ar["probability"] if ar and "error" not in ar else (lr["probability"] if lr else 0.0)
    st.plotly_chart(build_helpfulness_gauge(prob), use_container_width=True)
    if lr:
        tone, decision = ("danger","Revisión obligatoria") if "Punto Ciego" in lr["status"] else (("success","Lista para publicar") if prob >= 0.70 else ("warning","Conviene mejorarla"))
        render_status_panel("Diagnóstico", decision, f"Estado: {lr['status']} · Utilidad: {format_percentage(prob)}", tone=tone)
    else:
        st.info("Introduce una reseña y presiona Analizar.")

st.markdown('<div class="section-label">Características calculadas</div>', unsafe_allow_html=True)
lr = st.session_state.get("latest_audit_result")
ar = st.session_state.get("_api_result")
prob = ar["probability"] if ar and "error" not in ar else (lr["probability"] if lr else 0.0)
review_len  = lr["review_len"]  if lr else 0
incoherence = lr["incoherente"] if lr else False
sentiment_val = (ar or {}).get("features", {}).get("sentiment_score") \
    or (ar or {}).get("sentiment_score") \
    or (ar or {}).get("features_calculated", {}).get("sentiment_compound") \
    or (lr.get("sentiment_score") if lr else None)
stars_val = st.session_state.get("latest_stars", 5)

f1, f2, f3, f4 = st.columns(4, gap="medium")
with f1:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Longitud</div><div class="metric-value">{review_len} palabras</div><div class="metric-caption">Umbral recomendado: ≥ 80 palabras</div><span class="metric-badge {'metric-badge-good' if review_len > 60 else 'metric-badge-warn'}">{'Adecuada' if review_len > 60 else 'Muy corta'}</span></div>""", unsafe_allow_html=True)
with f2:
    filled = "&#9733;" * int(stars_val); empty = "&#9734;" * max(0, 5-int(stars_val))
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Calificación</div><div class="metric-value" style="font-size:1.4rem;color:#f59e0b">{filled}{empty}</div><div class="metric-caption">Estrellas asignadas</div><span class="metric-badge metric-badge-info">{stars_val} de 5</span></div>""", unsafe_allow_html=True)
with f3:
    s_label = ("Positivo" if sentiment_val and sentiment_val > 0.05 else ("Negativo" if sentiment_val and sentiment_val < -0.05 else "Neutro")) if sentiment_val is not None else "Pendiente"
    s_badge = ("metric-badge-good" if sentiment_val and sentiment_val > 0.05 else ("metric-badge-warn" if sentiment_val and sentiment_val < -0.05 else "metric-badge-info")) if sentiment_val is not None else "metric-badge-info"
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Sentimiento VADER</div><div class="metric-value">{f'{sentiment_val:.2f}' if sentiment_val is not None else '—'}</div><div class="metric-caption">Score compuesto (−1 a +1)</div><span class="metric-badge {s_badge}">{s_label}</span></div>""", unsafe_allow_html=True)
with f4:
    coherence_label = "Incoherente" if incoherence else "Coherente"
    coherence_value = "Tono vs. estrellas no coinciden" if incoherence else "Tono alineado con estrellas"
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Coherencia texto–estrellas</div><div class="metric-value" style="font-size:1rem">{coherence_value}</div><div class="metric-caption">¿El sentimiento del texto coincide con la calificación?</div><span class="metric-badge {'metric-badge-warn' if incoherence else 'metric-badge-good'}">{coherence_label}</span></div>""", unsafe_allow_html=True)

st.markdown('<div class="section-label">Benchmark del producto</div>', unsafe_allow_html=True)
st.caption("Comparación de la reseña actual contra el historial del producto en la base operativa. Incluye reseñas históricas del dataset y reseñas auditadas previamente en esta sesión.")
pb = get_product_benchmark(selected_product)
b1, b2, b3, b4 = st.columns(4, gap="medium")
with b1: render_metric_card("Promedio", format_percentage(pb["avg_helpfulness"]), "Utilidad media")
with b2: render_metric_card("Top", format_percentage(pb["top_helpfulness"]), "Mejor score")
with b3: render_metric_card("Total reseñas", str(pb["count"]), "Historial")
with b4:
    if lr:
        render_metric_card("vs. promedio", f"{lr['probability'] - pb['avg_helpfulness']:+.1%}", "Tu reseña vs. media")

if lr:
    recs = generate_review_recommendations(lr)
    st.markdown('<div class="section-label">Cómo mejorar esta reseña</div>', unsafe_allow_html=True)
    r1, r2 = st.columns(2, gap="large")
    with r1: st.markdown(f'<div class="highlight-card"><div class="highlight-title">Acción principal</div><div class="highlight-body">{recs[0]}</div></div>', unsafe_allow_html=True)
    with r2:
        if len(recs) > 1: st.markdown(f'<div class="highlight-card"><div class="highlight-title">Acción adicional</div><div class="highlight-body">{recs[1]}</div></div>', unsafe_allow_html=True)
    sv1, _ = st.columns([0.35, 0.65])
    with sv1:
        if st.button("Guardar reseña", use_container_width=True):
            ok, msg = save_latest_review_to_file(selected_product)
            (st.success if ok else st.warning)(msg)
    st.markdown('<div class="section-label">Vista previa</div>', unsafe_allow_html=True)
    render_review_card(user_name=user_name, stars=stars, review_text=review_text,
        meta_line=f"{product_detail['ProductName']} | {product_detail['Categoria_Real']} | {pd.Timestamp.now().strftime('%d/%m/%Y')}",
        badge=lr["status"], helpfulness=format_percentage(prob), highlighted=True)

st.session_state["selected_product_id"] = selected_product
st.session_state["latest_stars"]        = stars
st.session_state["latest_review_text"]  = review_text