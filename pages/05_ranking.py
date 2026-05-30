"""Ranking y benchmark — indicadores en tarjetas, sin texto de relleno."""

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


def load_css() -> None:
    with open("styles/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def _render_logo() -> str:
    return """
    <svg class="sidebar-logo-svg" width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="38" height="38" rx="10" fill="url(#lg1k)"/>
      <path d="M10 26 L19 12 L28 26 Z" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.5)" stroke-width="1.2"/>
      <path d="M14 26 L19 17 L24 26 Z" fill="rgba(255,255,255,0.9)"/>
      <circle cx="19" cy="11" r="2.5" fill="#7dd3fc"/>
      <defs>
        <linearGradient id="lg1k" x1="0" y1="0" x2="38" y2="38" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stop-color="#1e3a8a"/>
          <stop offset="100%" stop-color="#0f4c5c"/>
        </linearGradient>
      </defs>
    </svg>
    """


load_css()

with st.sidebar:
    st.markdown(
        f"""
        <div class="sidebar-logo-wrap">
            {_render_logo()}
            <div>
                <div class="sidebar-logo-text-main">Seminario<br>Predictivo</div>
                <div class="sidebar-logo-text-sub">Caso 06 · Amazon Reviews</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="sidebar-panel">
            <div class="sidebar-panel-title">Navegación</div>
            <div class="sidebar-panel-item">1. Resumen Ejecutivo</div>
            <div class="sidebar-panel-item">2. Exploración de Datos</div>
            <div class="sidebar-panel-item">3. Modelos y Evaluación</div>
            <div class="sidebar-panel-item">4. Auditoría en Tiempo Real</div>
            <div class="sidebar-panel-item">5. Ranking y Benchmark</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.title("Ranking y Benchmark")
st.caption("Comparación de reseñas por producto. Analiza primero en Auditoría para ver tu posición.")

product_options  = get_product_options()
saved_reviews_df = get_audited_reviews_operational_table()

if not product_options:
    st.warning("No hay productos disponibles en el catálogo.")
    st.stop()

# ── Filtros ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Filtros</div>', unsafe_allow_html=True)
f1, f2 = st.columns(2, gap="medium")
with f1:
    selected_product = st.selectbox("Producto", options=product_options)
with f2:
    selected_status = st.selectbox(
        "Estado",
        options=["Todos", "APROBADA (Publicada)", "RECHAZADA (Baja Calidad)", "RECHAZADA (Punto Ciego)"],
    )

detail = get_product_detail(selected_product)
st.info(f"**{detail['ProductName']}** · `{detail['ProductId']}` · Categoría: {detail['Categoria_Real']}")

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

st.markdown('<div class="section-label">Indicadores del producto</div>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4, gap="medium")
with m1:
    render_metric_card("Reseñas", format_compact_number(review_count), "Base competitiva local")
with m2:
    render_metric_card("Utilidad máxima", format_percentage(top_score), "Mejor score observado")
with m3:
    render_metric_card("Utilidad media", format_percentage(avg_score), "Promedio local")
with m4:
    render_metric_card("Líder actual", top_user[:22], "Usuario mejor posicionado")

# ── Top 5 ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Top 5 del producto</div>', unsafe_allow_html=True)
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
        filled    = "&#9733;" * stars
        empty     = "&#9734;" * max(0, 5 - stars)

        c1, c2, c3, c4 = st.columns([2, 1, 1, 1], gap="medium")
        with c1:
            st.markdown(
                f"""
                <div class="metric-card" style="{'border:2px solid var(--primary);' if is_top else ''}">
                    <div class="metric-label">
                        <span class="metric-badge {'metric-badge-good' if is_top else 'metric-badge-info'}">{pos_label}</span>
                    </div>
                    <div class="metric-value" style="font-size:1rem;margin-top:0.3rem">{user}</div>
                </div>
                """, unsafe_allow_html=True,
            )
        with c2:
            render_metric_card("Utilidad", format_percentage(score), "Score de helpfulness")
        with c3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Estrellas</div>
                    <div class="metric-value" style="font-size:1.1rem;color:#f59e0b">{filled}{empty}</div>
                </div>
                """, unsafe_allow_html=True,
            )
        with c4:
            badge_class = "metric-badge-good" if "APROBADA" in estado else "metric-badge-warn"
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Estado</div>
                    <div class="metric-caption" style="margin-top:0.3rem">{estado}</div>
                    <span class="metric-badge {badge_class}">{'Publicada' if 'APROBADA' in estado else 'Rechazada'}</span>
                </div>
                """, unsafe_allow_html=True,
            )
else:
    st.info("No hay reseñas disponibles para los filtros seleccionados.")

# ── Tu posición ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Tu reseña en contexto</div>', unsafe_allow_html=True)
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
    render_metric_card("Total del producto", format_compact_number(position_summary["product_count"]), "Volumen histórico")

if latest_review_id and not review_window_df.empty:
    for _, row in review_window_df.iterrows():
        render_review_card(
            user_name=str(row["User"]), stars=int(row["Stars"]),
            review_text=str(row["Text"]),
            meta_line=f"Puesto local {int(row['Puesto Local'])}",
            badge="Tu reseña" if row["EsActual"] else row["Estado"],
            helpfulness=format_percentage(float(row["Helpfulness"])),
            highlighted=bool(row["EsActual"]),
        )
else:
    st.info("Analiza una reseña en Auditoría para ver tu posición aquí.")

# ── Historial ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-label">Historial reciente del producto</div>', unsafe_allow_html=True)
if not product_history_df.empty:
    preview = product_history_df.head(10).copy()
    preview["CreatedAt"] = preview["CreatedAt"].dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(preview[["CreatedAt", "User", "Stars", "Helpfulness", "Estado", "Text"]], use_container_width=True, hide_index=True)
else:
    st.info("No hay historial disponible para los filtros actuales.")

# ── Reseñas guardadas ──────────────────────────────────────────────────────────
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
    csv_bytes = filtered_saved.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Descargar CSV", data=csv_bytes, file_name="resenas_filtradas.csv", mime="text/csv", use_container_width=True)
else:
    st.info("No hay reseñas guardadas para los filtros seleccionados.")

# ── Top 20 global ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Top 20 global por utilidad</div>', unsafe_allow_html=True)
st.dataframe(global_ranking_df.head(20), use_container_width=True, hide_index=True)