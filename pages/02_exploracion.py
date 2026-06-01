try:
    import streamlit as _st
    if not _st.session_state.get("app_initialized"):
        _st.switch_page("main.py")
except Exception:
    pass

import pandas as pd
import plotly.express as px
import streamlit as st
from shared_sidebar import render_sidebar
from plots.eda_charts import (
    build_correlation_heatmap, build_length_vs_helpfulness,
    build_review_length_distribution, build_stars_distribution,
    build_stars_vs_helpfulness, build_sentiment_vs_score,
    build_incoherence_distribution, build_target_balance,
)
from services.catalog_service import map_product_metadata
from services.data_loader import load_processed_reviews, load_reviews_with_category
from services.supabase_service import load_reviews_from_supabase
from services.feature_service import add_basic_text_features
from services.preprocessing_service import get_corporate_audit_db
from utils.formatters import format_compact_number, format_percentage

with open("styles/styles.css", "r", encoding="utf-8") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
render_sidebar()

st.markdown("""
<div style="background:linear-gradient(135deg,#16213b 0%,#1746a2 60%,#0f4c5c 100%);
    border-radius:16px;padding:1.4rem 2rem;margin-bottom:1.4rem;color:#fff">
    <div style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                color:rgba(255,255,255,0.55);text-transform:uppercase;margin-bottom:0.35rem">
        Seminario Predictivo 2026 · Caso 06
    </div>
    <div style="font-size:clamp(1.4rem,3vw,1.9rem);font-weight:800;
                letter-spacing:-0.02em;line-height:1.2;margin-bottom:0.3rem">
        Exploración de Datos
    </div>
    <div style="font-size:0.82rem;color:rgba(255,255,255,0.65)">
        Análisis exploratorio interactivo · Filtra por estrellas, categoría, longitud y utilidad
    </div>
</div>
""", unsafe_allow_html=True)

# ── Carga ─────────────────────────────────────────────────────────────────────
reviews_cat = add_basic_text_features(load_reviews_with_category())
reviews_raw = add_basic_text_features(load_processed_reviews())
fallback    = add_basic_text_features(get_corporate_audit_db().rename(columns={"Stars": "Score"}))

source = reviews_cat if not reviews_cat.empty else (reviews_raw if not reviews_raw.empty else fallback)
source = map_product_metadata(source)

if "Helpfulness" not in source.columns:
    if "HelpfulnessNumerator" in source.columns and "HelpfulnessDenominator" in source.columns:
        source["Helpfulness"] = (source["HelpfulnessNumerator"] / source["HelpfulnessDenominator"].replace(0, pd.NA)).fillna(0)
    elif "y_util" in source.columns:
        source["Helpfulness"] = source["y_util"].astype(float)

score_col       = "Score" if "Score" in source.columns else ("Stars" if "Stars" in source.columns else None)
helpfulness_col = "Helpfulness" if "Helpfulness" in source.columns else None

if "categoria_alimento" in source.columns:
    category_col, category_label = "categoria_alimento", "Categoría de alimento"
elif "Categoria_Real" in source.columns:
    category_col, category_label = "Categoria_Real", "Categoría"
else:
    category_col, category_label = None, "Categoría"

# Año
if "Time" in source.columns:
    source["Año"] = pd.to_datetime(source["Time"], unit="s", errors="coerce").dt.year.fillna(0).astype(int)
elif "CreatedAt" in source.columns:
    source["Año"] = pd.to_datetime(source["CreatedAt"], errors="coerce").dt.year.fillna(0).astype(int)
else:
    source["Año"] = 0

# ── Fusionar reseñas de Supabase al source ───────────────────────────────────
try:
    _sb_df = load_reviews_from_supabase()
    if not _sb_df.empty:
        _sb_norm = pd.DataFrame({
            "Score":        pd.to_numeric(_sb_df.get("stars", 5), errors="coerce").fillna(5).astype(int),
            "Helpfulness":  pd.to_numeric(_sb_df.get("helpfulness", 0), errors="coerce").fillna(0),
            "y_util":       (_sb_df.get("helpfulness", 0) >= 0.70).astype(int),
            "review_len":   pd.to_numeric(_sb_df.get("review_len", 50), errors="coerce").fillna(50).astype(int),
            "sentiment_score": pd.to_numeric(_sb_df.get("sentiment_score", 0), errors="coerce").fillna(0),
            "incoherente":  _sb_df.get("incoherente", False).astype(int) if "incoherente" in _sb_df.columns else 0,
            "ProductId":    _sb_df.get("product_id", "").astype(str),
            "Text":         _sb_df.get("texto", ""),
            "Helpfulness":  pd.to_numeric(_sb_df.get("helpfulness", 0), errors="coerce").fillna(0),
            "Año":          pd.to_datetime(_sb_df.get("created_at"), errors="coerce").dt.year.fillna(2026).astype(int),
            "categoria_alimento": _sb_df.get("categoria", "Alimentos generales") if "categoria" in _sb_df.columns else "Alimentos generales",
        })
        # Asegurar que tenga las mismas columnas relevantes
        if category_col and category_col not in _sb_norm.columns:
            _sb_norm[category_col] = _sb_norm.get("categoria_alimento", "Alimentos generales")
        source = pd.concat([source, _sb_norm], ignore_index=True)
except Exception:
    pass

años_disponibles = sorted([y for y in source["Año"].unique() if y > 2000])

# ══════════════════════════════════════════════════════════════════════════════
# FILTROS — multiselect
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Filtros</div>', unsafe_allow_html=True)

fc1, fc2, fc3, fc4, fc5 = st.columns([1, 1.4, 1, 1, 1], gap="medium")

with fc1:
    star_options = [str(x) for x in sorted(source[score_col].dropna().astype(int).unique())] if score_col else []
    sel_stars = st.multiselect("Estrellas", options=star_options, placeholder="Todas")

with fc2:
    cat_options = sorted(source[category_col].dropna().astype(str).unique().tolist()) if category_col else []
    sel_cats = st.multiselect(category_label, options=cat_options, placeholder="Todas")

with fc3:
    year_options = [str(y) for y in años_disponibles]
    sel_years = st.multiselect("Año", options=year_options, placeholder="Todos")

with fc4:
    min_l = int(source["review_len"].min()) if "review_len" in source.columns else 0
    max_l = int(source["review_len"].max()) if "review_len" in source.columns else 500
    max_l = max(max_l, min_l + 1)
    sel_len = st.slider("Longitud (palabras)", min_value=min_l, max_value=max_l, value=(min_l, max_l))

with fc5:
    sel_util = st.selectbox("Utilidad", options=["Todas", "Útiles (≥ 0.70)", "No útiles (< 0.70)"])

# ── Aplicar filtros ───────────────────────────────────────────────────────────
df = source.copy()
if sel_stars and score_col:
    df = df[df[score_col].astype(str).isin(sel_stars)]
if sel_cats and category_col:
    df = df[df[category_col].isin(sel_cats)]
if sel_years:
    df = df[df["Año"].astype(str).isin(sel_years)]
if "review_len" in df.columns:
    df = df[df["review_len"].between(sel_len[0], sel_len[1])]
if helpfulness_col and sel_util != "Todas":
    df = df[df[helpfulness_col] >= 0.70] if "Útiles" in sel_util else df[df[helpfulness_col] < 0.70]

# Badge de filtros activos
filtros_activos = []
if sel_stars:    filtros_activos.append(f"Estrellas: {', '.join(sel_stars)}")
if sel_cats:     filtros_activos.append(f"Categorías: {len(sel_cats)} seleccionadas")
if sel_years:    filtros_activos.append(f"Años: {', '.join(sel_years)}")
if sel_util != "Todas": filtros_activos.append(sel_util)

if filtros_activos:
    badges = " &nbsp;·&nbsp; ".join(f'<span style="background:#dbeafe;color:#1d4ed8;font-size:0.72rem;font-weight:600;padding:0.2rem 0.6rem;border-radius:999px">{f}</span>' for f in filtros_activos)
    st.markdown(f'<div style="margin-bottom:0.6rem">{badges}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# INDICADORES DEL CORTE
# ══════════════════════════════════════════════════════════════════════════════
try:
    _sb_extra = len(load_reviews_from_supabase())
except Exception:
    _sb_extra = 0

n_total   = len(df) + _sb_extra
n_base    = len(df)
products  = int(df["ProductId"].astype(str).nunique()) if "ProductId" in df.columns else 0
ratio     = float(df[helpfulness_col].ge(0.70).mean()) if helpfulness_col and n_base > 0 else 0.0
avg_len   = int(df["review_len"].fillna(0).mean()) if "review_len" in df.columns and n_base > 0 else 0
pct_filtro = round(n_base / len(source) * 100, 1) if len(source) > 0 else 100.0

st.markdown('<div class="section-label">Indicadores del corte actual</div>', unsafe_allow_html=True)

i1, i2, i3, i4 = st.columns(4, gap="medium")
for col, valor, label, sublabel, color in [
    (i1, format_compact_number(n_total),    "Reseñas totales",   f"{pct_filtro}% del dataset",       "#1d4ed8"),
    (i2, format_compact_number(products),   "Productos únicos",  "IDs distintos en el corte",         "#7c3aed"),
    (i3, format_percentage(ratio),          "Ratio de útiles",   "Reseñas con Helpfulness ≥ 0.70",   "#15803d"),
    (i4, f"{avg_len} palabras",             "Longitud media",    "Promedio del corte filtrado",       "#b45309"),
]:
    with col:
        st.markdown(f"""
        <div style="background:#fff;border:1px solid #e2e8f0;border-top:3px solid {color};
                    border-radius:12px;padding:0.85rem 0.8rem;text-align:center">
            <div style="font-size:1.5rem;font-weight:900;color:{color};line-height:1.1">{valor}</div>
            <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;
                        color:#64748b;margin:0.25rem 0;letter-spacing:.05em">{label}</div>
            <div style="font-size:0.65rem;color:#94a3b8">{sublabel}</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DISTRIBUCIONES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Distribuciones</div>', unsafe_allow_html=True)

d1, d2 = st.columns(2, gap="large")
with d1:
    st.caption("**Calificaciones** — Concentración en 4-5 estrellas genera desbalance.")
    st.plotly_chart(build_stars_distribution(df), use_container_width=True)
with d2:
    st.caption("**Longitud** — Las reseñas largas son minoría pero suelen ser más útiles.")
    st.plotly_chart(build_review_length_distribution(df), use_container_width=True)

d3, d4 = st.columns(2, gap="large")
with d3:
    st.caption("**Balance de clases** — Desbalance que justifica F1 sobre Accuracy.")
    st.plotly_chart(build_target_balance(df), use_container_width=True)
with d4:
    st.caption("**Coherencia texto-estrellas** — El 18% presenta incoherencia.")
    st.plotly_chart(build_incoherence_distribution(df), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# RELACIONES CON LA UTILIDAD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Relaciones con la utilidad</div>', unsafe_allow_html=True)

r1, r2 = st.columns(2, gap="large")
with r1:
    st.caption("**Estrellas vs. utilidad** — Las 4-5 estrellas dominan pero no garantizan utilidad.")
    st.plotly_chart(build_stars_vs_helpfulness(df), use_container_width=True)
with r2:
    st.caption("**Longitud vs. utilidad** — Relación más fuerte del dataset.")
    st.plotly_chart(build_length_vs_helpfulness(df), use_container_width=True)

st.caption("**Sentimiento por estrellas** — El sentimiento sube con las estrellas pero con alta varianza.")
st.plotly_chart(build_sentiment_vs_score(df), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# DISTRIBUCIÓN POR CATEGORÍA
# ══════════════════════════════════════════════════════════════════════════════
if category_col and not df.empty:
    st.markdown('<div class="section-label">Distribución por categoría de alimento</div>', unsafe_allow_html=True)

    cat_stats = (
        df.groupby(category_col)
        .agg(
            n_resenas=(category_col, "count"),
            ratio_util=(helpfulness_col, lambda x: (x >= 0.70).mean()) if helpfulness_col else (category_col, "count"),
            avg_len=("review_len", "mean") if "review_len" in df.columns else (category_col, "count"),
        )
        .reset_index()
        .sort_values("n_resenas", ascending=False)
    )

    fig_cat = px.bar(
        cat_stats.sort_values("n_resenas", ascending=True),
        x="n_resenas", y=category_col, orientation="h",
        title="Reseñas por categoría de alimento",
        labels={"n_resenas": "N° de reseñas", category_col: "Categoría"},
        color="ratio_util",
        color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
        color_continuous_midpoint=0.5,
        template="plotly_white",
    )
    fig_cat.update_coloraxes(colorbar_title="Ratio útiles")
    fig_cat.update_layout(height=max(350, len(cat_stats) * 28), margin=dict(l=10, r=20, t=40, b=10))
    st.plotly_chart(fig_cat, use_container_width=True)

    cat_display = cat_stats.copy()
    cat_display["n_resenas"]  = cat_display["n_resenas"].apply(format_compact_number)
    cat_display["ratio_util"] = cat_display["ratio_util"].apply(format_percentage)
    cat_display["avg_len"]    = cat_display["avg_len"].apply(lambda x: f"{int(x)} palabras")
    cat_display.columns       = ["Categoría", "Reseñas", "% Útiles", "Longitud media"]
    st.dataframe(cat_display, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# CORRELACIÓN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Correlación entre variables</div>', unsafe_allow_html=True)
st.plotly_chart(build_correlation_heatmap(df), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# DESCARGA DE DATOS FILTRADOS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Descargar datos del corte actual</div>', unsafe_allow_html=True)

if df.empty:
    st.info("No hay datos con los filtros actuales para descargar.")
else:
    # Columnas legibles para exportar
    export_cols = [c for c in [
        score_col, "review_len", "sentiment_score", "incoherente",
        "y_util", helpfulness_col, "Text", "ProductId",
        category_col, "Año",
    ] if c and c in df.columns]
    df_export = df[export_cols].copy()

    # Renombrar columnas a nombres legibles
    rename_map = {
        score_col:        "Estrellas",
        "review_len":     "Longitud (palabras)",
        "sentiment_score":"Sentimiento VADER",
        "incoherente":    "Incoherente",
        "y_util":         "Es útil (1/0)",
        helpfulness_col:  "Tasa de utilidad",
        "Text":           "Texto de la reseña",
        "ProductId":      "ID Producto",
        category_col:     "Categoría",
        "Año":            "Año",
    }
    df_export = df_export.rename(columns={k: v for k, v in rename_map.items() if k and k in df_export.columns})

    n_filas = len(df_export)
    st.markdown(
        f'<div class="highlight-card"><div class="highlight-body">'
        f'El corte actual tiene <strong>{format_compact_number(n_filas)} reseñas</strong>. '
        f'Elige el formato para descargarlas.</div></div>',
        unsafe_allow_html=True,
    )

    import io, re

    # Limpieza de caracteres ilegales para Excel y PDF (control chars, etc.)
    def _clean_text(val):
        if not isinstance(val, str):
            return val
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", val).strip()

    df_clean = df_export.copy()
    for col in df_clean.select_dtypes(include="object").columns:
        df_clean[col] = df_clean[col].map(_clean_text)

    dl1, dl2, dl3, dl4 = st.columns(4, gap="medium")

    # ── CSV ──────────────────────────────────────────────────────────────────
    with dl1:
        csv_bytes = df_clean.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇ CSV",
            data=csv_bytes,
            file_name="resenas_filtradas.csv",
            mime="text/csv",
            use_container_width=True,
            help="Compatible con Excel, Google Sheets y cualquier herramienta de análisis.",
        )
        st.caption("Excel · Google Sheets")

    # ── JSON ─────────────────────────────────────────────────────────────────
    with dl2:
        json_bytes = df_clean.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            label="⬇ JSON",
            data=json_bytes,
            file_name="resenas_filtradas.json",
            mime="application/json",
            use_container_width=True,
            help="Ideal para consumir desde una API o sistema externo.",
        )
        st.caption("APIs · integraciones")

    # ── Excel ────────────────────────────────────────────────────────────────
    with dl3:
        try:
            buffer_xl = io.BytesIO()
            with pd.ExcelWriter(buffer_xl, engine="openpyxl") as writer:
                df_clean.to_excel(writer, index=False, sheet_name="Resenas filtradas")
            st.download_button(
                label="⬇ Excel",
                data=buffer_xl.getvalue(),
                file_name="resenas_filtradas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                help="Archivo .xlsx con hoja nombrada y columnas formateadas.",
            )
            st.caption("Hoja de cálculo .xlsx")
        except Exception:
            st.warning("Excel no disponible — usa CSV.")

    # ── PDF ──────────────────────────────────────────────────────────────────
    with dl4:
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm

            buffer_pdf = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer_pdf,
                pagesize=landscape(A4),
                rightMargin=1*cm, leftMargin=1*cm,
                topMargin=1.5*cm, bottomMargin=1*cm,
            )
            styles = getSampleStyleSheet()
            elements = []

            # Título
            elements.append(Paragraph(
                f"Reseñas Amazon Fine Food — Corte filtrado ({format_compact_number(n_filas)} registros)",
                styles["Heading2"]
            ))
            elements.append(Spacer(1, 0.4*cm))

            # Limitar a 500 filas para no generar un PDF enorme
            df_pdf = df_clean.head(500)
            cols_pdf = list(df_pdf.columns)

            # Truncar texto largo en columnas de texto
            def _trunc(val, n=60):
                s = str(val) if not isinstance(val, float) else f"{val:.3f}"
                return s[:n] + "…" if len(s) > n else s

            data = [cols_pdf] + [[_trunc(v) for v in row] for row in df_pdf.itertuples(index=False)]

            col_width = (landscape(A4)[0] - 2*cm) / len(cols_pdf)
            table = Table(data, colWidths=[col_width] * len(cols_pdf), repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#1746A2")),
                ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
                ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
                ("FONTSIZE",    (0, 0), (-1, 0),  7),
                ("FONTSIZE",    (0, 1), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EFF6FF")]),
                ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
                ("VALIGN",      (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",  (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING",(0,0), (-1, -1), 3),
            ]))
            elements.append(table)

            if n_filas > 500:
                elements.append(Spacer(1, 0.3*cm))
                elements.append(Paragraph(
                    f"* PDF limitado a 500 filas. Descarga CSV o Excel para el dataset completo ({format_compact_number(n_filas)} reseñas).",
                    styles["Italic"]
                ))

            doc.build(elements)

            st.download_button(
                label="⬇ PDF",
                data=buffer_pdf.getvalue(),
                file_name="resenas_filtradas.pdf",
                mime="application/pdf",
                use_container_width=True,
                help="Tabla en PDF. Máximo 500 filas para un archivo manejable.",
            )
            st.caption("Vista imprimible · máx. 500 filas")
        except ImportError:
            st.info("PDF no disponible — instala reportlab.")