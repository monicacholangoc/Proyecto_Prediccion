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
        st.info(
            f"Producto: {product_detail['ProductName']}\n\n"
            f"Categoria: {product_detail['Categoria_Real']}"
        )
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
    latest_result = st.session_state.get("latest_audit_result")
    probability = latest_result["probability"] if latest_result else 0.0
    st.plotly_chart(build_helpfulness_gauge(probability), use_container_width=True)

    if latest_result:
        if "Punto Ciego" in latest_result["status"]:
            tone = "danger"
            recommendation = "Reescribe el texto para que hable del producto correcto y agrega experiencia concreta de uso."
            decision = "Revisión obligatoria"
        elif latest_result["probability"] >= 0.70:
            tone = "success"
            recommendation = "La reseña ya tiene buena señal de utilidad. Puedes reforzarla con detalles de contexto y uso real."
            decision = "Lista para publicar"
        else:
            tone = "warning"
            recommendation = "Agrega más detalle, beneficios concretos y una explicación más clara para elevar la utilidad percibida."
            decision = "Conviene mejorarla"

        render_status_panel(
            "Diagnóstico actual",
            decision,
            f"Estado del sistema: {latest_result['status']}. Utilidad estimada: {format_percentage(latest_result['probability'])}.",
            tone=tone,
        )
        if latest_result.get("context_validation_enabled"):
            render_info_panel(
                "Validación de contexto",
                (
                    f"{latest_result['context_explanation']} "
                    f"Coincidencias de contexto: {', '.join(latest_result['context_hits']) if latest_result['context_hits'] else 'ninguna clara'}. "
                    f"Términos ajenos detectados: {', '.join(latest_result['tech_hits']) if latest_result['tech_hits'] else 'ninguno'}."
                ),
            )
    else:
        render_info_panel(
            "Diagnóstico inicial",
            "Aquí mostraremos la probabilidad de utilidad, la coherencia del texto con las estrellas "
            "y recomendaciones accionables para mejorar la reseña.",
        )

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
