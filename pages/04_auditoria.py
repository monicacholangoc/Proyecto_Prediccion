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
from services.catalog_service import get_product_detail, get_product_options, get_product_catalog
from services.ml_service import generate_review_recommendations, audit_review_text, load_trained_model
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
.feat-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; margin-bottom:0.6rem; }
.feat-card {
    background:#fff; border:1px solid #e2e8f0; border-radius:12px;
    padding:0.7rem 0.8rem; position:relative; overflow:hidden;
    box-shadow:0 1px 3px rgba(0,0,0,0.04);
}
.feat-card::before {
    content:""; position:absolute; left:0; top:0; bottom:0;
    width:3px; border-radius:3px 0 0 3px;
}
.feat-card-green::before { background:#15803d; }
.feat-card-amber::before { background:#b45309; }
.feat-card-blue::before  { background:#1d4ed8; }
.feat-card-gray::before  { background:#94a3b8; }
.feat-card-red::before   { background:#dc2626; }
.feat-lbl { font-size:0.6rem; font-weight:700; color:#94a3b8; text-transform:uppercase;
            letter-spacing:0.07em; margin-bottom:0.2rem; }
.feat-val { font-size:1rem; font-weight:800; color:#0f172a; line-height:1.2; margin-bottom:0.15rem; }
.feat-cap { font-size:0.62rem; color:#94a3b8; margin-bottom:0.25rem; }
.feat-badge { display:inline-block; font-size:0.6rem !important; font-weight:700;
              padding:0.12rem 0.45rem !important; border-radius:999px; color:#fff !important; }
.feat-green { background:#15803d; }
.feat-amber { background:#b45309; }
.feat-blue  { background:#1d4ed8; }
.feat-gray  { background:#64748b; }
.feat-red   { background:#dc2626; }

.diag-card {
    border-radius:14px; padding:1rem 1.1rem; margin-top:0.5rem;
    border:1px solid; position:relative;
}
.diag-success { background:#f0fdf4; border-color:#86efac; }
.diag-warning { background:#fffbeb; border-color:#fcd34d; }
.diag-danger  { background:#fef2f2; border-color:#fca5a5; }
.diag-title { font-size:0.65rem; font-weight:800; text-transform:uppercase;
              letter-spacing:0.08em; margin-bottom:0.3rem; }
.diag-success .diag-title { color:#15803d; }
.diag-warning .diag-title { color:#b45309; }
.diag-danger  .diag-title { color:#dc2626; }
.diag-decision { font-size:1.05rem; font-weight:800; color:#0f172a; margin-bottom:0.3rem; }
.diag-reason   { font-size:0.75rem; color:#475569; line-height:1.5; }
.diag-prob { font-size:1.6rem; font-weight:900; position:absolute; right:1rem; top:50%;
             transform:translateY(-50%); }
.diag-success .diag-prob { color:#15803d; }
.diag-warning .diag-prob { color:#b45309; }
.diag-danger  .diag-prob { color:#dc2626; }
</style>
""", unsafe_allow_html=True)


def _api_url():
    try:
        return st.secrets["API_URL"].rstrip("/")
    except Exception:
        return os.getenv("API_URL", "https://proyecto-prediccion-v9qk.onrender.com").rstrip("/")


def _call_predict(review_text, stars, model_name="lgbm"):
    try:
        r = requests.post(
            _api_url() + "/reviews/predict_helpfulness",
            json={"review_text": review_text, "stars": stars, "model": model_name},
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

# ── Catálogo y filtro por categoría ──────────────────────────────────────────
catalog = get_product_catalog()

st.markdown('<div class="section-label">Selecciona categoría y producto a auditar</div>', unsafe_allow_html=True)

# Obtener categorías disponibles
if not catalog.empty and "Categoria_Real" in catalog.columns:
    categorias = ["Todas las categorías"] + sorted(catalog["Categoria_Real"].dropna().unique().tolist())
else:
    categorias = ["Todas las categorías"]

cat_col, prod_col = st.columns([1, 2], gap="medium")

with cat_col:
    selected_cat = st.selectbox(
        "Categoría",
        options=categorias,
        help="Filtra los productos por categoría de alimento"
    )

# Filtrar productos según categoría seleccionada
if not catalog.empty and selected_cat != "Todas las categorías" and "Categoria_Real" in catalog.columns:
    filtered_catalog = catalog[catalog["Categoria_Real"] == selected_cat]
    product_options = sorted(filtered_catalog["ProductId"].dropna().astype(str).unique().tolist())
else:
    product_options = get_product_options()

if not product_options:
    st.warning("No hay productos disponibles para esta categoría.")
    st.stop()

with prod_col:
    selected_product = st.selectbox(
        "Producto",
        options=product_options,
        help="Selecciona el producto sobre el que harás la reseña"
    )

product_detail = get_product_detail(selected_product)

# Info del producto seleccionado
st.markdown(
    f"""<div class="highlight-card" style="padding:0.6rem 1rem;margin-bottom:0.5rem">
        <div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:center">
            <div>
                <div class="highlight-title" style="font-size:0.65rem">Producto</div>
                <div style="font-size:0.88rem;font-weight:700;color:var(--text)">{product_detail['ProductName']}</div>
            </div>
            <div>
                <div class="highlight-title" style="font-size:0.65rem">Categoría</div>
                <div style="font-size:0.88rem;font-weight:700;color:var(--primary)">{product_detail['Categoria_Real']}</div>
            </div>
            <div>
                <div class="highlight-title" style="font-size:0.65rem">ID Producto</div>
                <div style="font-size:0.78rem;color:var(--muted);font-family:monospace">{product_detail['ProductId']}</div>
            </div>
        </div>
    </div>""",
    unsafe_allow_html=True,
)

st.markdown("---")
tab1, tab2 = st.tabs(["Resena individual", "Carga masiva CSV"])

# ==============================================================
# TAB 1
# ==============================================================
with tab1:
    left_col, right_col = st.columns([1.1, 1], gap="large")

    with left_col:
        st.markdown('<div class="section-label">Configuracion</div>', unsafe_allow_html=True)

        # ── Selector de modelo ────────────────────────────────────────────
        MODEL_OPTIONS = {
            "LightGBM (Principal)":        "lgbm",
            "Logistic Regression":         "logistic",
            "Heurística (sin modelo)":     "heuristic",
        }
        selected_model_label = st.selectbox(
            "Modelo de predicción",
            options=list(MODEL_OPTIONS.keys()),
            help="Selecciona el modelo que evaluará la utilidad de la reseña. LightGBM es el modelo ganador del proyecto.",
        )
        selected_model = MODEL_OPTIONS[selected_model_label]

        # Badge visual del modelo seleccionado
        model_colors = {"lgbm": "#15803d", "logistic": "#1d4ed8", "heuristic": "#b45309"}
        model_color  = model_colors.get(selected_model, "#64748b")
        st.markdown(
            f'<span style="background:{model_color};color:#fff;font-size:0.7rem;'
            f'font-weight:700;padding:0.2rem 0.6rem;border-radius:999px">'
            f'✓ {selected_model_label}</span>',
            unsafe_allow_html=True,
        )

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
                    api_r = _call_predict(review_text.strip(), stars, selected_model)
                st.session_state["_api_result"]       = api_r if "error" not in api_r else None
                st.session_state["_last_review_text"] = review_text.strip()
                st.session_state["_last_stars"]       = stars
                st.session_state["_last_product"]     = selected_product
                st.session_state["_toggle_prev_val"]  = validate_context
                if "error" in api_r:
                    st.error(f"API no disponible: {api_r['error']}")
                # Si la API respondió bien, usar su probabilidad
                # Si no, append_audited_review calcula con el modelo local
                audit_result = append_audited_review(
                    selected_product, user_name, stars,
                    review_text.strip(), validate_context=validate_context,
                )
                # Sobrescribir probabilidad con resultado de la API si está disponible
                api_result = st.session_state.get("_api_result")
                if api_result and "probability" in api_result:
                    audit_result = dict(audit_result)
                    audit_result["probability"] = float(api_result["probability"])
                    # Recalcular status según nueva probabilidad
                    if audit_result.get("context_blind_spot"):
                        audit_result["status"] = "RECHAZADA (Punto Ciego)"
                    elif audit_result["probability"] >= 0.70:
                        audit_result["status"] = "APROBADA (Publicada)"
                    else:
                        audit_result["status"] = "RECHAZADA (Baja Calidad)"
                    st.session_state["latest_audit_result"] = audit_result
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

        # Barra de progreso de longitud
        len_pct = min(int(rl / 80 * 100), 100)
        len_color = "#15803d" if rl > 80 else ("#b45309" if rl > 40 else "#dc2626")

        st.markdown(f"""
        <div class="feat-grid">
            <div class="feat-card feat-card-{'green' if rl > 60 else 'amber'}">
                <div class="feat-lbl">Longitud</div>
                <div class="feat-val">{rl} palabras</div>
                <div style="background:#f1f5f9;border-radius:999px;height:4px;margin:0.25rem 0;overflow:hidden">
                    <div style="width:{len_pct}%;height:100%;background:{len_color};border-radius:999px"></div>
                </div>
                <div class="feat-cap">Umbral: 80 palabras</div>
                <span class="feat-badge {'feat-green' if rl > 60 else 'feat-amber'}">{ll}</span>
            </div>
            <div class="feat-card feat-card-{'green' if sent is not None and sent > 0.05 else ('red' if sent is not None and sent < -0.05 else 'blue')}">
                <div class="feat-lbl">Sentimiento</div>
                <div class="feat-val">{ss}</div>
                <div style="background:#f1f5f9;border-radius:999px;height:4px;margin:0.25rem 0;overflow:hidden">
                    <div style="width:{min(int((float(ss) + 1) / 2 * 100), 100) if ss != '-' else 50}%;height:100%;background:{'#15803d' if sent is not None and sent > 0.05 else '#dc2626'};border-radius:999px"></div>
                </div>
                <div class="feat-cap">VADER (-1 a +1)</div>
                <span class="feat-badge {sb}">{sl}</span>
            </div>
            <div class="feat-card feat-card-blue">
                <div class="feat-lbl">Calificacion</div>
                <div class="feat-val" style="color:#f59e0b;letter-spacing:2px">{"★" * int(sv) + "☆" * (5 - int(sv))}</div>
                <div style="background:#f1f5f9;border-radius:999px;height:4px;margin:0.25rem 0;overflow:hidden">
                    <div style="width:{int(sv/5*100)}%;height:100%;background:#f59e0b;border-radius:999px"></div>
                </div>
                <div class="feat-cap">{sv} de 5 estrellas</div>
                <span class="feat-badge feat-blue">{sv} / 5</span>
            </div>
            <div class="feat-card feat-card-{'green' if not incoh else 'amber'}">
                <div class="feat-lbl">Coherencia</div>
                <div class="feat-val">{cl}</div>
                <div style="background:#f1f5f9;border-radius:999px;height:4px;margin:0.25rem 0;overflow:hidden">
                    <div style="width:{'100' if not incoh else '30'}%;height:100%;background:{'#15803d' if not incoh else '#b45309'};border-radius:999px"></div>
                </div>
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
            diag_cls = "diag-danger" if is_blind else ("diag-success" if prob >= 0.70 else "diag-warning")
            decision = "Revision obligatoria" if is_blind else ("Lista para publicar" if prob >= 0.70 else "Conviene mejorarla")

            if is_blind:
                razon = "La resena no menciona contexto alimenticio relevante."
            elif prob >= 0.70:
                razon = "La resena supera el umbral de utilidad del 70%."
            elif rl < 60:
                razon = "La resena es muy corta. Se recomienda superar las 80 palabras."
            elif sent is not None and sent < -0.05:
                razon = "El sentimiento del texto es negativo. Revisa la coherencia con las estrellas."
            else:
                razon = f"Utilidad estimada de {format_percentage(prob)}, por debajo del umbral del 70%."

            st.markdown(f"""
            <div class="diag-card {diag_cls}">
                <div class="diag-title">Resultado del analisis</div>
                <div class="diag-decision">{decision}</div>
                <div class="diag-reason">{razon}</div>
                <div class="diag-prob">{format_percentage(prob)}</div>
            </div>
            """, unsafe_allow_html=True)

            if lr.get("context_validation_enabled"):
                ctx  = ", ".join(lr.get("context_hits", [])) or "ninguna"
                tech = ", ".join(lr.get("tech_hits", []))    or "ninguno"
                st.markdown(
                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;'
                    f'padding:0.55rem 0.8rem;margin-top:0.4rem">'
                    f'<div style="font-size:0.6rem;font-weight:700;color:#94a3b8;text-transform:uppercase;'
                    f'letter-spacing:.07em;margin-bottom:0.2rem">Contexto alimenticio</div>'
                    f'<div style="font-size:0.72rem;color:#475569;line-height:1.5">'
                    f'{lr.get("context_explanation","")}</div>'
                    f'<div style="margin-top:0.3rem;font-size:0.68rem;color:#64748b">'
                    f'<b>Detectadas:</b> {ctx} &nbsp;·&nbsp; <b>Ajenas:</b> {tech}'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown("""
            <div style="background:#f8fafc;border:1px dashed #cbd5e1;border-radius:12px;
                        padding:1.2rem;text-align:center;margin-top:0.5rem">
                <div style="font-size:0.8rem;color:#94a3b8">
                    Escribe una resena y presiona Analizar para ver el diagnostico
                </div>
            </div>
            """, unsafe_allow_html=True)

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