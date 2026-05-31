"""Pagina de auditoria en tiempo real.

Recibe una reseña, consulta la capa de servicios y devuelve una salida
lista para usuario final: score, estado y diagnostico resumido.
"""

import pandas as pd
import streamlit as st

from components.cards import render_highlight_card, render_metric_card, render_review_card
from components.feedback import render_bullet_panel, render_info_panel, render_status_panel
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


# ── CSS visual mejorado ───────────────────────────────────────────────────────
st.markdown("""
<style>
.feat-grid { display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; margin-bottom:0.6rem; }
.feat-card {
    background:#fff; border:1px solid #e2e8f0; border-radius:12px;
    padding:0.7rem 0.8rem; position:relative; overflow:hidden;
    box-shadow:0 1px 3px rgba(0,0,0,0.04);
}
.feat-card::before { content:""; position:absolute; left:0; top:0; bottom:0; width:3px; border-radius:3px 0 0 3px; }
.feat-card-green::before { background:#15803d; }
.feat-card-amber::before { background:#b45309; }
.feat-card-blue::before  { background:#1d4ed8; }
.feat-card-red::before   { background:#dc2626; }
.feat-lbl { font-size:0.6rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.07em; margin-bottom:0.2rem; }
.feat-val { font-size:1rem; font-weight:800; color:#0f172a; line-height:1.2; margin-bottom:0.15rem; }
.feat-cap { font-size:0.62rem; color:#94a3b8; margin-bottom:0.25rem; }
.feat-badge { display:inline-block; font-size:0.6rem !important; font-weight:700; padding:0.12rem 0.45rem !important; border-radius:999px; color:#fff !important; }
.feat-green { background:#15803d; } .feat-amber { background:#b45309; }
.feat-blue  { background:#1d4ed8; } .feat-red   { background:#dc2626; }
.feat-gray  { background:#64748b; }
.diag-card { border-radius:14px; padding:1rem 1.1rem; margin-top:0.5rem; border:1px solid; position:relative; }
.diag-success { background:#f0fdf4; border-color:#86efac; }
.diag-warning { background:#fffbeb; border-color:#fcd34d; }
.diag-danger  { background:#fef2f2; border-color:#fca5a5; }
.diag-title { font-size:0.65rem; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.3rem; }
.diag-success .diag-title { color:#15803d; } .diag-warning .diag-title { color:#b45309; } .diag-danger .diag-title { color:#dc2626; }
.diag-decision { font-size:1.05rem; font-weight:800; color:#0f172a; margin-bottom:0.3rem; }
.diag-reason   { font-size:0.75rem; color:#475569; line-height:1.5; max-width:72%; }
.diag-prob { font-size:1.6rem; font-weight:900; position:absolute; right:1rem; top:50%; transform:translateY(-50%); }
.diag-success .diag-prob { color:#15803d; } .diag-warning .diag-prob { color:#b45309; } .diag-danger .diag-prob { color:#dc2626; }
</style>
""", unsafe_allow_html=True)

st.title("Auditoría en Tiempo Real")
st.caption("Espacio central del producto para evaluar reseñas y dar retroalimentación.")

product_options = get_product_options()

if not product_options:
    st.warning("No hay productos disponibles en el catalogo para auditar.")
    st.stop()

left_col, right_col = st.columns([1.1, 1], gap="large")

with left_col:
    st.markdown(
        """
        <div class="section-panel">
            <div class="section-kicker">Entrada operativa</div>
            <h3>Evalúa una reseña antes de publicarla</h3>
            <p>
                Esta herramienta simula el flujo de revisión de una reseña y estima
                si será percibida como útil por otros compradores.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_product = st.selectbox("Producto", options=product_options)
    product_detail = get_product_detail(selected_product)
    if product_detail:
        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
                    padding:0.6rem 1rem;margin-bottom:0.5rem">
            <div style="display:flex;gap:2rem;flex-wrap:wrap">
                <div>
                    <div style="font-size:0.6rem;font-weight:700;color:#94a3b8;text-transform:uppercase">Producto</div>
                    <div style="font-size:0.88rem;font-weight:700;color:#0f172a">{product_detail['ProductName']}</div>
                </div>
                <div>
                    <div style="font-size:0.6rem;font-weight:700;color:#94a3b8;text-transform:uppercase">Categoria</div>
                    <div style="font-size:0.88rem;font-weight:700;color:#1d4ed8">{product_detail['Categoria_Real']}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
    validate_context = st.toggle(
        "Activar validación de contexto / punto ciego",
        value=True,
        help=(
            "Si está activo, la app revisa si la reseña realmente habla del "
            "producto o categoría seleccionados, además de medir utilidad."
        ),
    )
    stars = st.slider("Calificación en estrellas", min_value=1, max_value=5, value=5)
    user_name = st.text_input("Perfil de usuario", value="Auditor_Seminario")
    review_text = st.text_area("Texto de la reseña", height=200)
    analyze_review = st.button("Analizar reseña", type="primary")

    # La accion principal se delega al service para no mezclar UI con negocio.
    if analyze_review:
        if not is_non_empty_text(review_text):
            st.warning("Ingresa una reseña antes de analizar.")
        else:
            audit_result = append_audited_review(
                selected_product,
                user_name,
                stars,
                review_text,
                validate_context=validate_context,
            )
            st.session_state["latest_audit_result"] = audit_result

    st.markdown("#### Carga masiva")
    uploaded_file = st.file_uploader(
        "Sube un CSV para auditoría por lotes",
        type=["csv"],
        help="Debe incluir ProductId, ProfileName, Score y Text.",
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
                st.success(f"Lote procesado correctamente: {len(batch_df)} reseñas agregadas.")
                st.dataframe(batch_df.head(20), use_container_width=True)

with right_col:
    lr   = st.session_state.get("latest_audit_result")
    prob = lr["probability"] if lr else 0.0
    st.plotly_chart(build_helpfulness_gauge(prob), use_container_width=True)

    # ── Características calculadas ────────────────────────────────────────────
    st.markdown('<div class="section-label" style="margin-bottom:0.4rem">Caracteristicas calculadas</div>', unsafe_allow_html=True)
    rl   = lr["review_len"] if lr else 0
    incoh = lr["incoherente"] if lr else False
    sv   = st.session_state.get("latest_stars", 5)
    sent = lr.get("sentiment_score") if lr else None

    lb = "feat-green" if rl > 60 else "feat-amber"
    ll = "Adecuada" if rl > 60 else "Corta"
    card_len = "feat-card-green" if rl > 60 else "feat-card-amber"
    len_pct  = min(int(rl / 80 * 100), 100)
    len_color = "#15803d" if rl > 80 else ("#b45309" if rl > 40 else "#dc2626")

    if sent is not None:
        sl = "Positivo" if sent > 0.05 else ("Negativo" if sent < -0.05 else "Neutro")
        sb = "feat-green" if sent > 0.05 else ("feat-red" if sent < -0.05 else "feat-blue")
        card_sent = "feat-card-green" if sent > 0.05 else ("feat-card-red" if sent < -0.05 else "feat-card-blue")
        ss = f"{sent:.2f}"
        sent_pct = min(int((sent + 1) / 2 * 100), 100)
        sent_color = "#15803d" if sent > 0.05 else "#dc2626"
    else:
        sl, sb, ss, card_sent = "Pendiente", "feat-gray", "-", "feat-card-blue"
        sent_pct, sent_color = 50, "#94a3b8"

    cl = "Coherente" if not incoh else "Incoherente"
    cb = "feat-green" if not incoh else "feat-amber"
    card_coh = "feat-card-green" if not incoh else "feat-card-amber"

    st.markdown(f"""
    <div class="feat-grid">
        <div class="feat-card {card_len}">
            <div class="feat-lbl">Longitud</div>
            <div class="feat-val">{rl} palabras</div>
            <div style="background:#f1f5f9;border-radius:999px;height:4px;margin:0.25rem 0;overflow:hidden">
                <div style="width:{len_pct}%;height:100%;background:{len_color};border-radius:999px"></div>
            </div>
            <div class="feat-cap">Umbral: 80 palabras</div>
            <span class="feat-badge {lb}">{ll}</span>
        </div>
        <div class="feat-card {card_sent}">
            <div class="feat-lbl">Sentimiento</div>
            <div class="feat-val">{ss}</div>
            <div style="background:#f1f5f9;border-radius:999px;height:4px;margin:0.25rem 0;overflow:hidden">
                <div style="width:{sent_pct}%;height:100%;background:{sent_color};border-radius:999px"></div>
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
        <div class="feat-card {card_coh}">
            <div class="feat-lbl">Coherencia</div>
            <div class="feat-val">{cl}</div>
            <div style="background:#f1f5f9;border-radius:999px;height:4px;margin:0.25rem 0;overflow:hidden">
                <div style="width:{"100" if not incoh else "30"}%;height:100%;background:{"#15803d" if not incoh else "#b45309"};border-radius:999px"></div>
            </div>
            <div class="feat-cap">Tono vs. estrellas</div>
            <span class="feat-badge {cb}">{cl}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Diagnóstico visual ────────────────────────────────────────────────────
    st.markdown('<div class="section-label" style="margin-top:0.5rem;margin-bottom:0.3rem">Diagnostico</div>', unsafe_allow_html=True)
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
            razon = "El sentimiento es negativo. Revisa la coherencia con las estrellas."
        else:
            razon = f"Utilidad de {format_percentage(prob)}, por debajo del umbral del 70%."

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
                f'''<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
                            padding:0.55rem 0.8rem;margin-top:0.4rem">
                    <div style="font-size:0.6rem;font-weight:700;color:#94a3b8;text-transform:uppercase;
                                letter-spacing:.07em;margin-bottom:0.2rem">Contexto alimenticio</div>
                    <div style="font-size:0.72rem;color:#475569;line-height:1.5">{lr.get("context_explanation","")}</div>
                    <div style="margin-top:0.3rem;font-size:0.68rem;color:#64748b">
                        <b>Detectadas:</b> {ctx} &nbsp;·&nbsp; <b>Ajenas:</b> {tech}
                    </div></div>''',
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

st.markdown("### Lectura del Resultado")
result_cols = st.columns(4, gap="medium")
latest_result = st.session_state.get("latest_audit_result")
probability = latest_result["probability"] if latest_result else 0.0
review_len = latest_result["review_len"] if latest_result else 0
incoherence = latest_result["incoherente"] if latest_result else False
product_benchmark = get_product_benchmark(selected_product)
latest_review_id = st.session_state.get("latest_review_id")
position_summary = get_position_summary(selected_product, latest_review_id)
review_window_df = get_review_context_window(selected_product, latest_review_id, window_size=1)
product_history_df = get_product_reviews_by_date(selected_product, ascending=False)

with result_cols[0]:
    render_metric_card("Utilidad estimada", format_percentage(probability), "Probabilidad calculada por la capa de scoring")
with result_cols[1]:
    render_metric_card("Longitud", f"{review_len} palabras", "Cantidad de palabras detectadas en la reseña")
with result_cols[2]:
    render_metric_card("Incoherencia", "Sí" if incoherence else "No", "Consistencia básica entre tono y estrellas")
with result_cols[3]:
    blind_spot_label = "Punto ciego" if latest_result and latest_result.get("context_blind_spot") else "Estado"
    blind_spot_value = "Detectado" if latest_result and latest_result.get("context_blind_spot") else (latest_result["status"] if latest_result else "Sin evaluar")
    blind_spot_caption = "Resultado contextual actual" if latest_result and latest_result.get("context_validation_enabled") else "Resultado operativo actual"
    render_metric_card(blind_spot_label, blind_spot_value, blind_spot_caption)

position_cols = st.columns(3, gap="medium")
with position_cols[0]:
    render_metric_card(
        "Posición local",
        f"{position_summary['local_rank']} / {position_summary['product_count']}" if position_summary["local_rank"] else "Sin posición",
        "Lugar estimado dentro del producto",
    )
with position_cols[1]:
    render_metric_card(
        "Posición global",
        f"{position_summary['global_rank']} / {position_summary['global_count']}" if position_summary["global_rank"] else "Sin posición",
        "Lugar estimado en toda la base visible",
    )
with position_cols[2]:
    render_metric_card(
        "Reseñas del producto",
        str(position_summary["product_count"]),
        "Volumen histórico del artículo seleccionado",
    )

advice_left, advice_right = st.columns([1, 1], gap="large")
with advice_left:
    if latest_result:
        recommendations = generate_review_recommendations(latest_result)
        render_highlight_card(
            "Recomendación principal",
            "Mejora sugerida",
            recommendations[0],
        )
    else:
        render_highlight_card(
            "Recomendación principal",
            "Esperando análisis",
            "Una vez analices una reseña, aquí aparecerá la recomendación más importante para mejorarla.",
        )
with advice_right:
    render_bullet_panel(
        "Buenas prácticas para una reseña útil",
        [
            "Describe el contexto real de uso del producto.",
            "Explica beneficios o problemas concretos, no solo opinión general.",
            "Mantén coherencia entre el texto escrito y la calificación en estrellas.",
        ],
    )

benchmark_left, benchmark_right = st.columns(2, gap="large")
with benchmark_left:
    render_bullet_panel(
        "Comparación contra el histórico",
        [
            f"Promedio del producto: {format_percentage(product_benchmark['avg_helpfulness'])}.",
            f"Mejor score del producto: {format_percentage(product_benchmark['top_helpfulness'])}.",
            f"Volumen histórico visible: {product_benchmark['count']} reseñas.",
        ],
    )
with benchmark_right:
    if latest_result:
        delta_vs_avg = latest_result["probability"] - product_benchmark["avg_helpfulness"]
        comparison_text = (
            "Tu reseña está por encima del promedio histórico del producto."
            if delta_vs_avg >= 0
            else "Tu reseña está por debajo del promedio histórico del producto."
        )
        render_highlight_card(
            "Benchmark",
            f"{delta_vs_avg:+.1%}",
            comparison_text,
        )
    else:
        render_highlight_card(
            "Benchmark",
            "Sin comparación",
            "Analiza una reseña para contrastarla contra el promedio histórico del producto.",
        )

if latest_result:
    st.markdown("### Explicación para el usuario")
    render_info_panel(
        "Cómo interpretar este score",
        f"El sistema estimó una utilidad de {format_percentage(probability)}. "
        f"Esto se apoya en señales como longitud textual, coherencia general y estructura de la reseña. "
        f"Si el score no es alto, la estrategia correcta no es cambiar la nota, sino mejorar la calidad del contenido escrito.",
    )
    render_bullet_panel("Sugerencias automáticas", recommendations)

    save_left, save_right = st.columns([0.7, 1.3], gap="large")
    with save_left:
        save_review = st.button("Grabar reseña", use_container_width=True)
    with save_right:
        if save_review:
            saved_ok, save_message = save_latest_review_to_file(selected_product)
            if saved_ok:
                st.success(save_message)
            else:
                st.warning(save_message)

    st.markdown("### Vista previa tipo plataforma")
    created_at_display = pd.Timestamp.now().strftime("%d/%m/%Y")
    render_review_card(
        user_name=user_name,
        stars=stars,
        review_text=review_text,
        meta_line=f"{product_detail['ProductName']} | {product_detail['Categoria_Real']} | {created_at_display}",
        badge=latest_result["status"],
        helpfulness=format_percentage(probability),
        highlighted=True,
    )

    st.markdown("### Tu reseña en contexto del producto")
    if review_window_df.empty:
        render_info_panel(
            "Ventana contextual no disponible",
            "Todavía no fue posible ubicar la reseña dentro del ranking local del producto.",
        )
    else:
        for _, row in review_window_df.iterrows():
            meta_line = (
                f"Puesto local {int(row['Puesto Local'])} | "
                f"{pd.to_datetime(row['CreatedAt']).strftime('%d/%m/%Y') if 'CreatedAt' in row and pd.notna(row['CreatedAt']) else 'Sin fecha'}"
            )
            badge = "Tu reseña evaluada" if row["EsActual"] else row["Estado"]
            render_review_card(
                user_name=str(row["User"]),
                stars=int(row["Stars"]),
                review_text=str(row["Text"]),
                meta_line=meta_line,
                badge=badge,
                helpfulness=format_percentage(float(row["Helpfulness"])),
                highlighted=bool(row["EsActual"]),
            )

st.markdown("### Historial del producto por fecha")
history_preview = product_history_df.head(10).copy()
if not history_preview.empty:
    history_preview["CreatedAt"] = pd.to_datetime(history_preview["CreatedAt"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(
        history_preview[["CreatedAt", "User", "Stars", "Helpfulness", "Estado", "Text"]],
        use_container_width=True,
    )

st.markdown("### Archivo operativo de reseñas guardadas")
saved_reviews_df = get_audited_reviews_operational_table()
if saved_reviews_df.empty:
    st.info("Aún no hay reseñas guardadas en el CSV operativo separado.")
else:
    st.dataframe(saved_reviews_df.tail(20), use_container_width=True)

st.session_state["selected_product_id"] = selected_product
st.session_state["latest_stars"] = stars
st.session_state["latest_review_text"] = review_text