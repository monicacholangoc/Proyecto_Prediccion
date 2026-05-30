"""Ranking y benchmark de reseñas.

Comparación por producto, posición del usuario y top 5.
Sin emojis, indicadores compactos.
"""

import pandas as pd
import streamlit as st

from components.cards import render_metric_card, render_review_card
from services.catalog_service import get_product_detail, get_product_options
from services.preprocessing_service import (
    get_audited_reviews_operational_table,
    get_global_ranking,
    get_local_product_ranking,
    get_position_summary,
    get_product_reviews_by_date,
    get_review_context_window,
)
from utils.formatters import format_compact_number, format_percentage


st.title("Ranking y Benchmark")
st.caption("Comparación de reseñas por producto. Analiza una reseña en Auditoría para ver tu posición.")

product_options  = get_product_options()
saved_reviews_df = get_audited_reviews_operational_table()

if not product_options:
    st.warning("No hay productos disponibles en el catálogo.")
    st.stop()

# ── Filtros ────────────────────────────────────────────────────────────────────

f1, f2 = st.columns(2, gap="medium")
with f1:
    selected_product = st.selectbox("Producto", options=product_options)
with f2:
    selected_status = st.selectbox(
        "Estado",
        options=["Todos", "APROBADA (Publicada)", "RECHAZADA (Baja Calidad)", "RECHAZADA (Punto Ciego)"],
    )

detail = get_product_detail(selected_product)
st.info(
    f"**{detail['ProductName']}** · `{detail['ProductId']}` · Categoría: {detail['Categoria_Real']}"
)

# ── Datos ──────────────────────────────────────────────────────────────────────

ranking_df         = get_local_product_ranking(selected_product)
global_ranking_df  = get_global_ranking()
product_history_df = get_product_reviews_by_date(selected_product, ascending=False)
latest_review_id   = st.session_state.get("latest_review_id")
position_summary   = get_position_summary(selected_product, latest_review_id)
review_window_df   = get_review_context_window(selected_product, latest_review_id, window_size=2)

if selected_status != "Todos":
    if "Estado" in ranking_df.columns:
        ranking_df = ranking_df[ranking_df["Estado"] == selected_status]
    if "Estado" in product_history_df.columns:
        product_history_df = product_history_df[product_history_df["Estado"] == selected_status]

# ── Indicadores del producto ───────────────────────────────────────────────────

top_score    = float(ranking_df["Helpfulness"].max())  if not ranking_df.empty else 0.0
avg_score    = float(ranking_df["Helpfulness"].mean()) if not ranking_df.empty else 0.0
review_count = len(ranking_df)
top_user     = str(ranking_df.iloc[0]["User"]) if not ranking_df.empty else "Sin datos"

st.markdown("### Indicadores del producto")
m1, m2, m3, m4 = st.columns(4, gap="medium")
with m1:
    render_metric_card("Reseñas", format_compact_number(review_count), "Base competitiva local")
with m2:
    render_metric_card("Utilidad máxima", format_percentage(top_score), "Mejor score observado")
with m3:
    render_metric_card("Utilidad media", format_percentage(avg_score), "Promedio local del producto")
with m4:
    render_metric_card("Líder actual", top_user[:22], "Usuario mejor posicionado")

# ── Top 5 ──────────────────────────────────────────────────────────────────────

st.markdown("### Top 5 del producto")

position_labels = ["1er lugar", "2do lugar", "3er lugar", "4to lugar", "5to lugar"]
top5 = ranking_df.head(5) if not ranking_df.empty else pd.DataFrame()

if not top5.empty:
    for i, (_, row) in enumerate(top5.iterrows()):
        pos_label = position_labels[i] if i < len(position_labels) else f"{i+1}."
        user      = str(row.get("User", "—"))
        stars     = int(row.get("Stars", 0))
        score     = float(row.get("Helpfulness", 0))
        estado    = str(row.get("Estado", "—"))
        is_top    = i == 0

        filled = "&#9733;" * stars
        empty  = "&#9734;" * max(0, 5 - stars)

        st.markdown(
            f"""
            <div class="review-card{'  review-card-highlighted' if is_top else ''}">
                <div class="review-card-header">
                    <div class="review-user">
                        <span class="metric-badge metric-badge-info" style="margin-right:0.4rem">{pos_label}</span>
                        {user}
                    </div>
                    <div class="review-badge">{estado}</div>
                </div>
                <div class="review-stars" style="color:#f59e0b">{filled}{empty}</div>
                <div class="review-helpfulness">Utilidad: <strong>{format_percentage(score)}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.info("No hay reseñas disponibles para los filtros seleccionados.")

# ── Posición del usuario ───────────────────────────────────────────────────────

st.markdown("### Tu reseña en contexto")

p1, p2, p3 = st.columns(3, gap="medium")
with p1:
    render_metric_card(
        "Posición local",
        f"{position_summary['local_rank']} / {position_summary['product_count']}"
        if position_summary["local_rank"] else "Sin reseña evaluada",
        "Lugar dentro del producto",
    )
with p2:
    render_metric_card(
        "Posición global",
        f"{position_summary['global_rank']} / {position_summary['global_count']}"
        if position_summary["global_rank"] else "Sin reseña evaluada",
        "Lugar en toda la base",
    )
with p3:
    render_metric_card(
        "Total del producto",
        format_compact_number(position_summary["product_count"]),
        "Volumen histórico de reseñas",
    )

if latest_review_id and not review_window_df.empty:
    for _, row in review_window_df.iterrows():
        meta_line = f"Puesto local {int(row['Puesto Local'])}"
        badge     = "Tu reseña" if row["EsActual"] else row["Estado"]
        render_review_card(
            user_name=str(row["User"]),
            stars=int(row["Stars"]),
            review_text=str(row["Text"]),
            meta_line=meta_line,
            badge=badge,
            helpfulness=format_percentage(float(row["Helpfulness"])),
            highlighted=bool(row["EsActual"]),
        )
else:
    st.info("Analiza una reseña en Auditoría para ver tu posición aquí.")

# ── Historial reciente ─────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Historial reciente del producto")

if not product_history_df.empty:
    preview = product_history_df.head(10).copy()
    preview["CreatedAt"] = preview["CreatedAt"].dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(
        preview[["CreatedAt", "User", "Stars", "Helpfulness", "Estado", "Text"]],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No hay historial disponible para los filtros actuales.")

# ── Reseñas guardadas ──────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Reseñas guardadas")

filtered_saved = saved_reviews_df.copy()
if not filtered_saved.empty:
    if "ProductId" in filtered_saved.columns:
        filtered_saved = filtered_saved[filtered_saved["ProductId"].astype(str) == selected_product]
    if selected_status != "Todos" and "Estado" in filtered_saved.columns:
        filtered_saved = filtered_saved[filtered_saved["Estado"] == selected_status]

if not filtered_saved.empty:
    if "CreatedAt" in filtered_saved.columns:
        filtered_saved["CreatedAt"] = pd.to_datetime(
            filtered_saved["CreatedAt"], errors="coerce"
        ).dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(filtered_saved, use_container_width=True, hide_index=True)
    csv_bytes = filtered_saved.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Descargar reseñas filtradas (CSV)",
        data=csv_bytes,
        file_name="reseñas_filtradas.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("No hay reseñas guardadas para los filtros seleccionados.")

# ── Top 20 global ──────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Top 20 global por utilidad")
st.dataframe(global_ranking_df.head(20), use_container_width=True, hide_index=True)