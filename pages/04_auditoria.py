"""Pagina de auditoria en tiempo real."""

import os

import pandas as pd
import requests
import streamlit as st

from components.cards import render_highlight_card, render_metric_card, render_review_card
from components.feedback import render_status_panel
from plots.audit_charts import build_helpfulness_gauge
from services.catalog_service import get_product_detail, get_product_options
from services.ml_service import generate_review_recommendations
from services.preprocessing_service import (
    append_audited_review,
    get_audited_reviews_operational_table,
    get_product_benchmark,
    get_position_summary,
    get_product_reviews_by_date,
    get_review_context_window,
    process_uploaded_audit_file,
    save_latest_review_to_file,
)
from utils.formatters import format_percentage
from utils.validators import is_non_empty_text


# ── Funciones de conexión a la API de Render ──────────────────────────────────

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


def _call_top_words() -> dict:
    try:
        r = requests.get(_api_url() + "/reviews/top_words", timeout=35)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"error": str(exc)}


# ── App ───────────────────────────────────────────────────────────────────────

st.title("Auditoría en Tiempo Real")

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
    st.warning("No hay productos disponibles en el catalogo para auditar.")
    st.stop()

left_col, right_col = st.columns([1.1, 1], gap="large")

with left_col:
    selected_product = st.selectbox("Producto", options=product_options)
    product_detail = get_product_detail(selected_product)
    pd1, pd2 = st.columns(2)
    pd1.metric("Producto", product_detail["ProductName"][:28])
    pd2.metric("Categoría", product_detail["Categoria_Real"][:22])

    validate_context = st.toggle(
        "Activar validación de contexto / punto ciego",
        value=True,
        help="Revisa si la reseña habla del producto o categoría seleccionados.",
    )
    stars = st.slider("Calificación en estrellas", min_value=1, max_value=5, value=5)
    user_name = st.text_input("Perfil de usuario", value="Auditor_Seminario")
    review_text = st.text_area("Texto de la reseña", height=200)
    analyze_review = st.button("Analizar reseña", type="primary")

    if analyze_review:
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
    uploaded_file = st.file_uploader(
        "CSV con ProductId, ProfileName, Score, Text", type=["csv"]
    )
    process_batch = st.button("Procesar lote CSV")
    if process_batch:
        if uploaded_file is None:
            st.warning("Selecciona un archivo CSV antes de procesar el lote.")
        else:
            batch_df, error_message = process_uploaded_audit_file(uploaded_file)
            if error_message:
                st.error(error_message)
            else:
                st.success(f"Lote procesado: {len(batch_df)} reseñas agregadas.")
                st.dataframe(batch_df.head(20), use_container_width=True)

with right_col:
    latest_result = st.session_state.get("latest_audit_result")
    api_result    = st.session_state.get("_api_result")
    probability = (
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
            tech = ", ".join(latest_result["tech_hits"]) or "ninguno"
            c1, c2 = st.columns(2)
            c1.metric("Contexto detectado", ctx[:30])
            c2.metric("Términos ajenos", tech[:30])
    else:
        st.info("Introduce una reseña y presiona Analizar.")

# ── Métricas de resultado ─────────────────────────────────────────────────────
st.markdown("### Resultado")

latest_result    = st.session_state.get("latest_audit_result")
api_result       = st.session_state.get("_api_result")
probability = (
    api_result["probability"]
    if api_result and "error" not in api_result
    else (latest_result["probability"] if latest_result else 0.0)
)
review_len       = latest_result["review_len"] if latest_result else 0
incoherence      = latest_result["incoherente"] if latest_result else False
product_benchmark = get_product_benchmark(selected_product)
latest_review_id  = st.session_state.get("latest_review_id")
position_summary  = get_position_summary(selected_product, latest_review_id)
review_window_df  = get_review_context_window(selected_product, latest_review_id, window_size=1)
product_history_df = get_product_reviews_by_date(selected_product, ascending=False)

r1, r2, r3, r4 = st.columns(4, gap="medium")
with r1:
    render_metric_card("Utilidad estimada", format_percentage(probability), "Probabilidad del modelo")
with r2:
    render_metric_card("Longitud", f"{review_len} palabras", "Palabras en la reseña")
with r3:
    render_metric_card("Incoherencia", "Sí" if incoherence else "No", "Tono vs estrellas")
with r4:
    blind_val = "Detectado" if latest_result and latest_result.get("context_blind_spot") else (latest_result["status"] if latest_result else "Sin evaluar")
    render_metric_card("Punto ciego", blind_val, "Resultado contextual")

p1, p2, p3 = st.columns(3, gap="medium")
with p1:
    render_metric_card(
        "Posición local",
        f"{position_summary['local_rank']} / {position_summary['product_count']}" if position_summary["local_rank"] else "Sin posición",
        "Lugar en el producto",
    )
with p2:
    render_metric_card(
        "Posición global",
        f"{position_summary['global_rank']} / {position_summary['global_count']}" if position_summary["global_rank"] else "Sin posición",
        "Lugar en toda la base",
    )
with p3:
    render_metric_card("Reseñas del producto", str(position_summary["product_count"]), "Volumen histórico")

# ── Benchmark y recomendación ─────────────────────────────────────────────────
bm1, bm2, bm3, bm4 = st.columns(4, gap="medium")
bm1.metric("Promedio producto", format_percentage(product_benchmark["avg_helpfulness"]))
bm2.metric("Top producto",      format_percentage(product_benchmark["top_helpfulness"]))
bm3.metric("Total reseñas",     str(product_benchmark["count"]))
if latest_result:
    delta = latest_result["probability"] - product_benchmark["avg_helpfulness"]
    bm4.metric("vs. promedio", f"{delta:+.1%}", delta_color="normal")

if latest_result:
    recommendations = generate_review_recommendations(latest_result)
    adv_l, adv_r = st.columns(2, gap="large")
    with adv_l:
        render_highlight_card("Recomendación principal", "Mejora sugerida", recommendations[0])
    with adv_r:
        if len(recommendations) > 1:
            render_highlight_card("Recomendación adicional", "→", recommendations[1])

    save_l, save_r = st.columns([0.4, 0.6])
    with save_l:
        save_review = st.button("💾 Guardar reseña", use_container_width=True)
    with save_r:
        if save_review:
            saved_ok, save_message = save_latest_review_to_file(selected_product)
            (st.success if saved_ok else st.warning)(save_message)

    st.markdown("### Vista previa")
    render_review_card(
        user_name=user_name,
        stars=stars,
        review_text=review_text,
        meta_line=f"{product_detail['ProductName']} | {product_detail['Categoria_Real']} | {pd.Timestamp.now().strftime('%d/%m/%Y')}",
        badge=latest_result["status"],
        helpfulness=format_percentage(probability),
        highlighted=True,
    )

    st.markdown("### Tu reseña en contexto del producto")
    if not review_window_df.empty:
        for _, row in review_window_df.iterrows():
            meta_line = (
                f"Puesto local {int(row['Puesto Local'])} | "
                f"{pd.to_datetime(row['CreatedAt']).strftime('%d/%m/%Y') if pd.notna(row.get('CreatedAt')) else 'Sin fecha'}"
            )
            render_review_card(
                user_name=str(row["User"]),
                stars=int(row["Stars"]),
                review_text=str(row["Text"]),
                meta_line=meta_line,
                badge="Tu reseña evaluada" if row["EsActual"] else row["Estado"],
                helpfulness=format_percentage(float(row["Helpfulness"])),
                highlighted=bool(row["EsActual"]),
            )

# ── Historial ─────────────────────────────────────────────────────────────────
st.markdown("### Historial del producto por fecha")
history_preview = product_history_df.head(10).copy()
if not history_preview.empty:
    history_preview["CreatedAt"] = pd.to_datetime(history_preview["CreatedAt"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(
        history_preview[["CreatedAt", "User", "Stars", "Helpfulness", "Estado", "Text"]],
        use_container_width=True, hide_index=True,
    )

st.markdown("### Archivo operativo de reseñas guardadas")
saved_reviews_df = get_audited_reviews_operational_table()
if saved_reviews_df.empty:
    st.info("Aún no hay reseñas guardadas en el CSV operativo separado.")
else:
    st.dataframe(saved_reviews_df.tail(20), use_container_width=True, hide_index=True)

st.session_state["selected_product_id"] = selected_product
st.session_state["latest_stars"]        = stars
st.session_state["latest_review_text"]  = review_text