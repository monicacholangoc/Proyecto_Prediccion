"""Auditoria en tiempo real."""
try:
    import streamlit as _st
    if not _st.session_state.get("app_initialized"):
        _st.switch_page("main.py")
except Exception:
    pass

import os
import pandas as pd
import requests
import streamlit as st
from shared_sidebar import render_sidebar
from components.cards import render_metric_card, render_review_card
from components.feedback import render_status_panel
from plots.audit_charts import build_helpfulness_gauge
from services.catalog_service import get_product_detail, get_product_options
from services.ml_service import generate_review_recommendations, audit_review_text
from services.preprocessing_service import (
    append_audited_review,
    get_product_benchmark,
    get_position_summary,
    get_review_context_window,
    get_audited_reviews_operational_table,
    process_uploaded_audit_file,
    save_latest_review_to_file,
)
from utils.formatters import format_percentage
from utils.validators import is_non_empty_text

with open("styles/styles.css", "r", encoding="utf-8") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
render_sidebar()

st.markdown("""
<style>
.feat-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.3rem; margin-bottom:0.5rem; }
.feat-card { background:#fff; border:1px solid #e5e9f2; border-radius:8px; padding:0.4rem 0.55rem; }
.feat-lbl { font-size:0.58rem; font-weight:700; color:#7a8499; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.05rem; }
.feat-val { font-size:0.88rem; font-weight:700; color:#1a2236; line-height:1.2; margin-bottom:0.05rem; }
.feat-cap { font-size:0.56rem; color:#9aa5b8; margin-bottom:0.1rem; }
.feat-badge { display:inline-block; font-size:0.56rem !important; font-weight:600; padding:0.06rem 0.35rem !important; border-radius:4px; color:#fff !important; }
.feat-green { background:#15803d; }
.feat-amber { background:#b45309; }
.feat-blue  { background:#1d4ed8; }
.feat-gray  { background:#64748b; }
</style>
""", unsafe_allow_html=True)


def _api_url():
    try:
        return st.secrets["API_URL"].rstrip("/")
    except Exception:
        return os.getenv("API_URL", "https://proyecto-prediccion-v9qk.onrender.com").rstrip("/")


def _call_predict(review_text, stars):
    try:
        r = requests.post(
            _api_url() + "/reviews/predict_helpfulness",
            json={"review_text": review_text, "stars": stars},
            timeout=35,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        return {"error": "Timeout. Reintenta."}
    except Exception as exc:
        return {"error": str(exc)}


st.markdown("""
<div style="background:linear-gradient(135deg,#16213b 0%,#1746a2 60%,#0f4c5c 100%);
    border-radius:16px;padding:1.4rem 2rem;margin-bottom:1.4rem;color:#fff">
    <div style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                color:rgba(255,255,255,0.55);text-transform:uppercase;margin-bottom:0.35rem">
        Seminario Predictivo 2026 - Caso 06
    </div>
    <div style="font-size:clamp(1.4rem,3vw,1.9rem);font-weight:800;
                letter-spacing:-0.02em;line-height:1.2;margin-bottom:0.3rem">
        Auditoria en Tiempo Real
    </div>
    <div style="font-size:0.82rem;color:rgba(255,255,255,0.65)">
        Evaluacion individual - Carga masiva CSV - Diagnostico de utilidad
    </div>
</div>""", unsafe_allow_html=True)

product_options = get_product_options()
if not product_options:
    st.warning("No hay productos disponibles.")
    st.stop()

st.markdown('<div class="section-label">Producto a auditar</div>', unsafe_allow_html=True)
sc1, sc2, sc3 = st.columns([2, 1, 1], gap="medium")
with sc1:
    selected_product = st.selectbox("Producto", options=product_options, label_visibility="collapsed")
product_detail = get_product_detail(selected_product)
with sc2:
    st.metric("Producto", product_detail["ProductName"][:28])
with sc3:
    st.metric("Categoria", product_detail["Categoria_Real"][:22])

st.markdown("---")
tab1, tab2 = st.tabs(["Resena individual", "Carga masiva CSV"])

# ==============================================================
# TAB 1
# ==============================================================
with tab1:
    left_col, right_col = st.columns([1.1, 1], gap="large")

    with left_col:
        st.markdown('<div class="section-label">Configuracion</div>', unsafe_allow_html=True)

        # Leer valor previo ANTES de renderizar el toggle
        _prev_val = st.session_state.get("_toggle_prev_val", False)

        validate_context = st.toggle(
            "Validacion de contexto / punto ciego",
            value=False,
            key="_toggle_current_val",
            help=(
                "ON: si la resena no menciona ningun termino alimenticio, "
                "la probabilidad cae a 0.05 (punto ciego).\n"
                "OFF: solo evalua utilidad del texto."
            ),
        )

        stars = st.slider("Calificacion en estrellas", min_value=1, max_value=5, value=5)
        user_name = st.text_input("Perfil de usuario", value="Auditor_Seminario")
        review_text = st.text_area(
            "Texto de la resena", height=200,
            placeholder="Escribe aqui la resena a evaluar...",
        )
        analyze_clicked = st.button("Analizar resena", use_container_width=True)

        if analyze_clicked:
            if not is_non_empty_text(review_text):
                st.warning("Ingresa una resena antes de analizar.")
            else:
                with st.spinner("Analizando..."):
                    api_r = _call_predict(review_text.strip(), stars)
                st.session_state["_api_result"]       = api_r if "error" not in api_r else None
                st.session_state["_last_review_text"] = review_text.strip()
                st.session_state["_last_stars"]       = stars
                st.session_state["_last_product"]     = selected_product
                st.session_state["_toggle_prev_val"]  = validate_context
                if "error" in api_r:
                    st.error(f"API no disponible: {api_r['error']}")
                audit_result = append_audited_review(
                    selected_product, user_name, stars,
                    review_text.strip(), validate_context=validate_context,
                )
                st.session_state["latest_audit_result"] = audit_result
                st.session_state["latest_stars"]        = stars

        # Recalcular si el toggle cambio sin re-analizar
        last_text    = st.session_state.get("_last_review_text")
        last_stars_v = st.session_state.get("_last_stars")
        last_product = st.session_state.get("_last_product")

        if last_text and (validate_context != _prev_val):
            detail = get_product_detail(last_product or selected_product)
            recalc = audit_review_text(
                last_text,
                last_stars_v or stars,
                last_product or selected_product,
                product_name=detail.get("ProductName"),
                category_name=detail.get("Categoria_Real"),
                validate_context=validate_context,
            )
            st.session_state["latest_audit_result"] = recalc
            st.session_state["_toggle_prev_val"]    = validate_context

    # Panel derecho
    with right_col:
        lr   = st.session_state.get("latest_audit_result")
        prob = lr["probability"] if lr else 0.0

        st.plotly_chart(build_helpfulness_gauge(prob), use_container_width=True)

        # Caracteristicas calculadas compactas
        st.markdown(
            '<div class="section-label" style="margin-bottom:0.3rem">Caracteristicas calculadas</div>',
            unsafe_allow_html=True,
        )
        rl    = lr["review_len"]  if lr else 0
        incoh = lr["incoherente"] if lr else False
        sv    = st.session_state.get("latest_stars", 5)
        sent  = lr.get("sentiment_score") if lr else None

        lb = "feat-green" if rl > 60 else "feat-amber"
        ll = "Adecuada" if rl > 60 else "Corta"

        if sent is not None:
            sl = "Positivo" if sent > 0.05 else ("Negativo" if sent < -0.05 else "Neutro")
            sb = "feat-green" if sent > 0.05 else ("feat-amber" if sent < -0.05 else "feat-blue")
            ss = f"{sent:.2f}"
        else:
            sl, sb, ss = "Pendiente", "feat-gray", "-"

        filled = "&#9733;" * int(sv)
        empty  = "&#9734;" * max(0, 5 - int(sv))
        cl = "Coherente" if not incoh else "Incoherente"
        cb = "feat-green" if not incoh else "feat-amber"

        st.markdown(f"""
        <div class="feat-grid">
            <div class="feat-card">
                <div class="feat-lbl">Longitud</div>
                <div class="feat-val">{rl} palabras</div>
                <div class="feat-cap">Umbral: 80 palabras</div>
                <span class="feat-badge {lb}">{ll}</span>
            </div>
            <div class="feat-card">
                <div class="feat-lbl">Sentimiento</div>
                <div class="feat-val">{ss}</div>
                <div class="feat-cap">VADER (-1 a +1)</div>
                <span class="feat-badge {sb}">{sl}</span>
            </div>
            <div class="feat-card">
                <div class="feat-lbl">Calificacion</div>
                <div class="feat-val" style="color:#f59e0b">{filled}{empty}</div>
                <div class="feat-cap">{sv} de 5 estrellas</div>
                <span class="feat-badge feat-blue">{sv}/5</span>
            </div>
            <div class="feat-card">
                <div class="feat-lbl">Coherencia</div>
                <div class="feat-val">{cl}</div>
                <div class="feat-cap">Tono vs. estrellas</div>
                <span class="feat-badge {cb}">{cl}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Diagnostico
        st.markdown(
            '<div class="section-label" style="margin-top:0.5rem;margin-bottom:0.3rem">Diagnostico</div>',
            unsafe_allow_html=True,
        )
        if lr:
            is_blind = "Punto Ciego" in lr["status"]
            tone     = "danger" if is_blind else ("success" if prob >= 0.70 else "warning")
            decision = "Revision obligatoria" if is_blind else ("Lista para publicar" if prob >= 0.70 else "Conviene mejorarla")

            if is_blind:
                razon = "La resena no tiene contexto alimenticio."
            elif prob >= 0.70:
                razon = "La resena supera el umbral de utilidad."
            elif rl < 60:
                razon = "La resena es muy corta (menos de 60 palabras)."
            elif sent is not None and sent < -0.05:
                razon = "El sentimiento del texto es negativo."
            else:
                razon = f"Utilidad {format_percentage(prob)} bajo umbral del 70%."

            render_status_panel(
                "Diagnostico", decision,
                (
                    f"Estado: {lr['status']} | "
                    f"Utilidad: {format_percentage(prob)} | "
                    f"Punto ciego: {'Si' if is_blind else 'No'} | "
                    f"Validacion: {'Activa' if lr.get('context_validation_enabled') else 'Desactivada'} | "
                    f"Razon: {razon}"
                ),
                tone=tone,
            )
            if lr.get("context_validation_enabled"):
                ctx  = ", ".join(lr.get("context_hits", [])) or "ninguna"
                tech = ", ".join(lr.get("tech_hits", []))    or "ninguno"
                st.markdown(
                    f'<div class="highlight-card" style="margin-top:0.4rem;padding:0.5rem 0.7rem">'
                    f'<div class="highlight-title" style="font-size:0.68rem">Contexto alimenticio</div>'
                    f'<div class="highlight-body" style="font-size:0.7rem">'
                    f'{lr.get("context_explanation","")}<br>'
                    f'<b>Detectadas:</b> {ctx} | <b>Ajenas:</b> {tech}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Introduce una resena y presiona Analizar.")

    st.markdown("---")

    
    lr   = st.session_state.get("latest_audit_result")
    prob = lr["probability"] if lr else 0.0

    if lr:
        recs = generate_review_recommendations(lr)
        st.markdown('<div class="section-label">Como mejorar esta resena</div>', unsafe_allow_html=True)
        r1, r2 = st.columns(2, gap="large")
        with r1:
            st.markdown(
                f'<div class="highlight-card"><div class="highlight-title">Accion principal</div>'
                f'<div class="highlight-body">{recs[0]}</div></div>',
                unsafe_allow_html=True,
            )
        with r2:
            if len(recs) > 1:
                st.markdown(
                    f'<div class="highlight-card"><div class="highlight-title">Accion adicional</div>'
                    f'<div class="highlight-body">{recs[1]}</div></div>',
                    unsafe_allow_html=True,
                )

        sv1, _ = st.columns([0.3, 0.7])
        with sv1:
            if st.button("Guardar resena", use_container_width=True):
                ok, msg = save_latest_review_to_file(selected_product)
                (st.success if ok else st.warning)(msg)

    latest_review_id = st.session_state.get("latest_review_id")
    position_summary = get_position_summary(selected_product, latest_review_id)
    review_window_df = get_review_context_window(selected_product, latest_review_id, window_size=2)

    if latest_review_id and not review_window_df.empty:
        st.markdown('<div class="section-label">Tu resena en contexto del ranking</div>', unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3, gap="medium")
        with p1:
            render_metric_card(
                "Posicion local",
                f"{position_summary['local_rank']} / {position_summary['product_count']}"
                if position_summary["local_rank"] else "Sin resena evaluada",
                "Lugar dentro del producto",
            )
        with p2:
            render_metric_card(
                "Posicion global",
                f"{position_summary['global_rank']} / {position_summary['global_count']}"
                if position_summary["global_rank"] else "Sin resena evaluada",
                "Lugar en toda la base",
            )
        with p3:
            render_metric_card(
                "Total del producto", str(position_summary["product_count"]), "Volumen historico"
            )

        with st.expander("Ver resenas del contexto de ranking"):
            for _, row in review_window_df.iterrows():
                is_cur     = bool(row["EsActual"])
                badge_txt  = "Tu resena" if is_cur else str(row["Estado"])
                full_text  = str(row["Text"])
                short_text = full_text[:180] + ("..." if len(full_text) > 180 else "")
                border     = "border:2px solid var(--primary);" if is_cur else ""
                badge_cls  = "metric-badge-good" if "APROBADA" in str(row["Estado"]) else "metric-badge-warn"
                st.markdown(
                    f'<div class="metric-card" style="{border}margin-bottom:0.5rem">'
                    f'<div style="display:flex;justify-content:space-between;margin-bottom:0.25rem">'
                    f'<span style="font-size:0.72rem;color:var(--muted)">Puesto {int(row["Puesto Local"])} - {str(row["User"])}</span>'
                    f'<span class="metric-badge {badge_cls}" style="font-size:0.6rem">{badge_txt}</span></div>'
                    f'<div style="font-size:0.76rem;color:var(--text);margin-bottom:0.2rem">{short_text}</div>'
                    f'<div style="font-size:0.64rem;color:var(--muted)">Utilidad: {format_percentage(float(row["Helpfulness"]))}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

# ==============================================================
# TAB 2
# ==============================================================
with tab2:
    st.markdown('<div class="section-label">Carga masiva de resenas</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="highlight-card"><div class="highlight-title">Formato requerido del CSV</div>'
        '<div class="highlight-body">Columnas: '
        '<code>ProductId</code>, <code>ProfileName</code>, <code>Score</code>, <code>Text</code>.'
        '</div></div>',
        unsafe_allow_html=True,
    )

    uc1, uc2 = st.columns([1.5, 1], gap="large")
    with uc1:
        uploaded_file = st.file_uploader(
            "Selecciona el archivo CSV", type=["csv"],
            help="Columnas: ProductId, ProfileName, Score, Text",
        )
        if st.button("Procesar lote CSV", type="primary", use_container_width=True):
            if uploaded_file is None:
                st.warning("Selecciona un archivo CSV antes de procesar.")
            else:
                with st.spinner("Procesando resenas..."):
                    batch_df, err = process_uploaded_audit_file(uploaded_file)
                if err:
                    st.error(err)
                else:
                    st.success(f"{len(batch_df)} resenas procesadas.")
                    st.session_state["_last_batch_df"] = batch_df

    with uc2:
        st.markdown(
            '<div class="metric-card"><div class="metric-label">Columnas requeridas</div>'
            '<div class="metric-caption" style="margin-top:0.4rem">'
            '<b>ProductId</b> - codigo del producto<br>'
            '<b>ProfileName</b> - nombre del autor<br>'
            '<b>Score</b> - calificacion (1-5)<br>'
            '<b>Text</b> - texto de la resena</div></div>',
            unsafe_allow_html=True,
        )

    batch_result = st.session_state.get("_last_batch_df")
    if batch_result is not None and not batch_result.empty:
        st.markdown('<div class="section-label">Resultado del lote</div>', unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4, gap="medium")
        aprobadas  = int((batch_result["Estado"] == "APROBADA (Publicada)").sum()) if "Estado" in batch_result.columns else 0
        rechazadas = len(batch_result) - aprobadas
        avg_util   = float(batch_result["Helpfulness"].mean()) if "Helpfulness" in batch_result.columns else 0.0
        with m1:
            render_metric_card("Total", str(len(batch_result)), "Resenas en el lote")
        with m2:
            render_metric_card("Aprobadas", str(aprobadas), "Utilidad >= 0.70")
        with m3:
            render_metric_card("Rechazadas", str(rechazadas), "Baja calidad o punto ciego")
        with m4:
            render_metric_card("Utilidad media", format_percentage(avg_util), "Promedio del lote")
        st.dataframe(batch_result, use_container_width=True, hide_index=True)
        st.download_button(
            "Descargar resultado CSV",
            data=batch_result.to_csv(index=False).encode("utf-8-sig"),
            file_name="resultado_lote_auditoria.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown('<div class="section-label">Resenas guardadas del producto</div>', unsafe_allow_html=True)
    saved_df = get_audited_reviews_operational_table()
    if not saved_df.empty:
        filt = (
            saved_df[saved_df["ProductId"].astype(str) == selected_product]
            if "ProductId" in saved_df.columns
            else saved_df
        )
        if not filt.empty:
            filt = filt.copy()
            if "CreatedAt" in filt.columns:
                filt["CreatedAt"] = pd.to_datetime(filt["CreatedAt"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")
            st.dataframe(filt, use_container_width=True, hide_index=True)
            st.download_button(
                "Descargar resenas guardadas",
                data=filt.to_csv(index=False).encode("utf-8-sig"),
                file_name="resenas_guardadas.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.info("No hay resenas guardadas para este producto.")
    else:
        st.info("No hay resenas guardadas aun.")

st.session_state["selected_product_id"] = selected_product
st.session_state["latest_stars"]        = stars if "stars" in dir() else 5
st.session_state["latest_review_text"]  = review_text if "review_text" in dir() else ""