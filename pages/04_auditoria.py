"""Ranking y Benchmark — versión mejorada con KPIs visuales, filtros de año/estado y top categorías."""

# ── Guard: redirige a main.py si se accede directamente sin sesión ──────────
try:
    import streamlit as _st
    if not _st.session_state.get("app_initialized"):
        _st.switch_page("main.py")
except Exception:
    pass
# ────────────────────────────────────────────────────────────────────────────

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shared_sidebar import render_sidebar
from components.cards import render_metric_card, render_review_card
from services.catalog_service import get_product_detail, get_product_options, get_product_catalog
from services.preprocessing_service import (
    get_audited_reviews_operational_table,
    get_corporate_audit_db,
    get_global_ranking,
    get_local_product_ranking,
    get_position_summary,
    get_product_reviews_by_date,
    get_review_context_window,
)
from utils.formatters import format_compact_number, format_percentage

# ── CSS adicional para esta página ───────────────────────────────────────────
with open("styles/styles.css", "r", encoding="utf-8") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
/* ── Podium cards ── */
.podium-wrap { display:flex; gap:0.5rem; align-items:flex-end; margin-bottom:0.6rem; flex-wrap:wrap; }
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
.podium-medal { font-size:1.6rem; line-height:1; margin-bottom:0.3rem; }
.podium-pos   { font-size:0.6rem; font-weight:800; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin-bottom:0.15rem; }
.podium-user  { font-size:0.82rem; font-weight:700; color:var(--text); margin-bottom:0.2rem; line-height:1.2; }
.podium-score { font-size:1.15rem; font-weight:800; color:var(--primary); }
.podium-sub   { font-size:0.65rem; color:var(--muted); }

/* ── Gauge bar ── */
.gauge-bar-wrap { margin:0.3rem 0 0.1rem; }
.gauge-bar-bg   { background:var(--border); border-radius:999px; height:7px; overflow:hidden; }
.gauge-bar-fill { height:100%; border-radius:999px; }

/* ── Category rank table ── */
.cat-row { display:flex; align-items:center; gap:0.5rem; padding:0.35rem 0; border-bottom:1px solid var(--border); }
.cat-row:last-child { border-bottom:none; }
.cat-rank  { width:22px; font-size:0.72rem; font-weight:800; color:var(--muted); flex-shrink:0; }
.cat-name  { flex:1; font-size:0.82rem; font-weight:600; color:var(--text); }
.cat-bar   { width:80px; }
.cat-score { font-size:0.8rem; font-weight:700; color:var(--primary); width:40px; text-align:right; flex-shrink:0; }

/* ── Global KPI row ── */
.gkpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:0.5rem; margin-bottom:0.5rem; }
.gkpi-card {
    background:var(--surface-soft); border:1px solid var(--border);
    border-radius:14px; padding:0.8rem 0.9rem;
    box-shadow:var(--shadow-soft); text-align:center;
}
.gkpi-icon  { font-size:1.4rem; margin-bottom:0.2rem; }
.gkpi-val   { font-size:1.3rem; font-weight:800; color:var(--text); line-height:1; }
.gkpi-lbl   { font-size:0.68rem; color:var(--muted); margin-top:0.15rem; }

/* ── Status pill ── */
.status-pill {
    display:inline-block; font-size:0.65rem; font-weight:700;
    padding:0.15rem 0.5rem; border-radius:999px;
}
.sp-green { background:#dcfce7; color:#15803d; }
.sp-amber { background:#fef3c7; color:#b45309; }
.sp-red   { background:#fee2e2; color:#991b1b; }

/* ── Year chip row ── */
.year-chips { display:flex; flex-wrap:wrap; gap:0.4rem; margin-bottom:0.6rem; }

@media(max-width:768px) {
    .gkpi-grid { grid-template-columns:repeat(2,1fr); }
    .podium-wrap { flex-direction:column; align-items:stretch; }
}
</style>
""", unsafe_allow_html=True)

render_sidebar()

# ── Hero ─────────────────────────────────────────────────────────────────────
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
        Comparativa global de reseñas · Top categorías · Posición relativa en tiempo real
    </div>
</div>
""", unsafe_allow_html=True)

# ── Datos base ────────────────────────────────────────────────────────────────
product_options  = get_product_options()
catalog          = get_product_catalog()
full_db          = get_corporate_audit_db()
global_ranking   = get_global_ranking()
saved_reviews_df = get_audited_reviews_operational_table()

if not product_options:
    st.warning("No hay productos disponibles.")
    st.stop()

# Asegurar columna CreatedAt y año disponible
if "CreatedAt" in full_db.columns:
    full_db["CreatedAt"] = pd.to_datetime(full_db["CreatedAt"], errors="coerce")
    full_db["Año"] = full_db["CreatedAt"].dt.year.fillna(0).astype(int)
else:
    full_db["Año"] = 0

años_disponibles = sorted([y for y in full_db["Año"].unique() if y > 2000], reverse=True)

# ── Filtros globales ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Filtros</div>', unsafe_allow_html=True)
fc1, fc2, fc3, fc4 = st.columns([2, 1.4, 1.2, 1], gap="medium")

with fc1:
    selected_product = st.selectbox("Producto", options=product_options)
with fc2:
    selected_status = st.selectbox(
        "Estado",
        options=["Todos", "APROBADA (Publicada)", "RECHAZADA (Baja Calidad)", "RECHAZADA (Punto Ciego)"]
    )
with fc3:
    year_options = ["Todos los años"] + [str(y) for y in años_disponibles]
    selected_year = st.selectbox("Año", options=year_options)
with fc4:
    min_stars = st.selectbox("Estrellas mín.", options=["Todas", "⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"])

detail = get_product_detail(selected_product)
st.info(f"**{detail['ProductName']}** · `{detail['ProductId']}` · Categoría: **{detail['Categoria_Real']}**")

# ── Aplicar filtros ───────────────────────────────────────────────────────────
def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if selected_status != "Todos" and "Estado" in out.columns:
        out = out[out["Estado"] == selected_status]
    if selected_year != "Todos los años" and "Año" in out.columns:
        out = out[out["Año"] == int(selected_year)]
    if min_stars != "Todas" and "Stars" in out.columns:
        min_val = min_stars.count("⭐")
        out = out[out["Stars"] >= min_val]
    return out

ranking_df   = get_local_product_ranking(selected_product)
filtered_db  = _apply_filters(full_db)
filtered_local = _apply_filters(ranking_df)

# ── KPIs GLOBALES ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Indicadores globales</div>', unsafe_allow_html=True)

total_reviews   = len(filtered_db)
approved        = int((filtered_db["Estado"] == "APROBADA (Publicada)").sum()) if "Estado" in filtered_db.columns else 0
avg_helpfulness = float(filtered_db["Helpfulness"].mean()) if "Helpfulness" in filtered_db.columns and total_reviews > 0 else 0.0
total_products  = int(filtered_db["ProductId"].astype(str).nunique()) if "ProductId" in filtered_db.columns else 0
approval_rate   = approved / total_reviews if total_reviews > 0 else 0.0
rejected        = total_reviews - approved

st.markdown(f"""
<div class="gkpi-grid">
    <div class="gkpi-card">
        <div class="gkpi-icon">📦</div>
        <div class="gkpi-val">{format_compact_number(total_reviews)}</div>
        <div class="gkpi-lbl">Reseñas en base</div>
    </div>
    <div class="gkpi-card">
        <div class="gkpi-icon">✅</div>
        <div class="gkpi-val">{format_compact_number(approved)}</div>
        <div class="gkpi-lbl">Aprobadas · {format_percentage(approval_rate)}</div>
    </div>
    <div class="gkpi-card">
        <div class="gkpi-icon">❌</div>
        <div class="gkpi-val">{format_compact_number(rejected)}</div>
        <div class="gkpi-lbl">Rechazadas</div>
    </div>
    <div class="gkpi-card">
        <div class="gkpi-icon">📊</div>
        <div class="gkpi-val">{format_percentage(avg_helpfulness)}</div>
        <div class="gkpi-lbl">Utilidad media global</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Gráfica estados + evolución mensual ──────────────────────────────────────
vc1, vc2 = st.columns(2, gap="medium")

with vc1:
    st.markdown('<div class="section-label">Distribución por estado</div>', unsafe_allow_html=True)
    if "Estado" in filtered_db.columns and not filtered_db.empty:
        estado_counts = filtered_db["Estado"].value_counts().reset_index()
        estado_counts.columns = ["Estado", "Cantidad"]
        color_map = {
            "APROBADA (Publicada)":      "#15803d",
            "RECHAZADA (Baja Calidad)":  "#b45309",
            "RECHAZADA (Punto Ciego)":   "#991b1b",
        }
        fig_estado = px.pie(
            estado_counts, values="Cantidad", names="Estado",
            color="Estado", color_discrete_map=color_map,
            hole=0.55, template="plotly_white",
        )
        fig_estado.update_traces(textposition="outside", textinfo="percent+label",
                                 textfont_size=10, pull=[0.03]*len(estado_counts))
        fig_estado.update_layout(
            height=240, margin=dict(l=10,r=10,t=20,b=10),
            showlegend=False, title_font_size=11,
        )
        st.plotly_chart(fig_estado, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sin datos para graficar.")

with vc2:
    st.markdown('<div class="section-label">Evolución de reseñas por año</div>', unsafe_allow_html=True)
    if "Año" in filtered_db.columns and "CreatedAt" in filtered_db.columns and not filtered_db.empty:
        monthly = (
            filtered_db.dropna(subset=["CreatedAt"])
            .assign(Mes=lambda d: d["CreatedAt"].dt.to_period("M").astype(str))
            .groupby("Mes")
            .agg(Total=("Helpfulness","count"), Util_Media=("Helpfulness","mean"))
            .reset_index()
            .tail(24)  # últimos 24 meses
        )
        if not monthly.empty:
            fig_evol = go.Figure()
            fig_evol.add_trace(go.Bar(
                x=monthly["Mes"], y=monthly["Total"],
                name="Reseñas", marker_color="#dbe7ff",
                yaxis="y", opacity=0.85,
            ))
            fig_evol.add_trace(go.Scatter(
                x=monthly["Mes"], y=monthly["Util_Media"],
                name="Utilidad media", line=dict(color="#1746a2", width=2.5),
                yaxis="y2", mode="lines+markers", marker_size=4,
            ))
            fig_evol.update_layout(
                height=240, margin=dict(l=10,r=10,t=20,b=10),
                yaxis=dict(title="Reseñas", showgrid=True, gridcolor="#f0f4f8"),
                yaxis2=dict(title="Utilidad", overlaying="y", side="right",
                            tickformat=".0%", range=[0,1]),
                xaxis=dict(tickangle=-45, tickfont_size=8),
                legend=dict(orientation="h", y=1.1, font_size=9),
                template="plotly_white", plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_evol, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sin datos temporales.")
    else:
        st.info("Sin columna de fecha disponible.")

# ── Top 5 Categorías ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Top 5 categorías por utilidad media</div>', unsafe_allow_html=True)

cat_col_name = None
if "Categoria_Real" in filtered_db.columns:
    cat_col_name = "Categoria_Real"
elif catalog is not None and not catalog.empty and "Categoria_Real" in catalog.columns and "ProductId" in catalog.columns:
    # Enriquecer filtered_db con categorías desde el catálogo
    cat_map = catalog.set_index("ProductId")["Categoria_Real"].to_dict()
    filtered_db["Categoria_Real"] = filtered_db["ProductId"].astype(str).map(cat_map).fillna("Sin categoría")
    cat_col_name = "Categoria_Real"

tcc1, tcc2 = st.columns([1, 1.4], gap="medium")

if cat_col_name and not filtered_db.empty:
    cat_stats = (
        filtered_db.groupby(cat_col_name)
        .agg(
            n_resenas=(cat_col_name, "count"),
            util_media=("Helpfulness", "mean"),
            aprobadas=("Estado", lambda x: (x == "APROBADA (Publicada)").sum()),
        )
        .reset_index()
        .sort_values("util_media", ascending=False)
        .head(5)
        .reset_index(drop=True)
    )
    cat_stats["util_pct"] = cat_stats["util_media"] * 100

    with tcc1:
        medals = ["🥇","🥈","🥉","4️⃣","5️⃣"]
        colors = ["#f59e0b","#94a3b8","#b45309","#64748b","#64748b"]
        cat_html = '<div style="background:var(--surface-soft);border:1px solid var(--border);border-radius:14px;padding:0.7rem 0.9rem;">'
        for i, row in cat_stats.iterrows():
            bar_w = int(row["util_pct"])
            bar_color = colors[i] if i < len(colors) else "#64748b"
            cat_html += f"""
            <div class="cat-row">
                <div class="cat-rank">{medals[i]}</div>
                <div class="cat-name">{row[cat_col_name]}</div>
                <div class="cat-bar">
                    <div class="gauge-bar-bg">
                        <div class="gauge-bar-fill" style="width:{bar_w}%;background:{bar_color}"></div>
                    </div>
                </div>
                <div class="cat-score">{row['util_pct']:.1f}%</div>
            </div>"""
        cat_html += "</div>"
        st.markdown(cat_html, unsafe_allow_html=True)

    with tcc2:
        fig_cat = px.bar(
            cat_stats.sort_values("util_media", ascending=True),
            x="util_media", y=cat_col_name, orientation="h",
            color="util_media",
            color_continuous_scale=["#fef3c7","#f59e0b","#15803d"],
            labels={"util_media": "Utilidad media", cat_col_name: "Categoría"},
            template="plotly_white",
            text=cat_stats.sort_values("util_media", ascending=True)["n_resenas"].apply(lambda x: f"{int(x)} reseñas"),
        )
        fig_cat.update_coloraxes(showscale=False)
        fig_cat.update_traces(textposition="inside", textfont_size=9)
        fig_cat.update_xaxes(tickformat=".0%", range=[0,1])
        fig_cat.update_layout(height=220, margin=dict(l=10,r=10,t=15,b=10))
        st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("No hay datos de categorías disponibles para el filtro actual.")

# ── KPIs del producto seleccionado ───────────────────────────────────────────
st.markdown('<div class="section-label">Indicadores del producto seleccionado</div>', unsafe_allow_html=True)

top_score    = float(filtered_local["Helpfulness"].max())  if not filtered_local.empty else 0.0
avg_score    = float(filtered_local["Helpfulness"].mean()) if not filtered_local.empty else 0.0
review_count = len(filtered_local)
approved_prd = int((filtered_local["Estado"] == "APROBADA (Publicada)").sum()) if "Estado" in filtered_local.columns else 0
rejected_prd = review_count - approved_prd
top_user     = str(filtered_local.iloc[0]["User"]) if not filtered_local.empty else "Sin datos"

pc1, pc2, pc3, pc4, pc5 = st.columns(5, gap="small")
with pc1:
    render_metric_card("Reseñas", format_compact_number(review_count), "Con los filtros activos")
with pc2:
    render_metric_card("Utilidad máx.", format_percentage(top_score), "Reseña mejor puntuada")
with pc3:
    render_metric_card("Utilidad media", format_percentage(avg_score), "Promedio del producto")
with pc4:
    render_metric_card("Aprobadas", str(approved_prd), "Estado APROBADA")
with pc5:
    render_metric_card("Rechazadas", str(rejected_prd), "Estado RECHAZADA")

# ── Distribución de estrellas del producto ───────────────────────────────────
pd1, pd2 = st.columns(2, gap="medium")

with pd1:
    st.markdown('<div class="section-label">Estrellas del producto</div>', unsafe_allow_html=True)
    if not filtered_local.empty and "Stars" in filtered_local.columns:
        stars_cnt = filtered_local["Stars"].value_counts().sort_index().reset_index()
        stars_cnt.columns = ["Estrellas", "Cantidad"]
        stars_cnt["Label"] = stars_cnt["Estrellas"].apply(lambda x: "⭐"*int(x))
        fig_stars = px.bar(
            stars_cnt, x="Label", y="Cantidad",
            color="Estrellas",
            color_continuous_scale=["#fee2e2","#fef3c7","#fef9c3","#dcfce7","#15803d"],
            template="plotly_white",
            labels={"Label":"", "Cantidad":"Reseñas"},
        )
        fig_stars.update_coloraxes(showscale=False)
        fig_stars.update_layout(height=200, margin=dict(l=10,r=10,t=15,b=10))
        st.plotly_chart(fig_stars, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sin datos de estrellas.")

with pd2:
    st.markdown('<div class="section-label">Utilidad por estrella</div>', unsafe_allow_html=True)
    if not filtered_local.empty and "Stars" in filtered_local.columns and "Helpfulness" in filtered_local.columns:
        util_by_star = (
            filtered_local.groupby("Stars")["Helpfulness"].mean().reset_index()
        )
        util_by_star.columns = ["Estrellas","Utilidad_media"]
        util_by_star["Label"] = util_by_star["Estrellas"].apply(lambda x: f"{'⭐'*int(x)}")
        fig_us = px.line(
            util_by_star, x="Label", y="Utilidad_media",
            markers=True, template="plotly_white",
            labels={"Label":"","Utilidad_media":"Utilidad media"},
            color_discrete_sequence=["#1746a2"],
        )
        fig_us.update_yaxes(tickformat=".0%", range=[0,1])
        fig_us.update_traces(line_width=2.5, marker_size=7)
        fig_us.update_layout(height=200, margin=dict(l=10,r=10,t=15,b=10))
        st.plotly_chart(fig_us, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sin datos suficientes.")

# ── Pódium Top 3 ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Pódium — Top 3 del producto</div>', unsafe_allow_html=True)

podium_colors  = ["podium-1","podium-2","podium-3"]
podium_medals  = ["🥇","🥈","🥉"]
podium_labels  = ["1er lugar","2do lugar","3er lugar"]
top3 = filtered_local.head(3) if not filtered_local.empty else pd.DataFrame()

if not top3.empty:
    cols_podium = st.columns(len(top3), gap="medium")
    for i, (_, row) in enumerate(top3.iterrows()):
        pclass  = podium_colors[i] if i < 3 else "podium-card"
        medal   = podium_medals[i] if i < 3 else f"{i+1}."
        label   = podium_labels[i] if i < 3 else f"Puesto {i+1}"
        score   = float(row.get("Helpfulness", 0))
        user    = str(row.get("User","—"))[:22]
        stars_n = int(row.get("Stars",0))
        estado  = str(row.get("Estado","—"))
        stars_str = "⭐"*stars_n
        bar_w = int(score * 100)
        sp_cls = "sp-green" if "APROBADA" in estado else ("sp-red" if "Ciego" in estado else "sp-amber")
        sp_lbl = "Publicada" if "APROBADA" in estado else "Rechazada"
        with cols_podium[i]:
            st.markdown(f"""
            <div class="podium-card {pclass}">
                <div class="podium-medal">{medal}</div>
                <div class="podium-pos">{label}</div>
                <div class="podium-user">{user}</div>
                <div class="podium-score">{format_percentage(score)}</div>
                <div class="podium-sub">{stars_str}</div>
                <div class="gauge-bar-wrap">
                    <div class="gauge-bar-bg">
                        <div class="gauge-bar-fill" style="width:{bar_w}%;background:{'#15803d' if score>=.7 else '#b45309'}"></div>
                    </div>
                </div>
                <div style="margin-top:0.3rem"><span class="status-pill {sp_cls}">{sp_lbl}</span></div>
            </div>
            """, unsafe_allow_html=True)

    # Resto del top 5 como tabla compacta
    if len(filtered_local) > 3:
        st.markdown('<div class="section-label">Posiciones 4–10</div>', unsafe_allow_html=True)
        rest = filtered_local.iloc[3:10].copy()
        rest["Puesto"] = range(4, 4 + len(rest))
        rest["Utilidad"] = rest["Helpfulness"].apply(format_percentage)
        rest["Estrellas"] = rest["Stars"].apply(lambda x: "⭐"*int(x) if pd.notna(x) else "—")
        st.dataframe(
            rest[["Puesto","User","Estrellas","Utilidad","Estado"]].rename(columns={"User":"Usuario"}),
            use_container_width=True, hide_index=True,
        )
else:
    st.info("No hay reseñas para los filtros seleccionados.")

# ── Tu reseña en contexto ─────────────────────────────────────────────────────
st.markdown('<div class="section-label">Tu reseña en contexto</div>', unsafe_allow_html=True)

latest_review_id = st.session_state.get("latest_review_id")
position_summary = get_position_summary(selected_product, latest_review_id)
review_window_df = get_review_context_window(selected_product, latest_review_id, window_size=2)

p1, p2, p3 = st.columns(3, gap="medium")
with p1:
    render_metric_card(
        "Posición local",
        f"{position_summary['local_rank']} / {position_summary['product_count']}" if position_summary["local_rank"] else "Sin reseña evaluada",
        "Lugar dentro del producto"
    )
with p2:
    render_metric_card(
        "Posición global",
        f"{position_summary['global_rank']} / {position_summary['global_count']}" if position_summary["global_rank"] else "Sin reseña evaluada",
        "Lugar en toda la base"
    )
with p3:
    render_metric_card(
        "Total del producto",
        format_compact_number(position_summary["product_count"]),
        "Volumen histórico"
    )

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

# ── Top 20 global ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-label">Top 20 global por utilidad</div>', unsafe_allow_html=True)

global_filtered = _apply_filters(global_ranking) if not global_ranking.empty else global_ranking

if not global_filtered.empty:
    display_cols = [c for c in ["Puesto Global","ProductId","User","Stars","Helpfulness","Estado"] if c in global_filtered.columns]
    top20 = global_filtered.head(20).copy()
    if "Helpfulness" in top20.columns:
        top20["Helpfulness"] = top20["Helpfulness"].apply(lambda x: format_percentage(float(x)))
    st.dataframe(top20[display_cols], use_container_width=True, hide_index=True)

# ── Reseñas guardadas ─────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Reseñas guardadas en archivo</div>', unsafe_allow_html=True)
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
    st.download_button(
        "⬇ Descargar CSV filtrado",
        data=filtered_saved.to_csv(index=False).encode("utf-8-sig"),
        file_name="resenas_filtradas.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("No hay reseñas guardadas para los filtros seleccionados.")