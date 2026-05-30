"""Pagina de ranking y benchmark.

Su objetivo es comparar la posicion de reseñas dentro del historico
y preparar una narrativa de competencia por producto.
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
    get_visible_global_audit_table,
)
from utils.formatters import format_compact_number, format_percentage


st.title("Ranking y Benchmark")
st.caption("Comparación entre reseñas, productos y señales históricas del dataset.")

product_options = get_product_options()
saved_reviews_df = get_audited_reviews_operational_table()

if not product_options:
    st.warning("No hay productos disponibles en el catalogo para construir rankings.")
    st.stop()

filter_cols = st.columns(4, gap="medium")
with filter_cols[0]:
    selected_product = st.selectbox("Producto para ranking", options=product_options)
with filter_cols[1]:
    available_users = ["Todos"]
    if not saved_reviews_df.empty and "User" in saved_reviews_df.columns:
        available_users += sorted(saved_reviews_df["User"].dropna().astype(str).unique().tolist())
    selected_user = st.selectbox("Filtrar por usuario", options=available_users)
with filter_cols[2]:
    selected_status = st.selectbox(
        "Filtrar por estado",
        options=["Todos", "APROBADA (Publicada)", "RECHAZADA (Baja Calidad)", "RECHAZADA (Punto Ciego)"],
    )
with filter_cols[3]:
    selected_source = st.selectbox(
        "Fuente visible",
        options=["Todas", "Solo histórico operativo", "Solo reseñas guardadas"],
    )

detail = get_product_detail(selected_product)
st.info(
    f"Producto: {detail['ProductName']} (`{detail['ProductId']}`)\n\n"
    f"Categoria: {detail['Categoria_Real']}"
)

ranking_df = get_local_product_ranking(selected_product)
global_ranking_df = get_global_ranking()
global_df = get_visible_global_audit_table()
product_history_df = get_product_reviews_by_date(selected_product, ascending=False)
latest_review_id = st.session_state.get("latest_review_id")
position_summary = get_position_summary(selected_product, latest_review_id)
review_window_df = get_review_context_window(selected_product, latest_review_id, window_size=2)

filtered_saved_reviews = saved_reviews_df.copy()
if not filtered_saved_reviews.empty:
    if "ProductId" in filtered_saved_reviews.columns:
        filtered_saved_reviews = filtered_saved_reviews[filtered_saved_reviews["ProductId"].astype(str) == selected_product]
    if selected_user != "Todos" and "User" in filtered_saved_reviews.columns:
        filtered_saved_reviews = filtered_saved_reviews[filtered_saved_reviews["User"].astype(str) == selected_user]
    if selected_status != "Todos" and "Estado" in filtered_saved_reviews.columns:
        filtered_saved_reviews = filtered_saved_reviews[filtered_saved_reviews["Estado"] == selected_status]

filtered_history = product_history_df.copy()
if selected_user != "Todos" and "User" in filtered_history.columns:
    filtered_history = filtered_history[filtered_history["User"].astype(str) == selected_user]
if selected_status != "Todos" and "Estado" in filtered_history.columns:
    filtered_history = filtered_history[filtered_history["Estado"] == selected_status]

top_score = float(ranking_df["Helpfulness"].max()) if not ranking_df.empty else 0.0
avg_score = float(ranking_df["Helpfulness"].mean()) if not ranking_df.empty else 0.0
review_count = len(ranking_df)
top_user = str(ranking_df.iloc[0]["User"]) if not ranking_df.empty else "Sin datos"

metric_cols = st.columns(4, gap="medium")
with metric_cols[0]:
    render_metric_card("Reseñas del producto", format_compact_number(review_count), "Base competitiva local")
with metric_cols[1]:
    render_metric_card("Top utilidad", format_percentage(top_score), "Mejor score observado")
with metric_cols[2]:
    render_metric_card("Promedio local", format_percentage(avg_score), "Nivel medio del producto")
with metric_cols[3]:
    render_metric_card("Líder actual", top_user, "Usuario mejor posicionado")

left_col, right_col = st.columns(2, gap="large")
with left_col:
    st.subheader("Top 5 histórico del producto")
    st.dataframe(ranking_df.head(5), use_container_width=True)
with right_col:
    st.subheader("Tu reseña en contexto")
    if latest_review_id and not review_window_df.empty:
        for _, row in review_window_df.iterrows():
            meta_line = f"Puesto local {int(row['Puesto Local'])}"
            badge = "Tu reseña" if row["EsActual"] else row["Estado"]
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
        st.dataframe(ranking_df.head(10), use_container_width=True)

summary_cols = st.columns(3, gap="medium")
with summary_cols[0]:
    render_metric_card(
        "Tu posición local",
        f"{position_summary['local_rank']} / {position_summary['product_count']}" if position_summary["local_rank"] else "Sin reseña evaluada",
        "Lugar de la última reseña auditada en este producto",
    )
with summary_cols[1]:
    render_metric_card(
        "Tu posición global",
        f"{position_summary['global_rank']} / {position_summary['global_count']}" if position_summary["global_rank"] else "Sin reseña evaluada",
        "Lugar de la última reseña en toda la base",
    )
with summary_cols[2]:
    render_metric_card(
        "Historial por fecha",
        format_compact_number(len(filtered_history)),
        "Cantidad de reseñas visibles del producto",
    )

st.markdown("---")
st.subheader("Historial reciente del producto por fecha")
history_to_show = filtered_history.copy()
if selected_source == "Solo reseñas guardadas":
    history_to_show = pd.DataFrame()

if not history_to_show.empty:
    history_preview = history_to_show.head(10).copy()
    history_preview["CreatedAt"] = history_preview["CreatedAt"].dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(
        history_preview[["CreatedAt", "User", "Stars", "Helpfulness", "Estado", "Text"]],
        use_container_width=True,
    )
else:
    st.info("No hay reseñas históricas que coincidan con los filtros actuales.")

st.markdown("---")
st.subheader("Reseñas guardadas por la app")
if not filtered_saved_reviews.empty:
    saved_preview = filtered_saved_reviews.copy()
    if "CreatedAt" in saved_preview.columns:
        saved_preview["CreatedAt"] = pd.to_datetime(saved_preview["CreatedAt"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(saved_preview, use_container_width=True)
    csv_bytes = filtered_saved_reviews.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Descargar reseñas filtradas (CSV)",
        data=csv_bytes,
        file_name="reseñas_filtradas.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("No hay reseñas guardadas en el archivo operativo para los filtros seleccionados.")

st.markdown("---")
st.subheader("Top global por utilidad")
st.dataframe(global_ranking_df.head(20), use_container_width=True)

st.markdown("---")
st.subheader("Base global enriquecida")
st.dataframe(global_df.tail(100), use_container_width=True)