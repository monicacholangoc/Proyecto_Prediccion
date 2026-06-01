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
/* ── Config header ───────────────────────────────── */
.config-header {
    display:flex; align-items:center; gap:0.5rem;
    background:linear-gradient(135deg,#1746a2,#0f4c5c);
    border-radius:10px; padding:0.6rem 0.9rem; margin-bottom:0.9rem;
}
.config-header-icon {
    width:26px; height:26px; border-radius:7px;
    background:rgba(255,255,255,.18);
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
}
.config-header-title {
    font-size:0.7rem; font-weight:800; color:#fff !important;
    text-transform:uppercase; letter-spacing:0.07em;
}
/* ── KPI cards — fondo oscuro auto-contenido ──── */
.feat-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.55rem; margin-bottom:0.5rem; }
.feat-card {
    background:#1e293b; border:1px solid rgba(255,255,255,0.1);
    border-radius:12px; display:flex; flex-direction:row; overflow:hidden; min-height:82px;
}
.feat-stripe { width:5px; flex-shrink:0; }
.stripe-green { background:#22c55e; }
.stripe-amber { background:#f59e0b; }
.stripe-blue  { background:#60a5fa; }
.stripe-red   { background:#f87171; }
.feat-icon-wrap { display:flex; align-items:center; justify-content:center; width:38px; flex-shrink:0; }
.icon-sq { width:26px; height:26px; border-radius:6px; display:flex; align-items:center; justify-content:center; }
.icon-green { background:rgba(34,197,94,.2);   color:#4ade80; }
.icon-amber { background:rgba(245,158,11,.2);  color:#fbbf24; }
.icon-blue  { background:rgba(96,165,250,.2);  color:#93c5fd; }
.icon-red   { background:rgba(248,113,113,.2); color:#fca5a5; }
.feat-body { flex:1; padding:0.5rem 0.6rem 0.5rem 0.2rem; display:flex; flex-direction:column; justify-content:space-between; min-width:0; }
.feat-lbl { font-size:0.55rem; font-weight:700; color:#94a3b8 !important; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.08rem; }
.feat-val { font-size:1.1rem; font-weight:800; color:#f1f5f9 !important; line-height:1.1; }
.feat-stars { font-size:0.95rem; color:#fbbf24 !important; letter-spacing:2px; }
.feat-bar-wrap { position:relative; padding-top:14px; }
.feat-bar-pct { font-size:0.55rem; font-weight:700; color:#94a3b8 !important; position:absolute; right:0; top:1px; }
.feat-bar-bg { background:rgba(255,255,255,.1); border-radius:3px; height:4px; overflow:hidden; }
.feat-bar-fg { height:100%; border-radius:3px; }
.feat-badge { display:inline-block; font-size:0.55rem; font-weight:700; padding:0.1rem 0.45rem; border-radius:4px; margin-top:0.28rem; }
.badge-green { background:rgba(34,197,94,.18);   color:#86efac !important; }
.badge-amber { background:rgba(245,158,11,.18);  color:#fde68a !important; }
.badge-blue  { background:rgba(96,165,250,.18);  color:#bfdbfe !important; }
.badge-red   { background:rgba(248,113,113,.18); color:#fecaca !important; }
.kpi-sec-lbl { font-size:0.58rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.08em; border-left:3px solid #1746a2; padding-left:0.45rem; margin:0.6rem 0 0.4rem; }
/* ── Diagnóstico ─────────────────────────────── */
.diag-section-wrap { background:#fff; border:1px solid #e2e8f0; border-radius:16px; padding:1.1rem 1.3rem; margin-top:0.8rem; }
.diag-section-eyebrow { font-size:0.6rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.09em; border-left:3px solid #1746a2; padding-left:0.5rem; margin-bottom:0.85rem; }
.diag-card { border-radius:12px; padding:1rem 1.1rem; border:1px solid; position:relative; overflow:hidden; }
.diag-card::before { content:""; position:absolute; left:0; top:0; bottom:0; width:5px; }
.diag-success { background:#f0fdf8; border-color:#6ee7b7; }
.diag-warning { background:#fffbeb; border-color:#fcd34d; }
.diag-danger  { background:#fff1f2; border-color:#fca5a5; }
.diag-success::before { background:#22c55e; }
.diag-warning::before { background:#f59e0b; }
.diag-danger::before  { background:#f87171; }
.diag-eyebrow { font-size:0.58rem; font-weight:700; text-transform:uppercase; letter-spacing:0.09em; margin-bottom:0.45rem; }
.diag-success .diag-eyebrow { color:#059669; }
.diag-warning .diag-eyebrow { color:#b45309; }
.diag-danger  .diag-eyebrow { color:#dc2626; }
.diag-row { display:flex; align-items:center; justify-content:space-between; gap:1rem; }
.diag-left { flex:1; min-width:0; }
.diag-decision { font-size:1.05rem; font-weight:800; color:#0f172a; }
.diag-reason   { font-size:0.74rem; color:#475569; line-height:1.5; margin-top:0.15rem; }
.diag-prob-block { flex-shrink:0; text-align:right; }
.diag-prob-val  { font-size:2.2rem; font-weight:900; letter-spacing:-0.03em; line-height:1; }
.diag-prob-lbl  { font-size:0.6rem; color:#94a3b8; margin-top:2px; }
.diag-success .diag-prob-val { color:#059669; }
.diag-warning .diag-prob-val { color:#b45309; }
.diag-danger  .diag-prob-val { color:#dc2626; }
.rec-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.65rem; margin-top:0.85rem; }
.rec-card { background:#f8fafc; border:1px solid #e8edf4; border-radius:11px; padding:0.8rem 0.9rem; border-top:3px solid #1746a2; }
.rec-card-warn { border-top-color:#f59e0b; }
.rec-eyebrow { font-size:0.58rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.07em; margin-bottom:0.35rem; }
.rec-body { font-size:0.8rem; color:#334155; line-height:1.5; }
.ctx-box { background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:0.65rem 0.9rem; margin-top:0.65rem; }
.ctx-lbl { font-size:0.58rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:.07em; margin-bottom:0.2rem; }
.ctx-txt  { font-size:0.73rem; color:#475569; line-height:1.5; }
.ctx-chips { display:flex; gap:0.5rem; margin-top:0.35rem; flex-wrap:wrap; }
.ctx-chip { font-size:0.68rem; padding:0.1rem 0.55rem; border-radius:4px; background:#fff; border:1px solid #e2e8f0; color:#64748b; }
.prod-info-bar { display:flex; gap:2rem; flex-wrap:wrap; align-items:center; background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:0.7rem 1.1rem; margin-bottom:1rem; }
.prod-info-field-lbl { font-size:0.6rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; }
.prod-info-field-val { font-size:0.9rem; font-weight:700; color:#0f172a; margin-top:0.1rem; }
.prod-info-field-val-accent { color:#1746a2; }
.prod-info-field-val-mono { font-family:monospace; color:#64748b; font-size:0.78rem; }
.diag-empty { background:#f8fafc; border:1px dashed #cbd5e1; border-radius:12px; padding:1.4rem; text-align:center; }
.diag-empty-icon { width:40px; height:40px; border-radius:10px; background:#e8edf4; display:flex; align-items:center; justify-content:center; margin:0 auto 0.6rem; }
.diag-empty-txt { font-size:0.8rem; color:#94a3b8; }
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
    f"""<div class="prod-info-bar">
        <div>
            <div class="prod-info-field-lbl">Producto</div>
            <div class="prod-info-field-val">{product_detail['ProductName']}</div>
        </div>
        <div>
            <div class="prod-info-field-lbl">Categoría</div>
            <div class="prod-info-field-val prod-info-field-val-accent">{product_detail['Categoria_Real']}</div>
        </div>
        <div>
            <div class="prod-info-field-lbl">ID Producto</div>
            <div class="prod-info-field-val prod-info-field-val-mono">{product_detail['ProductId']}</div>
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
    left_col, right_col = st.columns([1.05, 1], gap="medium")

    with left_col:
        # Marcador CSS para apuntar este panel (sin widgets dentro del div)
        st.markdown('<span class="audit-col-left" style="display:none"></span>', unsafe_allow_html=True)
        # Header visual de configuración (solo HTML estático, sin widgets dentro)
        st.markdown("""
        <div class="config-header">
            <div class="config-header-icon">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.07 4.93A10 10 0 0 0 4.93 19.07M4.93 4.93A10 10 0 0 1 19.07 19.07"/>
                </svg>
            </div>
            <span class="config-header-title">Configuración del análisis</span>
        </div>
        """, unsafe_allow_html=True)

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

    # Panel derecho — gauge Plotly + KPIs en HTML oscuro auto-contenido
    with right_col:
        lr   = st.session_state.get("latest_audit_result")
        prob = lr["probability"] if lr else 0.0

        st.plotly_chart(build_helpfulness_gauge(prob), use_container_width=True,
                        config={"displayModeBar": False})

        rl    = lr["review_len"]  if lr else 0
        incoh = lr["incoherente"] if lr else False
        sv    = st.session_state.get("latest_stars", 5)
        sent  = lr.get("sentiment_score") if lr else None

        if sent is not None:
            sl = "Positivo" if sent > 0.05 else ("Negativo" if sent < -0.05 else "Neutro")
            ss = f"{sent:.2f}"
        else:
            sl, ss = "Pendiente", "-"

        cl      = "Coherente" if not incoh else "Incoherente"
        len_pct = min(int(rl / 80 * 100), 100)

        len_color = "#22c55e" if rl > 80 else ("#f59e0b" if rl > 40 else "#f87171")
        len_top   = "green"   if rl > 60 else "amber"
        len_lbl   = "Adecuada" if rl > 60 else "Corta"
        len_badge = "badge-green" if rl > 60 else "badge-amber"

        sent_top     = "green" if (sent is not None and sent > 0.05) else ("red" if (sent is not None and sent < -0.05) else "blue")
        sent_badge   = "badge-green" if sent_top == "green" else ("badge-red" if sent_top == "red" else "badge-blue")
        sent_bar_clr = "#22c55e" if sent_top == "green" else ("#f87171" if sent_top == "red" else "#60a5fa")
        sent_bar_pct = min(int((float(ss) + 1) / 2 * 100), 100) if ss != "-" else 50

        coh_top     = "green" if not incoh else "amber"
        coh_badge   = "badge-green" if not incoh else "badge-amber"
        coh_bar_pct = 100 if not incoh else 30
        coh_bar_clr = "#22c55e" if not incoh else "#f59e0b"

        _ico_ruler = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><line x1="8" y1="9" x2="16" y2="9"/><line x1="8" y1="13" x2="12" y2="13"/></svg>'
        _ico_wave  = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>'
        _ico_star  = '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>'
        _ico_check = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'

        _icon_len  = "green" if len_top == "green" else "amber"
        _icon_coh  = "green" if coh_top == "green" else "amber"
        _stars_str = "★" * int(sv) + "☆" * (5 - int(sv))

        st.markdown(
            '<div class="kpi-sec-lbl">Características calculadas</div>'
            '<div class="feat-grid">'

            f'<div class="feat-card"><div class="feat-stripe stripe-{len_top}"></div>'
            f'<div class="feat-icon-wrap"><div class="icon-sq icon-{_icon_len}">{_ico_ruler}</div></div>'
            '<div class="feat-body"><div class="feat-lbl">Longitud</div>'
            f'<div class="feat-val">{rl} <span style="font-size:.68rem;opacity:.6">pal.</span></div>'
            f'<div class="feat-bar-wrap"><span class="feat-bar-pct">{len_pct}%</span>'
            f'<div class="feat-bar-bg"><div class="feat-bar-fg" style="width:{len_pct}%;background:{len_color}"></div></div></div>'
            f'<span class="feat-badge {len_badge}">{len_lbl} · umbral 80</span>'
            '</div></div>'

            f'<div class="feat-card"><div class="feat-stripe stripe-{sent_top}"></div>'
            f'<div class="feat-icon-wrap"><div class="icon-sq icon-{sent_top}">{_ico_wave}</div></div>'
            '<div class="feat-body"><div class="feat-lbl">Sentimiento</div>'
            f'<div class="feat-val">{ss}</div>'
            f'<div class="feat-bar-wrap"><span class="feat-bar-pct">{sent_bar_pct}%</span>'
            f'<div class="feat-bar-bg"><div class="feat-bar-fg" style="width:{sent_bar_pct}%;background:{sent_bar_clr}"></div></div></div>'
            f'<span class="feat-badge {sent_badge}">{sl} · VADER</span>'
            '</div></div>'

            f'<div class="feat-card"><div class="feat-stripe stripe-amber"></div>'
            f'<div class="feat-icon-wrap"><div class="icon-sq icon-amber">{_ico_star}</div></div>'
            '<div class="feat-body"><div class="feat-lbl">Calificación</div>'
            f'<div class="feat-stars">{_stars_str}</div>'
            f'<div class="feat-bar-wrap"><span class="feat-bar-pct">{int(sv/5*100)}%</span>'
            f'<div class="feat-bar-bg"><div class="feat-bar-fg" style="width:{int(sv/5*100)}%;background:#f59e0b"></div></div></div>'
            f'<span class="feat-badge badge-amber">{sv} / 5 estrellas</span>'
            '</div></div>'

            f'<div class="feat-card"><div class="feat-stripe stripe-{coh_top}"></div>'
            f'<div class="feat-icon-wrap"><div class="icon-sq icon-{_icon_coh}">{_ico_check}</div></div>'
            '<div class="feat-body"><div class="feat-lbl">Coherencia</div>'
            f'<div class="feat-val" style="font-size:.88rem">{cl}</div>'
            f'<div class="feat-bar-wrap"><span class="feat-bar-pct">{coh_bar_pct}%</span>'
            f'<div class="feat-bar-bg"><div class="feat-bar-fg" style="width:{coh_bar_pct}%;background:{coh_bar_clr}"></div></div></div>'
            f'<span class="feat-badge {coh_badge}">Tono vs. estrellas</span>'
            '</div></div>'

            '</div>',
            unsafe_allow_html=True,
        )

        # ── Diagnóstico — debajo de las KPIs en la columna derecha ────────
        _lr2   = st.session_state.get("latest_audit_result")
        _prob2 = _lr2["probability"] if _lr2 else 0.0
        _sent2 = _lr2.get("sentiment_score") if _lr2 else None
        _rl2   = _lr2["review_len"] if _lr2 else 0

        if _lr2:
            _is_blind2 = "Punto Ciego" in _lr2["status"]
            _diag_cls2 = "diag-danger" if _is_blind2 else ("diag-success" if _prob2 >= 0.70 else "diag-warning")
            _decision2 = "Revision obligatoria" if _is_blind2 else ("Lista para publicar" if _prob2 >= 0.70 else "Conviene mejorarla")
            if _is_blind2:
                _razon2 = "La resena no menciona contexto alimenticio relevante."
            elif _prob2 >= 0.70:
                _razon2 = "La resena supera el umbral de utilidad del 70%."
            elif _rl2 < 60:
                _razon2 = "La resena es muy corta. Se recomienda superar las 80 palabras."
            elif _sent2 is not None and _sent2 < -0.05:
                _razon2 = "El sentimiento del texto es negativo. Revisa la coherencia con las estrellas."
            else:
                _razon2 = f"Utilidad estimada de {format_percentage(_prob2)}, por debajo del umbral del 70%."

            _ctx2_html = ""
            if _lr2.get("context_validation_enabled"):
                _ctx2  = ", ".join(_lr2.get("context_hits", [])) or "ninguna"
                _tech2 = ", ".join(_lr2.get("tech_hits", []))    or "ninguno"
                _ctx2_html = (
                    '<div class="ctx-box">'
                    '<div class="ctx-lbl">Contexto alimenticio</div>'
                    f'<div class="ctx-txt">{_lr2.get("context_explanation","")}</div>'
                    '<div class="ctx-chips">'
                    f'<span class="ctx-chip">Detectadas: <b>{_ctx2}</b></span>'
                    f'<span class="ctx-chip">Ajenas: <b>{_tech2}</b></span>'
                    '</div></div>'
                )

            st.markdown(
                '<div class="diag-section-wrap">'
                '<div class="diag-section-eyebrow">Diagn\u00f3stico del an\u00e1lisis</div>'
                f'<div class="diag-card {_diag_cls2}">'
                '<div class="diag-eyebrow">Resultado del an\u00e1lisis</div>'
                '<div class="diag-row">'
                '<div class="diag-left">'
                f'<div class="diag-decision">{_decision2}</div>'
                f'<div class="diag-reason">{_razon2}</div>'
                '</div>'
                '<div class="diag-prob-block">'
                f'<div class="diag-prob-val">{format_percentage(_prob2)}</div>'
                '<div class="diag-prob-lbl">Probabilidad</div>'
                '</div>'
                '</div>'
                '</div>'
                f'{_ctx2_html}'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="diag-section-wrap">'
                '<div class="diag-section-eyebrow">Diagn\u00f3stico del an\u00e1lisis</div>'
                '<div class="diag-empty">'
                '<div class="diag-empty-icon">'
                '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" '
                'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<circle cx="11" cy="11" r="8"/>'
                '<line x1="21" y1="21" x2="16.65" y2="16.65"/>'
                '</svg>'
                '</div>'
                '<div class="diag-empty-txt">Escribe una rese\u00f1a y presiona <b>Analizar</b> para ver el diagn\u00f3stico</div>'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    # ── Recomendaciones + Guardar — debajo del botón Analizar (left_col) ──
    # Se ejecutan fuera de los with-cols, pero Streamlit los coloca
    # después del último widget de left_col gracias al orden de ejecución.
    # Usamos un contenedor de ancho completo para recomendaciones.
    _lr3 = st.session_state.get("latest_audit_result")
    if _lr3:
        _recs3 = generate_review_recommendations(_lr3)
        if _recs3:
            _r0 = _recs3[0] if len(_recs3) > 0 else ""
            _r1 = _recs3[1] if len(_recs3) > 1 else ""
            _rec_html3 = (
                '<div class="rec-card">'
                '<div class="rec-eyebrow">Acci\u00f3n principal</div>'
                f'<div class="rec-body">{_r0}</div>'
                '</div>'
            )
            if _r1:
                _rec_html3 += (
                    '<div class="rec-card rec-card-warn">'
                    '<div class="rec-eyebrow">Acci\u00f3n adicional</div>'
                    f'<div class="rec-body">{_r1}</div>'
                    '</div>'
                )
            with left_col:
                st.markdown(
                    f'<div class="rec-grid" style="margin-top:0.6rem">{_rec_html3}</div>',
                    unsafe_allow_html=True,
                )
                sv1, _ = st.columns([0.4, 0.6])
                with sv1:
                    if st.button("Guardar rese\u00f1a", use_container_width=True):
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