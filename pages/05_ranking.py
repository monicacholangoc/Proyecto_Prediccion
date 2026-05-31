"""Ranking y Benchmark — KPIs globales sobre dataset completo, filtro por categoría."""

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
from services.supabase_service import load_reviews_from_supabase, clear_supabase_cache
from config.constants import TOPIC_NAMES
from utils.formatters import format_compact_number, format_percentage

# ── CSS ───────────────────────────────────────────────────────────────────────
with open("styles/styles.css", "r", encoding="utf-8") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
.podium-card {
    flex:1; min-width:140px;
    border-radius:14px; padding:0.85rem 0.8rem 0.7rem;
    background:var(--surface-soft); border:1px solid var(--border);
    box-shadow:var(--shadow-soft); text-align:center;
    transition:transform .18s;
}
.podium-card:hover { transform:translateY(-3px); }
.podium-1 { border-top:4px solid #f59e0b; }
.podium-2 { border-top:4px solid #94a3b8; }
.podium-3 { border-top:4px solid #b45309; }
.podium-pos   { font-size:0.6rem; font-weight:800; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin-bottom:0.15rem; }
.podium-user  { font-size:0.82rem; font-weight:700; color:var(--text); margin-bottom:0.2rem; line-height:1.2; }
.podium-score { font-size:1.15rem; font-weight:800; color:var(--primary); }
.podium-sub   { font-size:0.65rem; color:var(--muted); }
.gauge-bar-wrap { margin:0.3rem 0 0.1rem; }
.gauge-bar-bg   { background:var(--border); border-radius:999px; height:7px; overflow:hidden; }
.gauge-bar-fill { height:100%; border-radius:999px; }
.cat-row { display:flex; align-items:center; gap:0.5rem; padding:0.38rem 0; border-bottom:1px solid var(--border); }
.cat-row:last-child { border-bottom:none; }
.cat-rank  { width:20px; font-size:0.7rem; font-weight:800; color:var(--muted); flex-shrink:0; }
.cat-name  { flex:1; font-size:0.8rem; font-weight:600; color:var(--text); }
.cat-bar-wrap { width:72px; }
.cat-score { font-size:0.8rem; font-weight:700; color:var(--primary); width:42px; text-align:right; flex-shrink:0; }
.gkpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:0.5rem; margin-bottom:0.5rem; }
.gkpi-card {
    background:var(--surface-soft); border:1px solid var(--border);
    border-radius:14px; padding:0.8rem 0.9rem;
    box-shadow:var(--shadow-soft); text-align:center;
}
.gkpi-val { font-size:1.3rem; font-weight:800; color:var(--text); line-height:1; }
.gkpi-lbl { font-size:0.68rem; color:var(--muted); margin-top:0.15rem; }
.gkpi-accent { border-top:3px solid var(--primary); }
.status-pill { display:inline-block; font-size:0.65rem; font-weight:700; padding:0.15rem 0.5rem; border-radius:999px; }
.sp-green { background:#dcfce7; color:#15803d; }
.sp-amber { background:#fef3c7; color:#b45309; }
.sp-red   { background:#fee2e2; color:#991b1b; }
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
        Comparativa global de resenas · Top categorias · Posicion relativa en tiempo real
    </div>
</div>
""", unsafe_allow_html=True)

# ── Cargar DATASET COMPLETO (no solo las 1000 de la DB operativa) ─────────────
@st.cache_data(show_spinner=False)
def _load_full_dataset() -> pd.DataFrame:
    """Carga el parquet completo priorizando el enriquecido con categorias de alimento."""
    # Prioridad: reviews_con_categoria (tiene categoria_alimento con 16+ cats)
    # Fallback: reviews_limpias (solo 5 topics LDA o ninguna categoria)
    df = add_basic_text_features(load_reviews_with_category())
    if df.empty:
        df = add_basic_text_features(load_processed_reviews())
    if df.empty:
        return df

    # Normalizar columna de categoria: preferir categoria_alimento
    if "categoria_alimento" in df.columns:
        df["Categoria_Real"] = df["categoria_alimento"]
    elif "product_topic" in df.columns and "Categoria_Real" not in df.columns:
        df["Categoria_Real"] = df["product_topic"].map(TOPIC_NAMES).fillna("Alimentos generales")
    elif "Categoria_Real" not in df.columns:
        df["Categoria_Real"] = "Alimentos generales"

    # Año desde Time (unix) o CreatedAt
    if "Time" in df.columns:
        df["CreatedAt"] = pd.to_datetime(df["Time"], unit="s", errors="coerce")
    elif "CreatedAt" in df.columns:
        df["CreatedAt"] = pd.to_datetime(df["CreatedAt"], errors="coerce")
    else:
        df["CreatedAt"] = pd.NaT
    df["Año"] = df["CreatedAt"].dt.year.where(df["CreatedAt"].notna(), other=0).astype(int)

    # Helpfulness y Estado
    if "y_util" in df.columns:
        df["Helpfulness"] = df["y_util"].astype(float)
        df["Estado"] = df["y_util"].apply(
            lambda x: "APROBADA (Publicada)" if x == 1 else "RECHAZADA (Baja Calidad)"
        )
    elif "Helpfulness" not in df.columns:
        if "HelpfulnessNumerator" in df.columns and "HelpfulnessDenominator" in df.columns:
            denom = df["HelpfulnessDenominator"].replace(0, pd.NA)
            df["Helpfulness"] = (df["HelpfulnessNumerator"] / denom).fillna(0)
        else:
            df["Helpfulness"] = 0.5
        df["Estado"] = df["Helpfulness"].apply(
            lambda x: "APROBADA (Publicada)" if x >= 0.70 else "RECHAZADA (Baja Calidad)"
        )

    # Stars desde Score
    if "Stars" not in df.columns and "Score" in df.columns:
        df["Stars"] = df["Score"]

    return df

full_df_base = _load_full_dataset()
catalog      = get_product_catalog()
op_db        = get_corporate_audit_db()
global_ranking = get_global_ranking()

# ── Fusionar reseñas nuevas de Supabase al full_df ───────────────────────────
# Esto garantiza que los KPIs globales reflejen el total real (histórico + nuevas)
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
    # Concatenar nuevas PRIMERO para que aparezcan arriba
    full_df = pd.concat([sb_norm, full_df_base], ignore_index=True)
else:
    full_df = full_df_base

# Enriquecer op_db con año
if not op_db.empty:
    if "CreatedAt" in op_db.columns:
        op_db["CreatedAt"] = pd.to_datetime(op_db["CreatedAt"], errors="coerce")
        op_db["Año"] = op_db["CreatedAt"].dt.year.fillna(0).astype(int)
    else:
        op_db["Año"] = 0

# ── Opciones de categoría para el filtro ─────────────────────────────────────
cat_options_full = ["Todas las categorias"]
if not full_df.empty and "Categoria_Real" in full_df.columns:
    cats = sorted(full_df["Categoria_Real"].dropna().unique().tolist())
    cat_options_full += cats
elif not catalog.empty and "Categoria_Real" in catalog.columns:
    cats = sorted(catalog["Categoria_Real"].dropna().unique().tolist())
    cat_options_full += cats

años_disponibles = []
if not full_df.empty and "Año" in full_df.columns:
    años_disponibles = sorted([y for y in full_df["Año"].unique() if y > 2000], reverse=True)

product_options = get_product_options()

# ── Filtros ───────────────────────────────────────────────────────────────────
# ── Botón actualizar datos en tiempo real ────────────────────────────────────
ref_col1, ref_col2 = st.columns([4, 1], gap="medium")
with ref_col1:
    nuevas_count = len(sb_df) if not sb_df.empty else 0
    st.markdown(
        f'<div style="padding:0.4rem 0;font-size:0.82rem;color:var(--muted)">'
        f'📊 Total en base: <strong>{format_compact_number(len(full_df))}</strong> reseñas '
        f'({format_compact_number(len(full_df_base))} históricas + '
        f'<span style="color:#15803d;font-weight:700">{nuevas_count} nuevas</span>)'
        f'</div>',
        unsafe_allow_html=True,
    )
with ref_col2:
    if st.button("🔄 Actualizar", use_container_width=True):
        clear_supabase_cache()
        st.rerun()

st.markdown('<div class="section-label">Filtros globales</div>', unsafe_allow_html=True)
fc1, fc2, fc3, fc4 = st.columns([2, 1.4, 1.2, 1], gap="medium")

with fc1:
    selected_cat = st.selectbox("Categoria", options=cat_options_full)
with fc2:
    selected_status = st.selectbox(
        "Estado",
        options=["Todos", "APROBADA (Publicada)", "RECHAZADA (Baja Calidad)"]
    )
with fc3:
    year_options = ["Todos los anos"] + [str(y) for y in años_disponibles]
    selected_year = st.selectbox("Ano", options=year_options)
with fc4:
    star_opts = ["Todas", "1", "2", "3", "4", "5"]
    min_stars = st.selectbox("Estrellas min.", options=star_opts)

# Selector de producto (para el podium y la seccion "tu resena")
st.markdown('<div class="section-label">Producto para podium y posicion personal</div>', unsafe_allow_html=True)
if product_options:
    selected_product = st.selectbox("Producto", options=product_options, label_visibility="visible")
    detail = get_product_detail(selected_product)
    st.caption(f"**{detail['ProductName']}** · `{detail['ProductId']}` · Categoria: {detail['Categoria_Real']}")
else:
    selected_product = None

# ── Funcion de filtrado ───────────────────────────────────────────────────────
def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if selected_cat != "Todas las categorias" and "Categoria_Real" in out.columns:
        out = out[out["Categoria_Real"] == selected_cat]
    if selected_status != "Todos" and "Estado" in out.columns:
        out = out[out["Estado"] == selected_status]
    if selected_year != "Todos los anos" and "Año" in out.columns:
        out = out[out["Año"] == int(selected_year)]
    if min_stars != "Todas" and "Stars" in out.columns:
        out = out[out["Stars"] >= int(min_stars)]
    return out

filtered_full = _apply_filters(full_df)

# ── KPIs GLOBALES (sobre dataset completo filtrado) ───────────────────────────
st.markdown('<div class="section-label">Indicadores globales</div>', unsafe_allow_html=True)

total_r    = len(filtered_full)
approved   = int((filtered_full["Estado"] == "APROBADA (Publicada)").sum()) if "Estado" in filtered_full.columns and total_r > 0 else 0
rejected   = total_r - approved
avg_help   = float(filtered_full["Helpfulness"].mean()) if "Helpfulness" in filtered_full.columns and total_r > 0 else 0.0
appr_rate  = approved / total_r if total_r > 0 else 0.0
n_products = int(filtered_full["ProductId"].astype(str).nunique()) if "ProductId" in filtered_full.columns else 0

st.markdown(f"""
<div class="gkpi-grid">
    <div class="gkpi-card gkpi-accent">
        <div class="gkpi-val">{format_compact_number(total_r)}</div>
        <div class="gkpi-lbl">Resenas en base</div>
    </div>
    <div class="gkpi-card" style="border-top:3px solid #15803d">
        <div class="gkpi-val" style="color:#15803d">{format_compact_number(approved)}</div>
        <div class="gkpi-lbl">Aprobadas · {format_percentage(appr_rate)}</div>
    </div>
    <div class="gkpi-card" style="border-top:3px solid #b45309">
        <div class="gkpi-val" style="color:#b45309">{format_compact_number(rejected)}</div>
        <div class="gkpi-lbl">Rechazadas</div>
    </div>
    <div class="gkpi-card" style="border-top:3px solid #0f9f74">
        <div class="gkpi-val">{format_percentage(avg_help)}</div>
        <div class="gkpi-lbl">Utilidad media global</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Graficas: distribucion estado + evolucion mensual ─────────────────────────
vc1, vc2 = st.columns(2, gap="medium")

with vc1:
    st.markdown('<div class="section-label">Distribucion por estado</div>', unsafe_allow_html=True)
    if "Estado" in filtered_full.columns and total_r > 0:
        ec = filtered_full["Estado"].value_counts().reset_index()
        ec.columns = ["Estado", "Cantidad"]
        color_map = {
            "APROBADA (Publicada)":     "#15803d",
            "RECHAZADA (Baja Calidad)": "#b45309",
            "RECHAZADA (Punto Ciego)":  "#991b1b",
            "Sin clasificar":           "#94a3b8",
        }
        fig_e = px.pie(ec, values="Cantidad", names="Estado",
                       color="Estado", color_discrete_map=color_map,
                       hole=0.55, template="plotly_white")
        fig_e.update_traces(textposition="outside", textinfo="percent+label",
                             textfont_size=10, pull=[0.03]*len(ec))
        fig_e.update_layout(height=240, margin=dict(l=10,r=10,t=20,b=10),
                             showlegend=False)
        st.plotly_chart(fig_e, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sin datos para graficar.")

with vc2:
    st.markdown('<div class="section-label">Evolucion de resenas por ano</div>', unsafe_allow_html=True)
    if "Año" in filtered_full.columns and "CreatedAt" in filtered_full.columns and total_r > 0:
        anual = (
            filtered_full[filtered_full["Año"] > 2000]
            .groupby("Año")
            .agg(Total=("Helpfulness","count"), Util_Media=("Helpfulness","mean"))
            .reset_index()
            .sort_values("Año")
        )
        if not anual.empty:
            fig_ev = go.Figure()
            fig_ev.add_trace(go.Bar(
                x=anual["Año"].astype(str), y=anual["Total"],
                name="Resenas", marker_color="#dbe7ff", opacity=0.85, yaxis="y",
            ))
            fig_ev.add_trace(go.Scatter(
                x=anual["Año"].astype(str), y=anual["Util_Media"],
                name="Utilidad media", line=dict(color="#1746a2", width=2.5),
                yaxis="y2", mode="lines+markers", marker_size=5,
            ))
            fig_ev.update_layout(
                height=240, margin=dict(l=10,r=10,t=20,b=10),
                yaxis=dict(title="Resenas", showgrid=True, gridcolor="#f0f4f8"),
                yaxis2=dict(title="Utilidad", overlaying="y", side="right",
                            tickformat=".0%", range=[0,1]),
                xaxis=dict(tickfont_size=9),
                legend=dict(orientation="h", y=1.1, font_size=9),
                template="plotly_white", plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_ev, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sin datos temporales.")
    else:
        st.info("Sin informacion de fechas disponible.")

# ── Top 5 Categorias ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Top 5 categorias por utilidad media</div>', unsafe_allow_html=True)

cat_col = "Categoria_Real" if "Categoria_Real" in filtered_full.columns else None

tcc1, tcc2 = st.columns([1, 1.4], gap="medium")

if cat_col and total_r > 0:
    cat_stats = (
        filtered_full.groupby(cat_col)
        .agg(
            n_resenas=(cat_col, "count"),
            util_media=("Helpfulness", "mean"),
        )
        .reset_index()
        .sort_values("util_media", ascending=False)
        .head(5)
        .reset_index(drop=True)
    )

    rank_labels = ["1", "2", "3", "4", "5"]
    bar_colors  = ["#f59e0b","#94a3b8","#b45309","#64748b","#64748b"]

    with tcc1:
        cat_html = '<div style="background:var(--surface-soft);border:1px solid var(--border);border-radius:14px;padding:0.7rem 0.9rem;">'
        for i, row in cat_stats.iterrows():
            bar_w     = int(row["util_media"] * 100)
            bar_color = bar_colors[i] if i < len(bar_colors) else "#64748b"
            cat_html += f"""
            <div class="cat-row">
                <div class="cat-rank">#{rank_labels[i]}</div>
                <div class="cat-name">{row[cat_col]}</div>
                <div class="cat-bar-wrap">
                    <div class="gauge-bar-bg">
                        <div class="gauge-bar-fill" style="width:{bar_w}%;background:{bar_color}"></div>
                    </div>
                </div>
                <div class="cat-score">{row['util_media']:.1%}</div>
            </div>"""
        cat_html += "</div>"
        st.markdown(cat_html, unsafe_allow_html=True)

    with tcc2:
        ordered = cat_stats.sort_values("util_media", ascending=True)
        fig_cat = px.bar(
            ordered, x="util_media", y=cat_col, orientation="h",
            color="util_media",
            color_continuous_scale=["#fef3c7","#f59e0b","#15803d"],
            labels={"util_media":"Utilidad media", cat_col:"Categoria"},
            template="plotly_white",
            text=ordered["n_resenas"].apply(lambda x: f"{format_compact_number(int(x))} res."),
        )
        fig_cat.update_coloraxes(showscale=False)
        fig_cat.update_traces(textposition="inside", textfont_size=9)
        fig_cat.update_xaxes(tickformat=".0%", range=[0,1])
        fig_cat.update_layout(height=220, margin=dict(l=10,r=10,t=15,b=10))
        st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Sin datos de categorias para el filtro actual.")

# ── Graficas del dataset filtrado: estrellas + utilidad por estrella ───────────
pd1, pd2 = st.columns(2, gap="medium")

with pd1:
    st.markdown('<div class="section-label">Distribucion de estrellas</div>', unsafe_allow_html=True)
    star_col = "Stars" if "Stars" in filtered_full.columns else ("Score" if "Score" in filtered_full.columns else None)
    if star_col and total_r > 0:
        sc = filtered_full[star_col].value_counts().sort_index().reset_index()
        sc.columns = ["Estrellas","Cantidad"]
        sc["Label"] = sc["Estrellas"].apply(lambda x: f"{int(x)} estrella{'s' if int(x)>1 else ''}")
        fig_s = px.bar(sc, x="Label", y="Cantidad",
                       color="Estrellas",
                       color_continuous_scale=["#fee2e2","#fef3c7","#fef9c3","#dcfce7","#15803d"],
                       template="plotly_white",
                       labels={"Label":"","Cantidad":"Resenas"})
        fig_s.update_coloraxes(showscale=False)
        fig_s.update_layout(height=210, margin=dict(l=10,r=10,t=15,b=10))
        st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sin datos de estrellas.")

with pd2:
    st.markdown('<div class="section-label">Utilidad media por estrella</div>', unsafe_allow_html=True)
    if star_col and "Helpfulness" in filtered_full.columns and total_r > 0:
        ubs = filtered_full.groupby(star_col)["Helpfulness"].mean().reset_index()
        ubs.columns = ["Estrellas","Utilidad_media"]
        ubs["Label"] = ubs["Estrellas"].apply(lambda x: f"{int(x)} estrellas")
        fig_us = px.line(ubs, x="Label", y="Utilidad_media",
                         markers=True, template="plotly_white",
                         labels={"Label":"","Utilidad_media":"Utilidad media"},
                         color_discrete_sequence=["#1746a2"])
        fig_us.update_yaxes(tickformat=".0%", range=[0,1])
        fig_us.update_traces(line_width=2.5, marker_size=7)
        fig_us.update_layout(height=210, margin=dict(l=10,r=10,t=15,b=10))
        st.plotly_chart(fig_us, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sin datos suficientes.")

# ── Podium Top 3 del PRODUCTO seleccionado ───────────────────────────────────
if selected_product:
    ranking_df     = get_local_product_ranking(selected_product)
    filtered_local = _apply_filters(ranking_df) if not ranking_df.empty else pd.DataFrame()

    top_score  = float(filtered_local["Helpfulness"].max())  if not filtered_local.empty else 0.0
    avg_score  = float(filtered_local["Helpfulness"].mean()) if not filtered_local.empty else 0.0
    n_rev_prd  = len(filtered_local)
    appr_prd   = int((filtered_local["Estado"] == "APROBADA (Publicada)").sum()) if "Estado" in filtered_local.columns else 0
    rej_prd    = n_rev_prd - appr_prd

    st.markdown('<div class="section-label">Indicadores del producto seleccionado</div>', unsafe_allow_html=True)
    pc1, pc2, pc3, pc4, pc5 = st.columns(5, gap="small")
    with pc1: render_metric_card("Resenas", format_compact_number(n_rev_prd), "Con los filtros activos")
    with pc2: render_metric_card("Utilidad max.", format_percentage(top_score), "Resena mejor puntuada")
    with pc3: render_metric_card("Utilidad media", format_percentage(avg_score), "Promedio del producto")
    with pc4: render_metric_card("Aprobadas", str(appr_prd), "Estado APROBADA")
    with pc5: render_metric_card("Rechazadas", str(rej_prd), "Estado RECHAZADA")

    podium_colors = ["podium-1","podium-2","podium-3"]
    podium_labels = ["1er lugar","2do lugar","3er lugar"]
    top3 = filtered_local.head(3) if not filtered_local.empty else pd.DataFrame()

    st.markdown('<div class="section-label">Podium — Top 3 del producto</div>', unsafe_allow_html=True)
    if not top3.empty:
        cols_p = st.columns(len(top3), gap="medium")
        for i, (_, row) in enumerate(top3.iterrows()):
            score   = float(row.get("Helpfulness", 0))
            user    = str(row.get("User","—"))[:24]
            stars_n = int(row.get("Stars", row.get("Score", 0)))
            estado  = str(row.get("Estado","—"))
            bar_w   = int(score * 100)
            sp_cls  = "sp-green" if "APROBADA" in estado else "sp-amber"
            sp_lbl  = "Publicada" if "APROBADA" in estado else "Rechazada"
            stars_html = " ".join(
                [f'<span style="color:#f59e0b;font-size:0.75rem">&#9733;</span>' for _ in range(stars_n)] +
                [f'<span style="color:#d1d5db;font-size:0.75rem">&#9734;</span>' for _ in range(5-stars_n)]
            )
            with cols_p[i]:
                st.markdown(f"""
                <div class="podium-card {podium_colors[i]}">
                    <div class="podium-pos">{podium_labels[i]}</div>
                    <div class="podium-user">{user}</div>
                    <div class="podium-score">{format_percentage(score)}</div>
                    <div class="podium-sub">{stars_html}</div>
                    <div class="gauge-bar-wrap">
                        <div class="gauge-bar-bg">
                            <div class="gauge-bar-fill" style="width:{bar_w}%;background:{'#15803d' if score>=.7 else '#b45309'}"></div>
                        </div>
                    </div>
                    <div style="margin-top:0.3rem"><span class="status-pill {sp_cls}">{sp_lbl}</span></div>
                </div>
                """, unsafe_allow_html=True)

        if len(filtered_local) > 3:
            st.markdown('<div class="section-label">Posiciones 4 al 10</div>', unsafe_allow_html=True)
            rest = filtered_local.iloc[3:10].copy()
            rest["Puesto"]   = range(4, 4 + len(rest))
            rest["Utilidad"] = rest["Helpfulness"].apply(format_percentage)
            rest["Estrellas"]= rest.get("Stars", rest.get("Score", pd.Series([0]*len(rest)))).apply(
                lambda x: str(int(x)) + " str."
            )
            display_rest = rest[["Puesto","User","Estrellas","Utilidad","Estado"]].rename(columns={"User":"Usuario"})
            st.dataframe(display_rest, use_container_width=True, hide_index=True)
    else:
        st.info("No hay resenas para los filtros seleccionados.")

    # ── Tu resena en contexto ─────────────────────────────────────────────────
    st.markdown('<div class="section-label">Tu resena en contexto</div>', unsafe_allow_html=True)
    latest_review_id = st.session_state.get("latest_review_id")
    position_summary = get_position_summary(selected_product, latest_review_id)
    review_window_df = get_review_context_window(selected_product, latest_review_id, window_size=2)

    p1, p2, p3 = st.columns(3, gap="medium")
    with p1:
        render_metric_card(
            "Posicion local",
            f"{position_summary['local_rank']} / {position_summary['product_count']}" if position_summary["local_rank"] else "Sin resena evaluada",
            "Lugar dentro del producto"
        )
    with p2:
        render_metric_card(
            "Posicion global",
            f"{position_summary['global_rank']} / {position_summary['global_count']}" if position_summary["global_rank"] else "Sin resena evaluada",
            "Lugar en toda la base"
        )
    with p3:
        render_metric_card(
            "Total del producto",
            format_compact_number(position_summary["product_count"]),
            "Volumen historico"
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

# ── Top 20 global ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-label">Top 20 global por utilidad</div>', unsafe_allow_html=True)

if not global_ranking.empty:
    top20 = global_ranking.head(20).copy()
    display_cols = [c for c in ["Puesto Global","ProductId","User","Stars","Helpfulness","Estado"] if c in top20.columns]
    if "Helpfulness" in top20.columns:
        top20["Helpfulness"] = top20["Helpfulness"].apply(lambda x: format_percentage(float(x)))
    st.dataframe(top20[display_cols], use_container_width=True, hide_index=True)
# ── Reseñas guardadas en Supabase — tiempo real ───────────────────────────────
st.markdown("---")
st.markdown('<div class="section-label">📡 Reseñas auditadas — tiempo real (Supabase)</div>', unsafe_allow_html=True)

sb_col1, sb_col2 = st.columns([3, 1], gap="medium")
with sb_col1:
    st.caption("Reseñas guardadas por todos los usuarios · Se actualiza automáticamente cada 30 segundos")
with sb_col2:
    if st.button("🔄 Actualizar ahora"):
        clear_supabase_cache()
        st.rerun()

df_supabase = load_reviews_from_supabase()

if not df_supabase.empty:
    sb_total    = len(df_supabase)
    sb_approved = int((df_supabase["status"].str.contains("APROBADA", na=False)).sum())
    sb_avg_help = float(df_supabase["helpfulness"].mean()) if "helpfulness" in df_supabase.columns else 0.0

    sk1, sk2, sk3 = st.columns(3, gap="medium")
    with sk1:
        render_metric_card("Reseñas guardadas", format_compact_number(sb_total), "Total en Supabase")
    with sk2:
        render_metric_card("Aprobadas", str(sb_approved), "Estado APROBADA")
    with sk3:
        render_metric_card("Utilidad media", format_percentage(sb_avg_help), "Promedio de probabilidad")

    display_sb = df_supabase[[c for c in [
        "id", "product_id", "usuario", "stars",
        "helpfulness", "status", "review_len", "created_at"
    ] if c in df_supabase.columns]].copy()

    if "helpfulness" in display_sb.columns:
        display_sb["helpfulness"] = display_sb["helpfulness"].apply(lambda x: format_percentage(float(x)))
    if "created_at" in display_sb.columns:
        display_sb["created_at"] = pd.to_datetime(
            display_sb["created_at"], errors="coerce"
        ).dt.strftime("%Y-%m-%d %H:%M")

    display_sb = display_sb.rename(columns={
        "id": "ID", "product_id": "Producto", "usuario": "Usuario",
        "stars": "Estrellas", "helpfulness": "Utilidad",
        "status": "Estado", "review_len": "Palabras", "created_at": "Fecha",
    })
    st.dataframe(display_sb, use_container_width=True, hide_index=True)

    if "helpfulness" in df_supabase.columns and sb_total > 1:
        fig_sb = px.histogram(
            df_supabase, x="helpfulness", nbins=20,
            title="Distribución de utilidad — reseñas en Supabase",
            labels={"helpfulness": "Probabilidad de utilidad"},
            color_discrete_sequence=["#1746a2"], template="plotly_white",
        )
        fig_sb.add_vline(x=0.70, line_dash="dash", line_color="#15803d",
                         annotation_text="Umbral aprobación (70%)",
                         annotation_position="top right")
        fig_sb.update_layout(height=240, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_sb, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("Aún no hay reseñas guardadas en Supabase. Audita una reseña en la página de Auditoría para verla aquí.")