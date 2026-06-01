"""Ranking y Benchmark — Tab 1: Global · Tab 2: Por Producto."""

try:
    import streamlit as _st
    if not _st.session_state.get("app_initialized"):
        _st.switch_page("main.py")
except Exception:
    pass

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shared_sidebar import render_sidebar
from components.cards import render_metric_card, render_review_card
from services.catalog_service import get_product_detail, get_product_options, get_product_catalog
from services.data_loader import load_processed_reviews, load_reviews_with_category
from services.feature_service import add_basic_text_features
from services.preprocessing_service import (
    get_corporate_audit_db,
    get_global_ranking,
    get_local_product_ranking,
    get_position_summary,
    get_review_context_window,
)
from services.supabase_service import load_reviews_from_supabase, clear_supabase_cache
from config.constants import TOPIC_NAMES
from utils.formatters import format_compact_number, format_percentage

# ── CSS ───────────────────────────────────────────────────────────────────────
with open("styles/styles.css", "r", encoding="utf-8") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
/* ── KPI grid ─────────────────────────────────────────────── */
.gkpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:0.55rem; margin-bottom:0.8rem; }
.gkpi-card {
    background:#fff; border:1px solid #e2e8f0; border-radius:14px;
    padding:0.85rem 1rem; text-align:center; position:relative; overflow:hidden;
}
.gkpi-card::before { content:""; position:absolute; top:0; left:0; right:0; height:3px; }
.gkpi-accent::before  { background:#1746a2; }
.gkpi-green::before   { background:#22c55e; }
.gkpi-red::before     { background:#f87171; }
.gkpi-teal::before    { background:#0f9f74; }
.gkpi-val { font-size:1.35rem; font-weight:800; color:#0f172a; line-height:1; margin-bottom:0.2rem; }
.gkpi-lbl { font-size:0.65rem; color:#64748b; text-transform:uppercase; letter-spacing:.06em; }

/* ── Podium ──────────────────────────────────────────────── */
.podium-card {
    flex:1; min-width:130px; border-radius:14px;
    padding:0.9rem 0.85rem 0.75rem; background:#fff;
    border:1px solid #e2e8f0; text-align:center;
}
.podium-1 { border-top:4px solid #f59e0b; }
.podium-2 { border-top:4px solid #94a3b8; }
.podium-3 { border-top:4px solid #b45309; }
.podium-pos   { font-size:0.58rem; font-weight:800; text-transform:uppercase; letter-spacing:.07em; color:#94a3b8; margin-bottom:0.2rem; }
.podium-medal { font-size:1.4rem; margin-bottom:0.1rem; }
.podium-user  { font-size:0.8rem; font-weight:700; color:#0f172a; margin-bottom:0.18rem; line-height:1.25; }
.podium-score { font-size:1.2rem; font-weight:900; color:#1746a2; }
.podium-sub   { font-size:0.63rem; color:#94a3b8; margin-top:0.12rem; }
.gauge-bar-bg { background:#f1f5f9; border-radius:999px; height:6px; overflow:hidden; margin:0.3rem 0 0.25rem; }
.gauge-bar-fill { height:100%; border-radius:999px; }
.status-pill { display:inline-block; font-size:0.62rem; font-weight:700; padding:0.14rem 0.5rem; border-radius:999px; }
.sp-green { background:#dcfce7; color:#15803d; }
.sp-amber { background:#fef3c7; color:#b45309; }
.sp-red   { background:#fee2e2; color:#991b1b; }

/* ── Category rows ───────────────────────────────────────── */
.cat-row { display:flex; align-items:center; gap:0.5rem; padding:0.4rem 0; border-bottom:1px solid #f1f5f9; }
.cat-row:last-child { border-bottom:none; }
.cat-rank { width:22px; font-size:0.68rem; font-weight:800; color:#94a3b8; flex-shrink:0; }
.cat-name { flex:1; font-size:0.79rem; font-weight:600; color:#0f172a; }
.cat-bar-wrap { width:70px; }
.cat-score { font-size:0.79rem; font-weight:700; color:#1746a2; width:42px; text-align:right; flex-shrink:0; }

/* ── Comparativa multi-producto ──────────────────────────── */
.prod-compare-card {
    background:#fff; border:1px solid #e2e8f0; border-radius:14px;
    padding:0.9rem 1rem; margin-bottom:0.55rem;
    display:flex; align-items:center; gap:0.8rem; position:relative; overflow:hidden;
}
.prod-compare-card::before { content:""; position:absolute; left:0; top:0; bottom:0; width:5px; }
.pc-rank  { font-size:1rem; font-weight:900; color:#94a3b8; width:28px; flex-shrink:0; text-align:center; }
.pc-name  { flex:1; min-width:0; }
.pc-title { font-size:0.82rem; font-weight:700; color:#0f172a; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.pc-cat   { font-size:0.65rem; color:#64748b; margin-top:1px; }
.pc-stats { display:flex; flex-direction:column; align-items:flex-end; flex-shrink:0; }
.pc-score { font-size:1.1rem; font-weight:900; }
.pc-sub   { font-size:0.62rem; color:#94a3b8; }
.pc-bar-wrap { width:80px; flex-shrink:0; }

/* ── Tabla de reseñas ────────────────────────────────────── */
.review-row {
    display:flex; align-items:center; gap:0.6rem;
    padding:0.55rem 0.7rem; border-radius:10px;
    background:#fff; border:1px solid #e2e8f0; margin-bottom:0.4rem;
}
.review-row.highlighted { border-color:#1746a2; background:#f0f4ff; }
.rr-rank { width:28px; font-size:0.8rem; font-weight:800; color:#94a3b8; flex-shrink:0; text-align:center; }
.rr-user { font-size:0.8rem; font-weight:700; color:#0f172a; min-width:0; }
.rr-stars { font-size:0.78rem; color:#f59e0b; letter-spacing:1px; flex-shrink:0; }
.rr-text  { font-size:0.75rem; color:#64748b; flex:1; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:0; }
.rr-score { font-size:0.88rem; font-weight:800; flex-shrink:0; }
.rr-pill  { flex-shrink:0; }

@media(max-width:768px) { .gkpi-grid { grid-template-columns:repeat(2,1fr); } }
</style>
""", unsafe_allow_html=True)

render_sidebar()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#16213b 0%,#1746a2 60%,#0f4c5c 100%);
    border-radius:16px;padding:1.4rem 2rem;margin-bottom:1.2rem;color:#fff">
    <div style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                color:rgba(255,255,255,0.55);text-transform:uppercase;margin-bottom:0.35rem">
        Seminario Predictivo 2026 · Caso 06
    </div>
    <div style="font-size:clamp(1.4rem,3vw,1.9rem);font-weight:800;
                letter-spacing:-0.02em;line-height:1.2;margin-bottom:0.3rem">
        Ranking y Benchmark
    </div>
    <div style="font-size:0.82rem;color:rgba(255,255,255,0.65)">
        Ranking global de todas las reseñas · Comparativa por producto · Posición en tiempo real
    </div>
</div>
""", unsafe_allow_html=True)

# ── Cargar datos ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_full_dataset() -> pd.DataFrame:
    df = add_basic_text_features(load_reviews_with_category())
    if df.empty:
        df = add_basic_text_features(load_processed_reviews())
    if df.empty:
        return df
    if "categoria_alimento" in df.columns:
        df["Categoria_Real"] = df["categoria_alimento"]
    elif "product_topic" in df.columns and "Categoria_Real" not in df.columns:
        df["Categoria_Real"] = df["product_topic"].map(TOPIC_NAMES).fillna("Alimentos generales")
    elif "Categoria_Real" not in df.columns:
        df["Categoria_Real"] = "Alimentos generales"
    if "Time" in df.columns:
        df["CreatedAt"] = pd.to_datetime(df["Time"], unit="s", errors="coerce")
    elif "CreatedAt" in df.columns:
        df["CreatedAt"] = pd.to_datetime(df["CreatedAt"], errors="coerce")
    else:
        df["CreatedAt"] = pd.NaT
    df["Año"] = df["CreatedAt"].dt.year.where(df["CreatedAt"].notna(), other=0).astype(int)
    if "y_util" in df.columns:
        df["Helpfulness"] = df["y_util"].astype(float)
        df["Estado"] = df["y_util"].apply(lambda x: "APROBADA (Publicada)" if x == 1 else "RECHAZADA (Baja Calidad)")
    elif "Helpfulness" not in df.columns:
        if "HelpfulnessNumerator" in df.columns and "HelpfulnessDenominator" in df.columns:
            denom = df["HelpfulnessDenominator"].replace(0, pd.NA)
            df["Helpfulness"] = (df["HelpfulnessNumerator"] / denom).fillna(0)
        else:
            df["Helpfulness"] = 0.5
        df["Estado"] = df["Helpfulness"].apply(lambda x: "APROBADA (Publicada)" if x >= 0.70 else "RECHAZADA (Baja Calidad)")
    if "Stars" not in df.columns and "Score" in df.columns:
        df["Stars"] = df["Score"]
    return df

full_df_base   = _load_full_dataset()
catalog        = get_product_catalog()
op_db          = get_corporate_audit_db()
global_ranking = get_global_ranking()
product_options = get_product_options()

# Fusionar Supabase
sb_df = load_reviews_from_supabase()
if not sb_df.empty:
    cat_map = catalog.set_index("ProductId")["Categoria_Real"].to_dict() if not catalog.empty and "Categoria_Real" in catalog.columns else {}
    sb_norm = pd.DataFrame({
        "ProductId":    sb_df["product_id"].astype(str),
        "Score":        pd.to_numeric(sb_df.get("stars", 5), errors="coerce").fillna(5).astype(int),
        "Stars":        pd.to_numeric(sb_df.get("stars", 5), errors="coerce").fillna(5).astype(int),
        "Helpfulness":  pd.to_numeric(sb_df.get("helpfulness", 0), errors="coerce").fillna(0),
        "Estado":       sb_df.get("status", "RECHAZADA (Baja Calidad)"),
        "User":         sb_df.get("usuario", "Nuevo"),
        "Text":         sb_df.get("texto", ""),
        "CreatedAt":    pd.to_datetime(sb_df.get("created_at"), errors="coerce"),
        "Categoria_Real": sb_df["product_id"].astype(str).map(cat_map).fillna("Alimentos generales"),
        "_es_nueva":    True,
    })
    sb_norm["Año"] = sb_norm["CreatedAt"].dt.year.fillna(2026).astype(int)
    full_df_base["_es_nueva"] = False
    full_df = pd.concat([sb_norm, full_df_base], ignore_index=True)
else:
    full_df = full_df_base

# Opciones de categoría y año
cat_options_full = ["Todas las categorías"]
if not full_df.empty and "Categoria_Real" in full_df.columns:
    cat_options_full += sorted(full_df["Categoria_Real"].dropna().unique().tolist())
años_disponibles = []
if not full_df.empty and "Año" in full_df.columns:
    años_disponibles = sorted([y for y in full_df["Año"].unique() if y > 2000], reverse=True)

# Barra de estado + botón actualizar
ref1, ref2 = st.columns([4, 1])
with ref1:
    nuevas_count = len(sb_df) if not sb_df.empty else 0
    st.markdown(
        f'<div style="padding:0.35rem 0;font-size:0.82rem;color:#64748b">'
        f'Base total: <strong style="color:#0f172a">{format_compact_number(len(full_df))}</strong> reseñas '
        f'({format_compact_number(len(full_df_base))} históricas + '
        f'<span style="color:#15803d;font-weight:700">{nuevas_count} nuevas</span>)</div>',
        unsafe_allow_html=True,
    )
with ref2:
    if st.button("🔄 Actualizar", use_container_width=True):
        clear_supabase_cache()
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TABS PRINCIPALES
# ══════════════════════════════════════════════════════════════════════════════
tab_global, tab_producto = st.tabs([
    "🌐  Ranking Global",
    "📦  Ranking por Producto",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
with tab_global:

    # Filtros globales
    st.markdown('<div class="section-label">Filtros</div>', unsafe_allow_html=True)
    gc1, gc2, gc3, gc4 = st.columns([2, 1.4, 1.2, 1], gap="medium")
    with gc1:
        g_cat    = st.selectbox("Categoría", options=cat_options_full, key="g_cat")
    with gc2:
        g_status = st.selectbox("Estado", ["Todos", "APROBADA (Publicada)", "RECHAZADA (Baja Calidad)"], key="g_status")
    with gc3:
        g_year   = st.selectbox("Año", ["Todos los años"] + [str(y) for y in años_disponibles], key="g_year")
    with gc4:
        g_stars  = st.selectbox("Estrellas mín.", ["Todas","1","2","3","4","5"], key="g_stars")

    def _filter_global(df):
        out = df.copy()
        if g_cat    != "Todas las categorías"    and "Categoria_Real" in out.columns: out = out[out["Categoria_Real"] == g_cat]
        if g_status != "Todos"                   and "Estado"         in out.columns: out = out[out["Estado"] == g_status]
        if g_year   != "Todos los años"          and "Año"            in out.columns: out = out[out["Año"] == int(g_year)]
        if g_stars  != "Todas"                   and "Stars"          in out.columns: out = out[out["Stars"] >= int(g_stars)]
        return out

    fdf = _filter_global(full_df)
    total_r  = len(fdf)
    approved = int((fdf["Estado"] == "APROBADA (Publicada)").sum()) if "Estado" in fdf.columns and total_r > 0 else 0
    rejected = total_r - approved
    avg_help = float(fdf["Helpfulness"].mean()) if "Helpfulness" in fdf.columns and total_r > 0 else 0.0
    appr_rt  = approved / total_r if total_r > 0 else 0.0

    # KPIs globales
    st.markdown('<div class="section-label">Indicadores globales</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="gkpi-grid">
        <div class="gkpi-card gkpi-accent">
            <div class="gkpi-val">{format_compact_number(total_r)}</div>
            <div class="gkpi-lbl">Reseñas totales</div>
        </div>
        <div class="gkpi-card gkpi-green">
            <div class="gkpi-val" style="color:#15803d">{format_compact_number(approved)}</div>
            <div class="gkpi-lbl">Aprobadas · {format_percentage(appr_rt)}</div>
        </div>
        <div class="gkpi-card gkpi-red">
            <div class="gkpi-val" style="color:#dc2626">{format_compact_number(rejected)}</div>
            <div class="gkpi-lbl">Rechazadas</div>
        </div>
        <div class="gkpi-card gkpi-teal">
            <div class="gkpi-val">{format_percentage(avg_help)}</div>
            <div class="gkpi-lbl">Utilidad media</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Gráficas: donut estado + evolución anual
    vc1, vc2 = st.columns(2, gap="medium")
    with vc1:
        st.markdown('<div class="section-label">Distribución por estado</div>', unsafe_allow_html=True)
        if "Estado" in fdf.columns and total_r > 0:
            ec = fdf["Estado"].value_counts().reset_index()
            ec.columns = ["Estado", "Cantidad"]
            color_map = {
                "APROBADA (Publicada)":     "#22c55e",
                "RECHAZADA (Baja Calidad)": "#f59e0b",
                "RECHAZADA (Punto Ciego)":  "#f87171",
            }
            fig_e = px.pie(ec, values="Cantidad", names="Estado",
                           color="Estado", color_discrete_map=color_map,
                           hole=0.58, template="plotly_white")
            fig_e.update_traces(textposition="outside", textinfo="percent+label",
                                textfont_size=10, pull=[0.03]*len(ec))
            fig_e.update_layout(height=240, margin=dict(l=10,r=10,t=20,b=10), showlegend=False)
            st.plotly_chart(fig_e, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sin datos.")

    with vc2:
        st.markdown('<div class="section-label">Evolución por año</div>', unsafe_allow_html=True)
        if "Año" in fdf.columns and total_r > 0:
            anual = (fdf[fdf["Año"] > 2000]
                     .groupby("Año")
                     .agg(Total=("Helpfulness","count"), Util_Media=("Helpfulness","mean"))
                     .reset_index().sort_values("Año"))
            if not anual.empty:
                fig_ev = go.Figure()
                fig_ev.add_trace(go.Bar(x=anual["Año"].astype(str), y=anual["Total"],
                                        name="Reseñas", marker_color="#dbe7ff", opacity=0.85, yaxis="y"))
                fig_ev.add_trace(go.Scatter(x=anual["Año"].astype(str), y=anual["Util_Media"],
                                            name="Utilidad media", line=dict(color="#1746a2", width=2.5),
                                            yaxis="y2", mode="lines+markers", marker_size=5))
                fig_ev.update_layout(
                    height=240, margin=dict(l=10,r=10,t=20,b=10),
                    yaxis=dict(title="Reseñas", showgrid=True, gridcolor="#f0f4f8"),
                    yaxis2=dict(title="Utilidad", overlaying="y", side="right",
                                tickformat=".0%", range=[0,1]),
                    xaxis=dict(tickfont_size=9),
                    legend=dict(orientation="h", y=1.12, font_size=9),
                    template="plotly_white", plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_ev, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sin datos temporales.")
        else:
            st.info("Sin información de fechas.")

    # Top 5 categorías
    st.markdown('<div class="section-label">Top 5 categorías por utilidad media</div>', unsafe_allow_html=True)
    cat_col = "Categoria_Real" if "Categoria_Real" in fdf.columns else None
    tcc1, tcc2 = st.columns([1, 1.4], gap="medium")
    if cat_col and total_r > 0:
        cat_stats = (fdf.groupby(cat_col)
                     .agg(n_resenas=(cat_col,"count"), util_media=("Helpfulness","mean"))
                     .reset_index().sort_values("util_media", ascending=False).head(5).reset_index(drop=True))
        bar_colors = ["#f59e0b","#94a3b8","#b45309","#64748b","#64748b"]
        with tcc1:
            cat_html = '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:0.7rem 0.9rem;">'
            for i, row in cat_stats.iterrows():
                bw = int(row["util_media"] * 100)
                bc = bar_colors[i] if i < len(bar_colors) else "#64748b"
                cat_html += (f'<div class="cat-row"><div class="cat-rank">#{i+1}</div>'
                             f'<div class="cat-name">{row[cat_col]}</div>'
                             f'<div class="cat-bar-wrap"><div class="gauge-bar-bg">'
                             f'<div class="gauge-bar-fill" style="width:{bw}%;background:{bc}"></div>'
                             f'</div></div><div class="cat-score">{row["util_media"]:.1%}</div></div>')
            cat_html += "</div>"
            st.markdown(cat_html, unsafe_allow_html=True)
        with tcc2:
            ordered = cat_stats.sort_values("util_media", ascending=True)
            fig_cat = px.bar(ordered, x="util_media", y=cat_col, orientation="h",
                             color="util_media", color_continuous_scale=["#fef3c7","#f59e0b","#15803d"],
                             labels={"util_media":"Utilidad media", cat_col:"Categoría"},
                             template="plotly_white",
                             text=ordered["n_resenas"].apply(lambda x: f"{format_compact_number(int(x))} res."))
            fig_cat.update_coloraxes(showscale=False)
            fig_cat.update_traces(textposition="inside", textfont_size=9)
            fig_cat.update_xaxes(tickformat=".0%", range=[0,1])
            fig_cat.update_layout(height=220, margin=dict(l=10,r=10,t=15,b=10))
            st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sin datos de categorías.")

    # Distribución estrellas + utilidad por estrella
    pd1, pd2 = st.columns(2, gap="medium")
    star_col = "Stars" if "Stars" in fdf.columns else ("Score" if "Score" in fdf.columns else None)
    with pd1:
        st.markdown('<div class="section-label">Distribución de estrellas</div>', unsafe_allow_html=True)
        if star_col and total_r > 0:
            sc = fdf[star_col].value_counts().sort_index().reset_index()
            sc.columns = ["Estrellas","Cantidad"]
            sc["Label"] = sc["Estrellas"].apply(lambda x: f"{int(x)} estrella{'s' if int(x)>1 else ''}")
            fig_s = px.bar(sc, x="Label", y="Cantidad", color="Estrellas",
                           color_continuous_scale=["#fee2e2","#fef3c7","#fef9c3","#dcfce7","#15803d"],
                           template="plotly_white", labels={"Label":"","Cantidad":"Reseñas"})
            fig_s.update_coloraxes(showscale=False)
            fig_s.update_layout(height=210, margin=dict(l=10,r=10,t=15,b=10))
            st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sin datos de estrellas.")
    with pd2:
        st.markdown('<div class="section-label">Utilidad media por estrella</div>', unsafe_allow_html=True)
        if star_col and "Helpfulness" in fdf.columns and total_r > 0:
            ubs = fdf.groupby(star_col)["Helpfulness"].mean().reset_index()
            ubs.columns = ["Estrellas","Utilidad_media"]
            ubs["Label"] = ubs["Estrellas"].apply(lambda x: f"{int(x)} estrellas")
            fig_us = px.line(ubs, x="Label", y="Utilidad_media", markers=True,
                             template="plotly_white",
                             labels={"Label":"","Utilidad_media":"Utilidad media"},
                             color_discrete_sequence=["#1746a2"])
            fig_us.update_yaxes(tickformat=".0%", range=[0,1])
            fig_us.update_traces(line_width=2.5, marker_size=7)
            fig_us.update_layout(height=210, margin=dict(l=10,r=10,t=15,b=10))
            st.plotly_chart(fig_us, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sin datos suficientes.")

    # Top 20 global — tabla completa
    st.markdown('<div class="section-label">Top 20 — ranking global por utilidad</div>', unsafe_allow_html=True)
    if not global_ranking.empty:
        top20 = global_ranking.head(20).copy()
        display_cols = [c for c in ["Puesto Global","ProductId","User","Stars","Helpfulness","Estado"] if c in top20.columns]
        if "Helpfulness" in top20.columns:
            top20["Helpfulness"] = top20["Helpfulness"].apply(lambda x: format_percentage(float(x)))
        st.dataframe(top20[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("Sin ranking global disponible.")

    # Reseñas en Supabase
    st.markdown("---")
    st.markdown('<div class="section-label">Reseñas auditadas en tiempo real (Supabase)</div>', unsafe_allow_html=True)
    df_supabase = load_reviews_from_supabase()
    if not df_supabase.empty:
        sb_total    = len(df_supabase)
        sb_approved = int((df_supabase["status"].str.contains("APROBADA", na=False)).sum())
        sb_avg_help = float(df_supabase["helpfulness"].mean()) if "helpfulness" in df_supabase.columns else 0.0

        sk1, sk2, sk3 = st.columns(3, gap="medium")
        with sk1: render_metric_card("Reseñas guardadas", format_compact_number(sb_total), "Total en Supabase")
        with sk2: render_metric_card("Aprobadas", str(sb_approved), "Estado APROBADA")
        with sk3: render_metric_card("Utilidad media", format_percentage(sb_avg_help), "Promedio")

        display_sb = df_supabase[[c for c in ["id","product_id","usuario","stars","helpfulness","status","review_len","created_at"] if c in df_supabase.columns]].copy()
        if "helpfulness" in display_sb.columns:
            display_sb["helpfulness"] = display_sb["helpfulness"].apply(lambda x: format_percentage(float(x)))
        if "created_at" in display_sb.columns:
            display_sb["created_at"] = pd.to_datetime(display_sb["created_at"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M")
        display_sb = display_sb.rename(columns={
            "id":"ID","product_id":"Producto","usuario":"Usuario",
            "stars":"Estrellas","helpfulness":"Utilidad",
            "status":"Estado","review_len":"Palabras","created_at":"Fecha",
        })
        st.dataframe(display_sb, use_container_width=True, hide_index=True)

        if "helpfulness" in df_supabase.columns and sb_total > 1:
            fig_sb = px.histogram(df_supabase, x="helpfulness", nbins=20,
                                  title="Distribución de utilidad — reseñas en Supabase",
                                  labels={"helpfulness":"Probabilidad de utilidad"},
                                  color_discrete_sequence=["#1746a2"], template="plotly_white")
            fig_sb.add_vline(x=0.70, line_dash="dash", line_color="#22c55e",
                             annotation_text="Umbral (70%)", annotation_position="top right")
            fig_sb.update_layout(height=240, margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig_sb, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Aún no hay reseñas guardadas en Supabase.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — POR PRODUCTO
# ─────────────────────────────────────────────────────────────────────────────
with tab_producto:

    # ── Sección A: comparativa entre productos seleccionados ──────────────────
    st.markdown('<div class="section-label">Comparativa entre productos</div>', unsafe_allow_html=True)
    st.caption("Selecciona entre 2 y 5 productos para comparar su rendimiento de utilidad.")

    productos_multi = st.multiselect(
        "Productos a comparar",
        options=product_options,
        default=product_options[:min(3, len(product_options))],
        max_selections=5,
        key="multi_prod",
    )

    if productos_multi:
        compare_rows = []
        for pid in productos_multi:
            detail    = get_product_detail(pid)
            rk_df     = get_local_product_ranking(pid)
            n_rev     = len(rk_df)
            avg_u     = float(rk_df["Helpfulness"].mean())  if not rk_df.empty and "Helpfulness"  in rk_df.columns else 0.0
            max_u     = float(rk_df["Helpfulness"].max())   if not rk_df.empty and "Helpfulness"  in rk_df.columns else 0.0
            appr_n    = int((rk_df["Estado"] == "APROBADA (Publicada)").sum()) if not rk_df.empty and "Estado" in rk_df.columns else 0
            compare_rows.append({
                "pid":     pid,
                "name":    detail.get("ProductName", pid),
                "cat":     detail.get("Categoria_Real", "—"),
                "n_rev":   n_rev,
                "avg_u":   avg_u,
                "max_u":   max_u,
                "appr":    appr_n,
            })

        compare_df = pd.DataFrame(compare_rows).sort_values("avg_u", ascending=False).reset_index(drop=True)

        # Cards de comparativa
        for i, row in compare_df.iterrows():
            bar_w   = int(row["avg_u"] * 100)
            bar_clr = "#22c55e" if row["avg_u"] >= 0.70 else ("#f59e0b" if row["avg_u"] >= 0.40 else "#f87171")
            score_clr = "#15803d" if row["avg_u"] >= 0.70 else ("#b45309" if row["avg_u"] >= 0.40 else "#dc2626")
            st.markdown(
                f'<div class="prod-compare-card" style="--bc:{bar_clr}">'
                f'<div class="pc-rank" style="color:{bar_clr}">#{i+1}</div>'
                f'<div class="pc-name">'
                f'<div class="pc-title">{row["name"]}</div>'
                f'<div class="pc-cat">{row["cat"]} · {row["n_rev"]} reseñas · {row["appr"]} aprobadas</div>'
                f'</div>'
                f'<div class="pc-bar-wrap"><div class="gauge-bar-bg">'
                f'<div class="gauge-bar-fill" style="width:{bar_w}%;background:{bar_clr}"></div>'
                f'</div></div>'
                f'<div class="pc-stats">'
                f'<div class="pc-score" style="color:{score_clr}">{row["avg_u"]:.1%}</div>'
                f'<div class="pc-sub">utilidad media</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Gráfica comparativa de barras
        if len(compare_df) >= 2:
            st.markdown('<div class="section-label">Gráfica comparativa</div>', unsafe_allow_html=True)
            fig_cmp = go.Figure()
            short_names = [n[:22] + "…" if len(n) > 22 else n for n in compare_df["name"]]
            fig_cmp.add_trace(go.Bar(
                name="Utilidad media",
                x=short_names, y=compare_df["avg_u"],
                marker_color="#1746a2", text=[f"{v:.1%}" for v in compare_df["avg_u"]],
                textposition="outside",
            ))
            fig_cmp.add_trace(go.Bar(
                name="Utilidad máxima",
                x=short_names, y=compare_df["max_u"],
                marker_color="#dbe7ff", text=[f"{v:.1%}" for v in compare_df["max_u"]],
                textposition="outside",
            ))
            fig_cmp.add_hline(y=0.70, line_dash="dash", line_color="#22c55e",
                              annotation_text="Umbral 70%", annotation_position="top right")
            fig_cmp.update_yaxes(tickformat=".0%", range=[0, 1.1])
            fig_cmp.update_layout(
                barmode="group", height=280, margin=dict(l=10,r=10,t=30,b=10),
                template="plotly_white", legend=dict(orientation="h", y=1.12, font_size=10),
            )
            st.plotly_chart(fig_cmp, use_container_width=True, config={"displayModeBar": False})

    else:
        st.info("Selecciona al menos un producto para ver la comparativa.")

    st.markdown("---")

    # ── Sección B: ranking detallado de un producto ───────────────────────────
    st.markdown('<div class="section-label">Ranking detallado de un producto</div>', unsafe_allow_html=True)

    col_prod, col_status = st.columns([2, 1], gap="medium")
    with col_prod:
        selected_product = st.selectbox("Producto", options=product_options, key="prod_detail")
    with col_status:
        p_status = st.selectbox("Estado", ["Todos", "APROBADA (Publicada)", "RECHAZADA (Baja Calidad)"], key="p_status")

    if selected_product:
        detail      = get_product_detail(selected_product)
        ranking_df  = get_local_product_ranking(selected_product)

        # Aplicar filtro de estado
        if p_status != "Todos" and not ranking_df.empty and "Estado" in ranking_df.columns:
            ranking_df = ranking_df[ranking_df["Estado"] == p_status]

        # Info del producto
        st.markdown(
            f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;'
            f'padding:0.65rem 1.1rem;margin-bottom:0.8rem;display:flex;gap:2rem;flex-wrap:wrap;align-items:center">'
            f'<div><div style="font-size:.6rem;font-weight:700;color:#94a3b8;text-transform:uppercase">Producto</div>'
            f'<div style="font-size:.9rem;font-weight:700;color:#0f172a">{detail["ProductName"]}</div></div>'
            f'<div><div style="font-size:.6rem;font-weight:700;color:#94a3b8;text-transform:uppercase">Categoría</div>'
            f'<div style="font-size:.88rem;font-weight:700;color:#1746a2">{detail["Categoria_Real"]}</div></div>'
            f'<div><div style="font-size:.6rem;font-weight:700;color:#94a3b8;text-transform:uppercase">ID</div>'
            f'<div style="font-size:.78rem;color:#64748b;font-family:monospace">{detail["ProductId"]}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if not ranking_df.empty:
            n_rev_prd = len(ranking_df)
            top_score = float(ranking_df["Helpfulness"].max())  if "Helpfulness" in ranking_df.columns else 0.0
            avg_score = float(ranking_df["Helpfulness"].mean()) if "Helpfulness" in ranking_df.columns else 0.0
            appr_prd  = int((ranking_df["Estado"] == "APROBADA (Publicada)").sum()) if "Estado" in ranking_df.columns else 0
            rej_prd   = n_rev_prd - appr_prd

            # KPIs del producto
            pc1, pc2, pc3, pc4, pc5 = st.columns(5, gap="small")
            with pc1: render_metric_card("Reseñas", format_compact_number(n_rev_prd), "Con filtro activo")
            with pc2: render_metric_card("Utilidad máx.", format_percentage(top_score), "Mejor reseña")
            with pc3: render_metric_card("Utilidad media", format_percentage(avg_score), "Promedio del producto")
            with pc4: render_metric_card("Aprobadas", str(appr_prd), "Estado APROBADA")
            with pc5: render_metric_card("Rechazadas", str(rej_prd), "Estado RECHAZADA")

            # Pódium Top 3
            top3 = ranking_df.head(3)
            medals = ["🥇", "🥈", "🥉"]
            podium_cls = ["podium-1", "podium-2", "podium-3"]
            podium_labels = ["1er lugar", "2do lugar", "3er lugar"]

            st.markdown('<div class="section-label">Pódium — Top 3 del producto</div>', unsafe_allow_html=True)
            cols_p = st.columns(min(len(top3), 3), gap="medium")
            for i, (_, row) in enumerate(top3.iterrows()):
                score   = float(row.get("Helpfulness", 0))
                user    = str(row.get("User","—"))[:24]
                stars_n = int(row.get("Stars", row.get("Score", 0)))
                estado  = str(row.get("Estado","—"))
                bar_w   = int(score * 100)
                bar_clr = "#22c55e" if score >= 0.7 else "#f59e0b"
                sp_cls  = "sp-green" if "APROBADA" in estado else "sp-amber"
                sp_lbl  = "Publicada" if "APROBADA" in estado else "Rechazada"
                stars_html = "".join(
                    ['<span style="color:#f59e0b;font-size:.75rem">★</span>' for _ in range(stars_n)] +
                    ['<span style="color:#d1d5db;font-size:.75rem">☆</span>' for _ in range(5-stars_n)]
                )
                with cols_p[i]:
                    st.markdown(f"""
                    <div class="podium-card {podium_cls[i]}">
                        <div class="podium-pos">{podium_labels[i]}</div>
                        <div class="podium-medal">{medals[i]}</div>
                        <div class="podium-user">{user}</div>
                        <div class="podium-score">{format_percentage(score)}</div>
                        <div class="podium-sub">{stars_html}</div>
                        <div class="gauge-bar-bg">
                            <div class="gauge-bar-fill" style="width:{bar_w}%;background:{bar_clr}"></div>
                        </div>
                        <div style="margin-top:0.3rem">
                            <span class="status-pill {sp_cls}">{sp_lbl}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Tabla completa de reseñas del producto
            st.markdown('<div class="section-label">Todas las reseñas del producto</div>', unsafe_allow_html=True)
            latest_review_id = st.session_state.get("latest_review_id")

            display_full = ranking_df.copy()
            display_full["Puesto"] = range(1, len(display_full) + 1)

            # Render como filas HTML para mejor visualización
            for _, row in display_full.iterrows():
                score     = float(row.get("Helpfulness", 0))
                user      = str(row.get("User","—"))[:30]
                stars_n   = int(row.get("Stars", row.get("Score", 0)))
                estado    = str(row.get("Estado","—"))
                text_pre  = str(row.get("Text",""))[:80] + ("…" if len(str(row.get("Text",""))) > 80 else "")
                puesto    = int(row.get("Puesto", 0))
                is_cur    = str(row.get("ReviewId","")) == str(latest_review_id) if latest_review_id else False
                score_clr = "#15803d" if score >= 0.7 else ("#b45309" if score >= 0.4 else "#dc2626")
                sp_cls    = "sp-green" if "APROBADA" in estado else "sp-amber"
                sp_lbl    = "✓ Publicada" if "APROBADA" in estado else "✗ Rechazada"
                stars_str = "★" * stars_n + "☆" * (5 - stars_n)
                hl_cls    = " highlighted" if is_cur else ""

                st.markdown(
                    f'<div class="review-row{hl_cls}">'
                    f'<div class="rr-rank">#{puesto}</div>'
                    f'<div style="display:flex;flex-direction:column;flex:1;min-width:0;gap:1px">'
                    f'<div style="display:flex;align-items:center;gap:0.5rem">'
                    f'<span class="rr-user">{user}</span>'
                    f'<span class="rr-stars">{stars_str}</span>'
                    f'{"<span style=\"font-size:.6rem;background:#1746a2;color:#fff;padding:1px 6px;border-radius:4px\">Tu reseña</span>" if is_cur else ""}'
                    f'</div>'
                    f'<div class="rr-text">{text_pre}</div>'
                    f'</div>'
                    f'<div class="rr-score" style="color:{score_clr}">{format_percentage(score)}</div>'
                    f'<div class="rr-pill"><span class="status-pill {sp_cls}">{sp_lbl}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        else:
            st.info("No hay reseñas disponibles para este producto con los filtros seleccionados.")

        # Tu reseña en contexto
        st.markdown('<div class="section-label">Tu reseña en contexto</div>', unsafe_allow_html=True)
        latest_review_id = st.session_state.get("latest_review_id")
        position_summary = get_position_summary(selected_product, latest_review_id)
        review_window_df = get_review_context_window(selected_product, latest_review_id, window_size=2)

        p1, p2, p3 = st.columns(3, gap="medium")
        with p1:
            render_metric_card("Posición local",
                f"{position_summary['local_rank']} / {position_summary['product_count']}" if position_summary["local_rank"] else "Sin reseña evaluada",
                "Lugar dentro del producto")
        with p2:
            render_metric_card("Posición global",
                f"{position_summary['global_rank']} / {position_summary['global_count']}" if position_summary["global_rank"] else "Sin reseña evaluada",
                "Lugar en toda la base")
        with p3:
            render_metric_card("Total del producto",
                format_compact_number(position_summary["product_count"]),
                "Volumen histórico")

        if latest_review_id and not review_window_df.empty:
            for _, row in review_window_df.iterrows():
                render_review_card(
                    user_name=str(row["User"]),
                    stars=int(row["Stars"]),
                    review_text=str(row["Text"]),
                    meta_line=f"Puesto local {int(row['Puesto Local'])}",
                    badge="Tu reseña" if row["EsActual"] else row["Estado"],
                    helpfulness=format_percentage(float(row["Helpfulness"])),
                    highlighted=bool(row["EsActual"]),
                )
        else:
            st.info("Analiza una reseña en Auditoría para ver tu posición aquí.")

st.session_state["selected_product_id"] = selected_product if "selected_product" in dir() else (product_options[0] if product_options else None)