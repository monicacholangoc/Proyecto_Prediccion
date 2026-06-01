"""Ranking y Benchmark — Tab 1: Ranking Global · Tab 2: Analisis por Producto."""

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
.gkpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:0.55rem; margin-bottom:0.8rem; }
.gkpi-card {
    background:#fff; border:1px solid #e2e8f0; border-radius:14px;
    padding:0.85rem 1rem; text-align:center; position:relative; overflow:hidden;
}
.gkpi-card::before { content:""; position:absolute; top:0; left:0; right:0; height:3px; }
.gkpi-accent::before { background:#1746a2; }
.gkpi-green::before  { background:#22c55e; }
.gkpi-red::before    { background:#f87171; }
.gkpi-teal::before   { background:#0f9f74; }
.gkpi-val { font-size:1.35rem; font-weight:800; color:#0f172a; line-height:1; margin-bottom:0.2rem; }
.gkpi-lbl { font-size:0.65rem; color:#64748b; text-transform:uppercase; letter-spacing:.06em; }

.podium-card {
    flex:1; min-width:130px; border-radius:14px;
    padding:0.9rem 0.85rem 0.75rem; background:#fff;
    border:1px solid #e2e8f0; text-align:center;
}
.podium-1 { border-top:4px solid #f59e0b; }
.podium-2 { border-top:4px solid #94a3b8; }
.podium-3 { border-top:4px solid #b45309; }
.podium-pos   { font-size:0.58rem; font-weight:800; text-transform:uppercase; letter-spacing:.07em; color:#94a3b8; margin-bottom:0.2rem; }
.podium-user  { font-size:0.8rem; font-weight:700; color:#0f172a; margin-bottom:0.18rem; line-height:1.25; }
.podium-score { font-size:1.2rem; font-weight:900; color:#1746a2; }
.podium-sub   { font-size:0.63rem; color:#94a3b8; margin-top:0.12rem; }
.gauge-bar-bg  { background:#f1f5f9; border-radius:999px; height:6px; overflow:hidden; margin:0.3rem 0 0.25rem; }
.gauge-bar-fill { height:100%; border-radius:999px; }
.status-pill { display:inline-block; font-size:0.62rem; font-weight:700; padding:0.14rem 0.5rem; border-radius:999px; }
.sp-green { background:#dcfce7; color:#15803d; }
.sp-amber { background:#fef3c7; color:#b45309; }
.sp-red   { background:#fee2e2; color:#991b1b; }

.cat-row { display:flex; align-items:center; gap:0.5rem; padding:0.4rem 0; border-bottom:1px solid #f1f5f9; }
.cat-row:last-child { border-bottom:none; }
.cat-rank  { width:22px; font-size:0.68rem; font-weight:800; color:#94a3b8; flex-shrink:0; }
.cat-name  { flex:1; font-size:0.79rem; font-weight:600; color:#0f172a; }
.cat-bar-wrap { width:70px; }
.cat-score { font-size:0.79rem; font-weight:700; color:#1746a2; width:42px; text-align:right; flex-shrink:0; }

.review-row {
    display:flex; align-items:center; gap:0.6rem;
    padding:0.55rem 0.75rem; border-radius:10px;
    background:#fff; border:1px solid #e2e8f0; margin-bottom:0.4rem;
}
.review-row.is-current { border-color:#1746a2; background:#f0f4ff; }
.rr-rank  { width:28px; font-size:0.82rem; font-weight:800; color:#94a3b8; flex-shrink:0; text-align:center; }
.rr-user  { font-size:0.82rem; font-weight:700; color:#0f172a; }
.rr-stars { font-size:0.78rem; color:#f59e0b; letter-spacing:1px; flex-shrink:0; }
.rr-text  { font-size:0.75rem; color:#64748b; flex:1; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; min-width:0; }
.rr-score { font-size:0.9rem; font-weight:800; flex-shrink:0; }

.prod-info-bar {
    background:#fff; border:1px solid #e2e8f0; border-radius:12px;
    padding:0.65rem 1.1rem; margin-bottom:0.8rem;
    display:flex; gap:2rem; flex-wrap:wrap; align-items:center;
}
.pib-lbl { font-size:0.6rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:.06em; }
.pib-val { font-size:0.9rem; font-weight:700; color:#0f172a; margin-top:1px; }
.pib-accent { color:#1746a2; }
.pib-mono   { font-family:monospace; color:#64748b; font-size:0.78rem; }

@media(max-width:768px){ .gkpi-grid{ grid-template-columns:repeat(2,1fr); } }
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
        Ranking global · Evolucion de resenas por producto · Posicion en tiempo real
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

full_df_base    = _load_full_dataset()
catalog         = get_product_catalog()
global_ranking  = get_global_ranking()
product_options = get_product_options()

# Fusionar Supabase
sb_df = load_reviews_from_supabase()
if not sb_df.empty:
    cat_map = catalog.set_index("ProductId")["Categoria_Real"].to_dict() if not catalog.empty and "Categoria_Real" in catalog.columns else {}
    sb_norm = pd.DataFrame({
        "ProductId":      sb_df["product_id"].astype(str),
        "Score":          pd.to_numeric(sb_df.get("stars", 5), errors="coerce").fillna(5).astype(int),
        "Stars":          pd.to_numeric(sb_df.get("stars", 5), errors="coerce").fillna(5).astype(int),
        "Helpfulness":    pd.to_numeric(sb_df.get("helpfulness", 0), errors="coerce").fillna(0),
        "Estado":         sb_df.get("status", "RECHAZADA (Baja Calidad)"),
        "User":           sb_df.get("usuario", "Nuevo"),
        "Text":           sb_df.get("texto", ""),
        "CreatedAt":      pd.to_datetime(sb_df.get("created_at"), errors="coerce"),
        "Categoria_Real": sb_df["product_id"].astype(str).map(cat_map).fillna("Alimentos generales"),
        "_es_nueva":      True,
    })
    sb_norm["Año"] = sb_norm["CreatedAt"].dt.year.fillna(2026).astype(int)
    full_df_base["_es_nueva"] = False
    full_df = pd.concat([sb_norm, full_df_base], ignore_index=True)
else:
    full_df = full_df_base

# Opciones de filtro
cat_options_full = ["Todas las categorias"]
if not full_df.empty and "Categoria_Real" in full_df.columns:
    cat_options_full += sorted(full_df["Categoria_Real"].dropna().unique().tolist())
años_disponibles = sorted([y for y in full_df["Año"].unique() if y > 2000], reverse=True) if not full_df.empty and "Año" in full_df.columns else []

# Contador + boton actualizar
ref1, ref2 = st.columns([4, 1])
with ref1:
    nuevas = len(sb_df) if not sb_df.empty else 0
    st.markdown(
        f'<div style="padding:.35rem 0;font-size:.82rem;color:#64748b">'
        f'Base total: <strong style="color:#0f172a">{format_compact_number(len(full_df))}</strong> resenas '
        f'({format_compact_number(len(full_df_base))} historicas + '
        f'<span style="color:#15803d;font-weight:700">{nuevas} nuevas</span>)</div>',
        unsafe_allow_html=True,
    )
with ref2:
    if st.button("Actualizar", use_container_width=True):
        clear_supabase_cache()
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_global, tab_producto = st.tabs(["Ranking Global", "Analisis por Producto"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — RANKING GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
with tab_global:

    st.markdown('<div class="section-label">Filtros</div>', unsafe_allow_html=True)
    gc1, gc2, gc3, gc4 = st.columns([2, 1.4, 1.2, 1], gap="medium")
    with gc1: g_cat    = st.selectbox("Categoria",       cat_options_full, key="g_cat")
    with gc2: g_status = st.selectbox("Estado",          ["Todos","APROBADA (Publicada)","RECHAZADA (Baja Calidad)"], key="g_status")
    with gc3: g_year   = st.selectbox("Ano",             ["Todos los anos"] + [str(y) for y in años_disponibles], key="g_year")
    with gc4: g_stars  = st.selectbox("Estrellas min.",  ["Todas","1","2","3","4","5"], key="g_stars")

    def _fg(df):
        out = df.copy()
        if g_cat    != "Todas las categorias"  and "Categoria_Real" in out.columns: out = out[out["Categoria_Real"] == g_cat]
        if g_status != "Todos"                 and "Estado"         in out.columns: out = out[out["Estado"] == g_status]
        if g_year   != "Todos los anos"        and "Año"            in out.columns: out = out[out["Año"] == int(g_year)]
        if g_stars  != "Todas"                 and "Stars"          in out.columns: out = out[out["Stars"] >= int(g_stars)]
        return out

    fdf = _fg(full_df)
    total_r  = len(fdf)
    approved = int((fdf["Estado"] == "APROBADA (Publicada)").sum()) if "Estado" in fdf.columns and total_r > 0 else 0
    rejected = total_r - approved
    avg_help = float(fdf["Helpfulness"].mean()) if "Helpfulness" in fdf.columns and total_r > 0 else 0.0
    appr_rt  = approved / total_r if total_r > 0 else 0.0

    st.markdown('<div class="section-label">Indicadores globales</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="gkpi-grid">
        <div class="gkpi-card gkpi-accent">
            <div class="gkpi-val">{format_compact_number(total_r)}</div>
            <div class="gkpi-lbl">Resenas totales</div>
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

    vc1, vc2 = st.columns(2, gap="medium")
    with vc1:
        st.markdown('<div class="section-label">Distribucion por estado</div>', unsafe_allow_html=True)
        if "Estado" in fdf.columns and total_r > 0:
            ec = fdf["Estado"].value_counts().reset_index()
            ec.columns = ["Estado","Cantidad"]
            color_map = {"APROBADA (Publicada)":"#22c55e","RECHAZADA (Baja Calidad)":"#f59e0b","RECHAZADA (Punto Ciego)":"#f87171"}
            fig_e = px.pie(ec, values="Cantidad", names="Estado", color="Estado",
                           color_discrete_map=color_map, hole=0.58, template="plotly_white")
            fig_e.update_traces(textposition="outside", textinfo="percent+label", textfont_size=10, pull=[0.03]*len(ec))
            fig_e.update_layout(height=240, margin=dict(l=10,r=10,t=20,b=10), showlegend=False)
            st.plotly_chart(fig_e, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sin datos.")

    with vc2:
        st.markdown('<div class="section-label">Evolucion por ano</div>', unsafe_allow_html=True)
        if "Año" in fdf.columns and total_r > 0:
            anual = (fdf[fdf["Año"] > 2000].groupby("Año")
                     .agg(Total=("Helpfulness","count"), Util_Media=("Helpfulness","mean"))
                     .reset_index().sort_values("Año"))
            if not anual.empty:
                fig_ev = go.Figure()
                fig_ev.add_trace(go.Bar(x=anual["Año"].astype(str), y=anual["Total"],
                                        name="Resenas", marker_color="#dbe7ff", opacity=0.85, yaxis="y"))
                fig_ev.add_trace(go.Scatter(x=anual["Año"].astype(str), y=anual["Util_Media"],
                                            name="Utilidad media", line=dict(color="#1746a2", width=2.5),
                                            yaxis="y2", mode="lines+markers", marker_size=5))
                fig_ev.update_layout(
                    height=240, margin=dict(l=10,r=10,t=20,b=10),
                    yaxis=dict(title="Resenas", showgrid=True, gridcolor="#f0f4f8"),
                    yaxis2=dict(title="Utilidad", overlaying="y", side="right", tickformat=".0%", range=[0,1]),
                    xaxis=dict(tickfont_size=9),
                    legend=dict(orientation="h", y=1.12, font_size=9),
                    template="plotly_white", plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_ev, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sin datos temporales.")
        else:
            st.info("Sin informacion de fechas.")

    st.markdown('<div class="section-label">Top 5 categorias por utilidad media</div>', unsafe_allow_html=True)
    cat_col = "Categoria_Real" if "Categoria_Real" in fdf.columns else None
    tcc1, tcc2 = st.columns([1, 1.4], gap="medium")
    if cat_col and total_r > 0:
        cat_stats = (fdf.groupby(cat_col)
                     .agg(n_resenas=(cat_col,"count"), util_media=("Helpfulness","mean"))
                     .reset_index().sort_values("util_media", ascending=False).head(5).reset_index(drop=True))
        bar_colors = ["#f59e0b","#94a3b8","#b45309","#64748b","#64748b"]
        with tcc1:
            cat_html = '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:.7rem .9rem">'
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
                             labels={"util_media":"Utilidad media", cat_col:"Categoria"},
                             template="plotly_white",
                             text=ordered["n_resenas"].apply(lambda x: f"{format_compact_number(int(x))} res."))
            fig_cat.update_coloraxes(showscale=False)
            fig_cat.update_traces(textposition="inside", textfont_size=9)
            fig_cat.update_xaxes(tickformat=".0%", range=[0,1])
            fig_cat.update_layout(height=220, margin=dict(l=10,r=10,t=15,b=10))
            st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sin datos de categorias.")

    pd1, pd2 = st.columns(2, gap="medium")
    star_col = "Stars" if "Stars" in fdf.columns else ("Score" if "Score" in fdf.columns else None)
    with pd1:
        st.markdown('<div class="section-label">Distribucion de estrellas</div>', unsafe_allow_html=True)
        if star_col and total_r > 0:
            sc = fdf[star_col].value_counts().sort_index().reset_index()
            sc.columns = ["Estrellas","Cantidad"]
            sc["Label"] = sc["Estrellas"].apply(lambda x: f"{int(x)} estrella{'s' if int(x)>1 else ''}")
            fig_s = px.bar(sc, x="Label", y="Cantidad", color="Estrellas",
                           color_continuous_scale=["#fee2e2","#fef3c7","#fef9c3","#dcfce7","#15803d"],
                           template="plotly_white", labels={"Label":"","Cantidad":"Resenas"})
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

    st.markdown('<div class="section-label">Top 20 — ranking global por utilidad</div>', unsafe_allow_html=True)
    if not global_ranking.empty:
        top20 = global_ranking.head(20).copy()
        display_cols = [c for c in ["Puesto Global","ProductId","User","Stars","Helpfulness","Estado"] if c in top20.columns]
        if "Helpfulness" in top20.columns:
            top20["Helpfulness"] = top20["Helpfulness"].apply(lambda x: format_percentage(float(x)))
        st.dataframe(top20[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("Sin ranking global disponible.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — ANALISIS POR PRODUCTO
# ─────────────────────────────────────────────────────────────────────────────
with tab_producto:

    # Selector de producto
    col_prod, col_estado = st.columns([2, 1], gap="medium")
    with col_prod:
        selected_product = st.selectbox("Producto a analizar", options=product_options, key="prod_detail")
    with col_estado:
        p_status = st.selectbox("Filtrar por estado", ["Todos","APROBADA (Publicada)","RECHAZADA (Baja Calidad)"], key="p_status")

    if not selected_product:
        st.info("Selecciona un producto para comenzar el analisis.")
        st.stop()

    detail     = get_product_detail(selected_product)
    ranking_df = get_local_product_ranking(selected_product)

    # Aplicar filtro de estado
    if p_status != "Todos" and not ranking_df.empty and "Estado" in ranking_df.columns:
        ranking_df = ranking_df[ranking_df["Estado"] == p_status]

    # Info del producto
    st.markdown(
        f'<div class="prod-info-bar">'
        f'<div><div class="pib-lbl">Producto</div><div class="pib-val">{detail["ProductName"]}</div></div>'
        f'<div><div class="pib-lbl">Categoria</div><div class="pib-val pib-accent">{detail["Categoria_Real"]}</div></div>'
        f'<div><div class="pib-lbl">ID</div><div class="pib-val pib-mono">{detail["ProductId"]}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if ranking_df.empty:
        st.info("No hay resenas disponibles para este producto con el filtro seleccionado.")
        st.stop()

    n_rev    = len(ranking_df)
    top_u    = float(ranking_df["Helpfulness"].max())  if "Helpfulness" in ranking_df.columns else 0.0
    avg_u    = float(ranking_df["Helpfulness"].mean()) if "Helpfulness" in ranking_df.columns else 0.0
    appr_n   = int((ranking_df["Estado"] == "APROBADA (Publicada)").sum()) if "Estado" in ranking_df.columns else 0
    rej_n    = n_rev - appr_n

    # KPIs del producto
    pc1, pc2, pc3, pc4, pc5 = st.columns(5, gap="small")
    with pc1: render_metric_card("Resenas", format_compact_number(n_rev), "Con filtro activo")
    with pc2: render_metric_card("Utilidad max.", format_percentage(top_u), "Mejor resena")
    with pc3: render_metric_card("Utilidad media", format_percentage(avg_u), "Promedio del producto")
    with pc4: render_metric_card("Aprobadas", str(appr_n), "Estado APROBADA")
    with pc5: render_metric_card("Rechazadas", str(rej_n), "Estado RECHAZADA")

    st.markdown("---")

    # ── Seccion A: Podium Top 3 ───────────────────────────────────────────────
    top3 = ranking_df.head(3)
    medals      = ["Oro", "Plata", "Bronce"]
    podium_cls  = ["podium-1","podium-2","podium-3"]
    podium_lbl  = ["1er lugar","2do lugar","3er lugar"]

    st.markdown('<div class="section-label">Podium — Top 3 del producto</div>', unsafe_allow_html=True)
    cols_p = st.columns(min(len(top3), 3), gap="medium")
    for i, (_, row) in enumerate(top3.iterrows()):
        score   = float(row.get("Helpfulness", 0))
        user    = str(row.get("User","—"))[:26]
        stars_n = int(row.get("Stars", row.get("Score", 0)))
        estado  = str(row.get("Estado","—"))
        bar_clr = "#22c55e" if score >= 0.7 else "#f59e0b"
        sp_cls  = "sp-green" if "APROBADA" in estado else "sp-amber"
        sp_lbl  = "Publicada" if "APROBADA" in estado else "Rechazada"
        stars_html = (
            "".join(['<span style="color:#f59e0b;font-size:.75rem">&#9733;</span>' for _ in range(stars_n)]) +
            "".join(['<span style="color:#d1d5db;font-size:.75rem">&#9734;</span>' for _ in range(5-stars_n)])
        )
        with cols_p[i]:
            st.markdown(f"""
            <div class="podium-card {podium_cls[i]}">
                <div class="podium-pos">{podium_lbl[i]}</div>
                <div style="font-size:.7rem;font-weight:700;color:#94a3b8;margin-bottom:.3rem">{medals[i]}</div>
                <div class="podium-user">{user}</div>
                <div class="podium-score">{format_percentage(score)}</div>
                <div class="podium-sub">{stars_html}</div>
                <div class="gauge-bar-bg">
                    <div class="gauge-bar-fill" style="width:{int(score*100)}%;background:{bar_clr}"></div>
                </div>
                <span class="status-pill {sp_cls}">{sp_lbl}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Seccion B: Evolucion de resenas del producto en el tiempo ─────────────
    st.markdown('<div class="section-label">Evolucion de resenas a lo largo del tiempo</div>', unsafe_allow_html=True)

    # Necesitamos fecha en ranking_df — volver a cargar sin filtrar para tener fechas
    rk_full = get_local_product_ranking(selected_product)

    # Enriquecer con fechas si existen en full_df
    if "CreatedAt" not in rk_full.columns or rk_full["CreatedAt"].isna().all():
        # Intentar fusionar fecha desde full_df via ProductId+User
        if "CreatedAt" in full_df.columns:
            fecha_map = (full_df[full_df["ProductId"].astype(str) == str(selected_product)]
                         [["User","CreatedAt"]].drop_duplicates("User").set_index("User")["CreatedAt"].to_dict())
            rk_full["CreatedAt"] = rk_full["User"].map(fecha_map)

    rk_full["CreatedAt"] = pd.to_datetime(rk_full.get("CreatedAt", pd.NaT), errors="coerce")
    rk_full["Año"]       = rk_full["CreatedAt"].dt.year.where(rk_full["CreatedAt"].notna(), other=None)
    rk_full["Mes"]       = rk_full["CreatedAt"].dt.to_period("M").astype(str).where(rk_full["CreatedAt"].notna(), other=None)

    tiene_fechas = rk_full["CreatedAt"].notna().any()

    if tiene_fechas:
        ev1, ev2 = st.columns(2, gap="medium")

        with ev1:
            st.markdown('<div class="section-label">Resenas y utilidad por ano</div>', unsafe_allow_html=True)
            anual_prd = (rk_full[rk_full["Año"].notna()]
                         .groupby("Año")
                         .agg(Total=("Helpfulness","count"), Util_Media=("Helpfulness","mean"))
                         .reset_index().sort_values("Año"))
            if not anual_prd.empty:
                fig_ap = go.Figure()
                fig_ap.add_trace(go.Bar(
                    x=anual_prd["Año"].astype(str), y=anual_prd["Total"],
                    name="Resenas", marker_color="#dbe7ff", opacity=0.9, yaxis="y",
                ))
                fig_ap.add_trace(go.Scatter(
                    x=anual_prd["Año"].astype(str), y=anual_prd["Util_Media"],
                    name="Utilidad media", line=dict(color="#1746a2", width=2.5),
                    yaxis="y2", mode="lines+markers", marker_size=6,
                ))
                fig_ap.add_hline(y=0.70, line_dash="dash", line_color="#22c55e",
                                 yref="y2", annotation_text="Umbral 70%",
                                 annotation_position="top right")
                fig_ap.update_layout(
                    height=260, margin=dict(l=10,r=10,t=25,b=10),
                    yaxis=dict(title="Resenas", showgrid=True, gridcolor="#f0f4f8"),
                    yaxis2=dict(title="Utilidad", overlaying="y", side="right",
                                tickformat=".0%", range=[0,1]),
                    xaxis=dict(tickfont_size=9),
                    legend=dict(orientation="h", y=1.15, font_size=9),
                    template="plotly_white", plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_ap, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sin datos anuales.")

        with ev2:
            st.markdown('<div class="section-label">Distribucion de utilidad por estrellas</div>', unsafe_allow_html=True)
            star_col_rk = "Stars" if "Stars" in rk_full.columns else ("Score" if "Score" in rk_full.columns else None)
            if star_col_rk and "Helpfulness" in rk_full.columns and len(rk_full) > 0:
                rk_box = rk_full.copy()
                rk_box["Estrellas"] = rk_box[star_col_rk].apply(lambda x: f"{int(x)} estrellas")
                fig_box = px.box(
                    rk_box, x="Estrellas", y="Helpfulness",
                    color="Estrellas",
                    color_discrete_sequence=["#fee2e2","#fef3c7","#fef9c3","#dcfce7","#22c55e"],
                    template="plotly_white",
                    labels={"Helpfulness":"Utilidad","Estrellas":""},
                )
                fig_box.update_yaxes(tickformat=".0%", range=[0,1])
                fig_box.add_hline(y=0.70, line_dash="dash", line_color="#1746a2",
                                  annotation_text="Umbral 70%", annotation_position="top right")
                fig_box.update_layout(height=260, margin=dict(l=10,r=10,t=25,b=10),
                                      showlegend=False)
                st.plotly_chart(fig_box, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sin datos suficientes.")

        # Evolucion temporal mensual — scatter con color por utilidad
        st.markdown('<div class="section-label">Utilidad de cada resena a lo largo del tiempo</div>', unsafe_allow_html=True)
        rk_scatter = rk_full[rk_full["CreatedAt"].notna()].copy()
        if not rk_scatter.empty:
            rk_scatter["Estado_Simple"] = rk_scatter["Estado"].apply(
                lambda x: "Aprobada" if "APROBADA" in str(x) else "Rechazada"
            )
            fig_sc = px.scatter(
                rk_scatter,
                x="CreatedAt",
                y="Helpfulness",
                color="Estado_Simple",
                color_discrete_map={"Aprobada":"#22c55e","Rechazada":"#f87171"},
                hover_data={
                    "User": True,
                    "Helpfulness": ":.1%",
                    "CreatedAt": True,
                    "Estado_Simple": False,
                },
                labels={"CreatedAt":"Fecha","Helpfulness":"Utilidad","Estado_Simple":"Estado"},
                template="plotly_white",
            )
            fig_sc.add_hline(y=0.70, line_dash="dash", line_color="#1746a2",
                             annotation_text="Umbral aprobacion (70%)",
                             annotation_position="top right")
            fig_sc.update_yaxes(tickformat=".0%", range=[-0.05,1.05])
            fig_sc.update_traces(marker_size=8, opacity=0.82)
            fig_sc.update_layout(
                height=300, margin=dict(l=10,r=10,t=25,b=10),
                legend=dict(orientation="h", y=1.12, font_size=10),
            )
            st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

        # Resumen por ano: tabla de aprobadas vs rechazadas
        st.markdown('<div class="section-label">Resumen anual — aprobadas vs rechazadas</div>', unsafe_allow_html=True)
        if not anual_prd.empty and "Estado" in rk_full.columns:
            anual_estado = (rk_full[rk_full["Año"].notna()]
                            .groupby(["Año","Estado"])
                            .size().reset_index(name="Cantidad"))
            fig_ae = px.bar(
                anual_estado, x="Año", y="Cantidad", color="Estado",
                barmode="stack",
                color_discrete_map={
                    "APROBADA (Publicada)":"#22c55e",
                    "RECHAZADA (Baja Calidad)":"#f59e0b",
                    "RECHAZADA (Punto Ciego)":"#f87171",
                },
                labels={"Año":"","Cantidad":"Resenas","Estado":"Estado"},
                template="plotly_white",
            )
            fig_ae.update_layout(height=240, margin=dict(l=10,r=10,t=20,b=10),
                                 legend=dict(orientation="h", y=1.15, font_size=9))
            st.plotly_chart(fig_ae, use_container_width=True, config={"displayModeBar": False})

    else:
        st.info("No hay informacion de fechas disponible para este producto.")

    st.markdown("---")

    # ── Seccion C: Ranking completo de resenas del producto ───────────────────
    st.markdown('<div class="section-label">Todas las resenas del producto — ranking por utilidad</div>', unsafe_allow_html=True)

    latest_review_id = st.session_state.get("latest_review_id")
    display_rk = ranking_df.copy()
    display_rk["Puesto"] = range(1, len(display_rk) + 1)

    for _, row in display_rk.iterrows():
        score   = float(row.get("Helpfulness", 0))
        user    = str(row.get("User","—"))[:30]
        stars_n = int(row.get("Stars", row.get("Score", 0)))
        estado  = str(row.get("Estado","—"))
        text_pre = str(row.get("Text",""))[:90] + ("..." if len(str(row.get("Text",""))) > 90 else "")
        puesto  = int(row.get("Puesto", 0))
        is_cur  = str(row.get("ReviewId","")) == str(latest_review_id) if latest_review_id else False
        score_clr = "#15803d" if score >= 0.7 else ("#b45309" if score >= 0.4 else "#dc2626")
        sp_cls  = "sp-green" if "APROBADA" in estado else "sp-amber"
        sp_lbl  = "Publicada" if "APROBADA" in estado else "Rechazada"
        stars_str = "★" * stars_n + "☆" * (5 - stars_n)
        hl_cls  = " is-current" if is_cur else ""
        my_badge = (' <span style="font-size:.6rem;background:#1746a2;color:#fff;'
                    'padding:1px 6px;border-radius:4px;margin-left:4px">Tu resena</span>') if is_cur else ""

        st.markdown(
            f'<div class="review-row{hl_cls}">'
            f'<div class="rr-rank">#{puesto}</div>'
            f'<div style="display:flex;flex-direction:column;flex:1;min-width:0;gap:2px">'
            f'<div style="display:flex;align-items:center;gap:.5rem">'
            f'<span class="rr-user">{user}</span>'
            f'<span class="rr-stars">{stars_str}</span>'
            f'{my_badge}'
            f'</div>'
            f'<div class="rr-text">{text_pre}</div>'
            f'</div>'
            f'<div class="rr-score" style="color:{score_clr}">{format_percentage(score)}</div>'
            f'<span class="status-pill {sp_cls}">{sp_lbl}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Seccion D: Tu resena en contexto ─────────────────────────────────────
    st.markdown('<div class="section-label">Tu resena en contexto</div>', unsafe_allow_html=True)
    position_summary = get_position_summary(selected_product, latest_review_id)
    review_window_df = get_review_context_window(selected_product, latest_review_id, window_size=2)

    p1, p2, p3 = st.columns(3, gap="medium")
    with p1:
        render_metric_card(
            "Posicion local",
            f"{position_summary['local_rank']} / {position_summary['product_count']}" if position_summary["local_rank"] else "Sin resena evaluada",
            "Lugar dentro del producto",
        )
    with p2:
        render_metric_card(
            "Posicion global",
            f"{position_summary['global_rank']} / {position_summary['global_count']}" if position_summary["global_rank"] else "Sin resena evaluada",
            "Lugar en toda la base",
        )
    with p3:
        render_metric_card(
            "Total del producto",
            format_compact_number(position_summary["product_count"]),
            "Volumen historico",
        )

    if latest_review_id and not review_window_df.empty:
        for _, row in review_window_df.iterrows():
            render_review_card(
                user_name=str(row["User"]),
                stars=int(row["Stars"]),
                review_text=str(row["Text"]),
                meta_line=f"Puesto local {int(row['Puesto Local'])}",
                badge="Tu resena" if row["EsActual"] else row["Estado"],
                helpfulness=format_percentage(float(row["Helpfulness"])),
                highlighted=bool(row["EsActual"]),
            )
    else:
        st.info("Analiza una resena en Auditoria para ver tu posicion aqui.")

st.session_state["selected_product_id"] = selected_product if "selected_product" in dir() else (product_options[0] if product_options else None)