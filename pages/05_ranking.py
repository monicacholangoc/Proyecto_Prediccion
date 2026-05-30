"""Ranking y benchmark."""
import pandas as pd
import streamlit as st
from shared_sidebar import render_sidebar
from components.cards import render_metric_card, render_review_card
from services.catalog_service import get_product_detail, get_product_options
from services.preprocessing_service import (get_audited_reviews_operational_table, get_global_ranking,
    get_local_product_ranking, get_position_summary, get_product_reviews_by_date, get_review_context_window)
from utils.formatters import format_compact_number, format_percentage

with open("styles/styles.css", "r", encoding="utf-8") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
render_sidebar()

st.title("Ranking y Benchmark")
st.caption("Comparación de reseñas por producto. Analiza primero en Auditoría para ver tu posición.")

product_options  = get_product_options()
saved_reviews_df = get_audited_reviews_operational_table()
if not product_options:
    st.warning("No hay productos disponibles."); st.stop()

st.markdown('<div class="section-label">Filtros</div>', unsafe_allow_html=True)
f1, f2 = st.columns(2, gap="medium")
with f1: selected_product = st.selectbox("Producto", options=product_options)
with f2: selected_status = st.selectbox("Estado", options=["Todos","APROBADA (Publicada)","RECHAZADA (Baja Calidad)","RECHAZADA (Punto Ciego)"])

detail = get_product_detail(selected_product)
st.info(f"**{detail['ProductName']}** · `{detail['ProductId']}` · Categoría: {detail['Categoria_Real']}")

ranking_df         = get_local_product_ranking(selected_product)
global_ranking_df  = get_global_ranking()
product_history_df = get_product_reviews_by_date(selected_product, ascending=False)
latest_review_id   = st.session_state.get("latest_review_id")
position_summary   = get_position_summary(selected_product, latest_review_id)
review_window_df   = get_review_context_window(selected_product, latest_review_id, window_size=2)

if selected_status != "Todos":
    if "Estado" in ranking_df.columns:         ranking_df         = ranking_df[ranking_df["Estado"] == selected_status]
    if "Estado" in product_history_df.columns: product_history_df = product_history_df[product_history_df["Estado"] == selected_status]

top_score    = float(ranking_df["Helpfulness"].max())  if not ranking_df.empty else 0.0
avg_score    = float(ranking_df["Helpfulness"].mean()) if not ranking_df.empty else 0.0
review_count = len(ranking_df)
top_user     = str(ranking_df.iloc[0]["User"]) if not ranking_df.empty else "Sin datos"

st.markdown('<div class="section-label">Indicadores del producto</div>', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="stat-row">
        <div class="stat-pill"><div class="stat-pill-icon stat-pill-icon-blue"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/></svg></div><div><div class="stat-pill-value">{format_compact_number(review_count)}</div><div class="stat-pill-label">Reseñas</div></div></div>
        <div class="stat-pill"><div class="stat-pill-icon stat-pill-icon-green"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#15803d" stroke-width="2" stroke-linecap="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg></div><div><div class="stat-pill-value">{format_percentage(top_score)}</div><div class="stat-pill-label">Utilidad máxima</div></div></div>
        <div class="stat-pill"><div class="stat-pill-icon stat-pill-icon-teal"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2" stroke-linecap="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div><div><div class="stat-pill-value">{format_percentage(avg_score)}</div><div class="stat-pill-label">Utilidad media</div></div></div>
        <div class="stat-pill"><div class="stat-pill-icon stat-pill-icon-amber"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b45309" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div><div><div class="stat-pill-value" style="font-size:0.9rem">{top_user[:18]}</div><div class="stat-pill-label">Líder actual</div></div></div>
    </div>
    """, unsafe_allow_html=True,
)

st.markdown('<div class="section-label">Top 5 del producto</div>', unsafe_allow_html=True)
pos_labels = ["1er lugar","2do lugar","3er lugar","4to lugar","5to lugar"]
top5 = ranking_df.head(5) if not ranking_df.empty else pd.DataFrame()
if not top5.empty:
    for i, (_, row) in enumerate(top5.iterrows()):
        pos = pos_labels[i] if i < len(pos_labels) else f"{i+1}."
        user = str(row.get("User","—")); score = float(row.get("Helpfulness",0))
        stars = int(row.get("Stars",0)); estado = str(row.get("Estado","—"))
        filled = "&#9733;"*stars; empty = "&#9734;"*max(0,5-stars)
        c1,c2,c3,c4 = st.columns([2,1,1,1], gap="medium")
        with c1:
            st.markdown(f"""<div class="metric-card" style="{'border:2px solid var(--primary);' if i==0 else ''}">
                <div class="metric-label"><span class="metric-badge {'metric-badge-good' if i==0 else 'metric-badge-info'}">{pos}</span></div>
                <div class="metric-value" style="font-size:1rem;margin-top:0.3rem">{user}</div>
            </div>""", unsafe_allow_html=True)
        with c2: render_metric_card("Utilidad", format_percentage(score), "Score de helpfulness")
        with c3:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Estrellas</div><div class="metric-value" style="font-size:1.1rem;color:#f59e0b">{filled}{empty}</div></div>""", unsafe_allow_html=True)
        with c4:
            bc = "metric-badge-good" if "APROBADA" in estado else "metric-badge-warn"
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Estado</div><div class="metric-caption" style="margin-top:0.3rem">{estado}</div><span class="metric-badge {bc}">{'Publicada' if 'APROBADA' in estado else 'Rechazada'}</span></div>""", unsafe_allow_html=True)
else:
    st.info("No hay reseñas para los filtros seleccionados.")

st.markdown('<div class="section-label">Tu reseña en contexto</div>', unsafe_allow_html=True)
p1,p2,p3 = st.columns(3, gap="medium")
with p1: render_metric_card("Posición local", f"{position_summary['local_rank']} / {position_summary['product_count']}" if position_summary["local_rank"] else "Sin reseña evaluada", "Lugar dentro del producto")
with p2: render_metric_card("Posición global", f"{position_summary['global_rank']} / {position_summary['global_count']}" if position_summary["global_rank"] else "Sin reseña evaluada", "Lugar en toda la base")
with p3: render_metric_card("Total del producto", format_compact_number(position_summary["product_count"]), "Volumen histórico")

if latest_review_id and not review_window_df.empty:
    for _, row in review_window_df.iterrows():
        render_review_card(user_name=str(row["User"]), stars=int(row["Stars"]), review_text=str(row["Text"]),
            meta_line=f"Puesto local {int(row['Puesto Local'])}", badge="Tu reseña" if row["EsActual"] else row["Estado"],
            helpfulness=format_percentage(float(row["Helpfulness"])), highlighted=bool(row["EsActual"]))
else:
    st.info("Analiza una reseña en Auditoría para ver tu posición aquí.")

st.markdown("---")
st.markdown('<div class="section-label">Historial reciente del producto</div>', unsafe_allow_html=True)
if not product_history_df.empty:
    preview = product_history_df.head(10).copy()
    preview["CreatedAt"] = preview["CreatedAt"].dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(preview[["CreatedAt","User","Stars","Helpfulness","Estado","Text"]], use_container_width=True, hide_index=True)
else:
    st.info("No hay historial disponible.")

st.markdown('<div class="section-label">Reseñas guardadas</div>', unsafe_allow_html=True)
filtered_saved = saved_reviews_df.copy()
if not filtered_saved.empty:
    if "ProductId" in filtered_saved.columns:
        filtered_saved = filtered_saved[filtered_saved["ProductId"].astype(str) == selected_product]
    if selected_status != "Todos" and "Estado" in filtered_saved.columns:
        filtered_saved = filtered_saved[filtered_saved["Estado"] == selected_status]
if not filtered_saved.empty:
    if "CreatedAt" in filtered_saved.columns:
        filtered_saved["CreatedAt"] = pd.to_datetime(filtered_saved["CreatedAt"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(filtered_saved, use_container_width=True, hide_index=True)
    st.download_button("Descargar CSV", data=filtered_saved.to_csv(index=False).encode("utf-8-sig"),
        file_name="resenas_filtradas.csv", mime="text/csv", use_container_width=True)
else:
    st.info("No hay reseñas guardadas para los filtros seleccionados.")

st.markdown('<div class="section-label">Top 20 global por utilidad</div>', unsafe_allow_html=True)
st.dataframe(global_ranking_df.head(20), use_container_width=True, hide_index=True)