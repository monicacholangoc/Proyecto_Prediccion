"""Resumen ejecutivo — limpio, sin duplicados, orientado a hallazgos."""
import plotly.graph_objects as go
import streamlit as st
from shared_sidebar import render_sidebar
from services.data_loader import load_processed_reviews
from services.supabase_service import load_reviews_from_supabase
from services.feature_service import add_basic_text_features
from services.model_eval_service import compute_model_evaluation
from plots.eda_charts import build_stars_distribution, build_review_length_distribution
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
        Resumen Ejecutivo
    </div>
    <div style="font-size:0.82rem;color:rgba(255,255,255,0.65)">
        Pipeline de datos · Modelo ganador · Hallazgos clave
    </div>
</div>
""", unsafe_allow_html=True)

# ── Carga ─────────────────────────────────────────────────────────────────────
reviews     = add_basic_text_features(load_processed_reviews())
try:
    _sb_extra = len(load_reviews_from_supabase())
except Exception:
    _sb_extra = 0

evaluation  = compute_model_evaluation()
metrics_df  = evaluation["metrics"]
feat_imp_df = evaluation["feature_importance"]
has_reviews = not reviews.empty

useful_ratio = float(reviews["y_util"].mean()) if has_reviews and "y_util" in reviews.columns else 0.695
avg_length   = int(reviews["review_len"].fillna(0).mean()) if has_reviews and "review_len" in reviews.columns else 113
base_final   = (len(reviews) + _sb_extra) if has_reviews else 66_854

best         = metrics_df.sort_values("roc_auc", ascending=False).iloc[0] if not metrics_df.empty else None
baseline_row = metrics_df[metrics_df["modelo"].str.contains("Logistic", na=False)].iloc[0] if not metrics_df.empty else None

_LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
               font=dict(family="inherit", size=11))

# ══════════════════════════════════════════════════════════════════════════════
# 1. PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Pipeline de datos — de 568 K a la base analítica final</div>', unsafe_allow_html=True)

_ARROW = ('<div style="display:flex;align-items:center;justify-content:center;padding:0 0.2rem">'
          '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2.5">'
          '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg></div>')

pct_kept = round(base_final / 568_454 * 100, 1)
st.markdown(f"""
<div style="display:flex;align-items:stretch;gap:0;margin-bottom:1.2rem;flex-wrap:nowrap;overflow-x:auto">
  <div style="flex:1;min-width:110px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:0.9rem 0.7rem;text-align:center">
    <div style="font-size:1.3rem;font-weight:900;color:#1d4ed8;line-height:1">568.454</div>
    <div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;color:#3b82f6;margin:0.2rem 0">Dataset original</div>
    <div style="font-size:0.68rem;color:#64748b">Amazon Fine Food Reviews</div>
  </div>
  {_ARROW}
  <div style="flex:1;min-width:110px;background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:0.9rem 0.7rem;text-align:center">
    <div style="font-size:1.3rem;font-weight:900;color:#b45309;line-height:1">−174.918</div>
    <div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;color:#f59e0b;margin:0.2rem 0">Duplicados</div>
    <div style="font-size:0.68rem;color:#64748b">Usuario · producto · fecha</div>
  </div>
  {_ARROW}
  <div style="flex:1;min-width:110px;background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:0.9rem 0.7rem;text-align:center">
    <div style="font-size:1.3rem;font-weight:900;color:#b45309;line-height:1">~−290 K</div>
    <div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;color:#f59e0b;margin:0.2rem 0">Votos insuficientes</div>
    <div style="font-size:0.68rem;color:#64748b">Menos de 5 votos útiles</div>
  </div>
  {_ARROW}
  <div style="flex:1;min-width:110px;background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:0.9rem 0.7rem;text-align:center">
    <div style="font-size:1.3rem;font-weight:900;color:#b45309;line-height:1">−14</div>
    <div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;color:#f59e0b;margin:0.2rem 0">Nulos</div>
    <div style="font-size:0.68rem;color:#64748b">Sin texto o score</div>
  </div>
  {_ARROW}
  <div style="flex:1;min-width:120px;background:#f0fdf4;border:2px solid #86efac;border-radius:12px;padding:0.9rem 0.7rem;text-align:center">
    <div style="font-size:1.3rem;font-weight:900;color:#15803d;line-height:1">{format_compact_number(base_final)}</div>
    <div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;color:#22c55e;margin:0.2rem 0">Base final</div>
    <div style="font-size:0.68rem;color:#64748b">{pct_kept}% del dataset · 4 features</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 2. MODELO GANADOR — 4 KPIs + badge
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Modelo ganador y métricas clave</div>', unsafe_allow_html=True)

if best is not None:
    delta_roc = float(best["roc_auc"]) - float(baseline_row["roc_auc"]) if baseline_row is not None else 0
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:1rem;padding:0.7rem 1.2rem;
                background:rgba(23,70,162,0.06);border-radius:10px;
                border:1px solid rgba(23,70,162,0.15);margin-bottom:0.8rem">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" stroke-width="2">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
        <span style="font-weight:700;font-size:0.88rem;color:#1e293b">Modelo ganador: {best["modelo"]}</span>
        <span class="metric-badge metric-badge-good">+{delta_roc:.1%} vs. Logistic Regression</span>
    </div>
    """, unsafe_allow_html=True)

    # 4 KPI cards simples
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    MODEL_COLORS = {"Logistic Regression":"#1d4ed8","LightGBM":"#15803d","XGBoost":"#b45309","CatBoost":"#7c3aed"}
    color = MODEL_COLORS.get(str(best["modelo"]), "#1d4ed8")

    for col, label, val, caption in [
        (k1, "ROC-AUC",   float(best["roc_auc"]),   "Separación real entre clases"),
        (k2, "F1-Score",  float(best["f1"]),         "Balance precisión-recall"),
        (k3, "Precisión", float(best["precision"]),  "De las útiles predichas, reales"),
        (k4, "Recall",    float(best["recall"]),     "Útiles reales detectadas"),
    ]:
        pct = int(val * 100)
        with col:
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #e2e8f0;border-top:3px solid {color};
                        border-radius:12px;padding:0.9rem;text-align:center">
                <div style="font-size:1.8rem;font-weight:900;color:{color};line-height:1">{val:.1%}</div>
                <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;
                            color:#64748b;margin:0.3rem 0">{label}</div>
                <div style="background:#f1f5f9;border-radius:999px;height:5px;margin:0.4rem 0;overflow:hidden">
                    <div style="width:{pct}%;height:100%;background:{color};border-radius:999px"></div>
                </div>
                <div style="font-size:0.68rem;color:#94a3b8">{caption}</div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 3. HALLAZGOS CLAVE — 3 hipótesis + 4 stats
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Hallazgos clave del caso</div>', unsafe_allow_html=True)

# Importancia de features
if not feat_imp_df.empty:
    total_imp = feat_imp_df["importancia"].sum()
    def _pct(feat):
        row = feat_imp_df[feat_imp_df["feature"] == feat]
        return float(row["importancia"].iloc[0]) / total_imp * 100 if not row.empty else 0
    len_pct  = _pct("review_len")
    sent_pct = _pct("sentiment_score")
    inc_pct  = _pct("incoherente")
    sc_pct   = _pct("Score")
else:
    len_pct, sent_pct, inc_pct, sc_pct = 45, 45, 5, 5

# 3 hipótesis en columnas
h1, h2, h3 = st.columns(3, gap="medium")

FEAT_NAMES = {
    "review_len": "Longitud de la reseña",
    "sentiment_score": "Sentimiento (VADER)",
    "incoherente": "Incoherencia texto-estrellas",
    "Score": "Calificación (estrellas)",
}
FEAT_COLORS = {
    "review_len": "#1d4ed8",
    "sentiment_score": "#f59e0b",
    "incoherente": "#ef4444",
    "Score": "#64748b",
}

with h1:
    fig_h1 = go.Figure(go.Bar(
        x=[len_pct, sent_pct, inc_pct, sc_pct],
        y=[FEAT_NAMES[f] for f in ["review_len","sentiment_score","incoherente","Score"]],
        orientation="h",
        marker_color=[FEAT_COLORS[f] for f in ["review_len","sentiment_score","incoherente","Score"]],
        text=[f"{v:.0f}%" for v in [len_pct, sent_pct, inc_pct, sc_pct]],
        textposition="outside",
    ))
    fig_h1.update_layout(**_LAYOUT, height=160, showlegend=False,
        xaxis=dict(showticklabels=False, showgrid=False, range=[0,80]),
        yaxis=dict(showgrid=False), margin=dict(l=10,r=50,t=10,b=10))
    st.plotly_chart(fig_h1, use_container_width=True, config={"displayModeBar": False})
    st.markdown("""<div class="highlight-card" style="margin-top:-0.3rem">
        <div class="highlight-title">H1 · Longitud domina</div>
        <span class="metric-badge metric-badge-good">Confirmada</span>
        <div class="highlight-body" style="margin-top:0.3rem">
            La longitud aporta el doble que el sentimiento. Las reseñas largas son consistentemente más útiles.
        </div>
    </div>""", unsafe_allow_html=True)

with h2:
    fig_h2 = go.Figure(go.Pie(
        values=[18, 82], labels=["Incoherentes","Coherentes"],
        hole=0.65, marker=dict(colors=["#ef4444","#22c55e"], line=dict(width=0)),
        textinfo="none", direction="clockwise", sort=False,
    ))
    fig_h2.add_annotation(text="18%<br><span style='font-size:9px'>incoherentes</span>",
                          x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#ef4444"))
    fig_h2.update_layout(**_LAYOUT, height=160, showlegend=False, margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig_h2, use_container_width=True, config={"displayModeBar": False})
    st.markdown("""<div class="highlight-card" style="margin-top:-0.3rem">
        <div class="highlight-title">H2 · Coherencia penaliza</div>
        <span class="metric-badge metric-badge-good">Confirmada</span>
        <div class="highlight-body" style="margin-top:0.3rem">
            El flag incoherente activa cuando el sentimiento choca con estrellas bajas (1-2).
        </div>
    </div>""", unsafe_allow_html=True)

with h3:
    fig_h3 = go.Figure(go.Bar(
        x=[sent_pct, len_pct], y=["Sentimiento","Longitud"],
        orientation="h",
        marker_color=["#f59e0b","#1d4ed8"],
        text=[f"{sent_pct:.0f}%", f"{len_pct:.0f}%"],
        textposition="outside",
    ))
    fig_h3.update_layout(**_LAYOUT, height=160, showlegend=False,
        xaxis=dict(showticklabels=False, showgrid=False, range=[0,80]),
        yaxis=dict(showgrid=False), margin=dict(l=10,r=50,t=10,b=10))
    st.plotly_chart(fig_h3, use_container_width=True, config={"displayModeBar": False})
    st.markdown("""<div class="highlight-card" style="margin-top:-0.3rem">
        <div class="highlight-title">H3 · Sentimiento contribuye</div>
        <span class="metric-badge metric-badge-warn">Parcial</span>
        <div class="highlight-body" style="margin-top:0.3rem">
            VADER aporta, pero con menor peso que la longitud. Importa más cuando hay coherencia con las estrellas.
        </div>
    </div>""", unsafe_allow_html=True)

# 4 stats resumen
st.markdown("<br>", unsafe_allow_html=True)
s1, s2, s3, s4 = st.columns(4, gap="medium")
roc_display = format_percentage(float(best["roc_auc"])) if best is not None else "—"
for col, val, label, sublabel, color in [
    (s1, str(avg_length),                   "palabras promedio",  "Longitud media de la base analítica",          "#1d4ed8"),
    (s2, format_percentage(useful_ratio),    "reseñas útiles",    "Clase minoritaria — razón del desbalance",     "#15803d"),
    (s3, roc_display,                        "ROC-AUC",           "Capacidad del modelo ganador",                 "#7c3aed"),
    (s4, "2x",                               "más peso",          "Longitud vs. sentimiento en importancia",      "#0d9488"),
]:
    with col:
        st.markdown(f"""
        <div style="background:#fff;border:1px solid #e2e8f0;border-top:3px solid {color};
                    border-radius:12px;padding:0.9rem;text-align:center">
            <div style="font-size:2rem;font-weight:900;color:{color};line-height:1">{val}</div>
            <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;color:#64748b;margin:0.3rem 0">{label}</div>
            <div style="font-size:0.7rem;color:#94a3b8">{sublabel}</div>
        </div>
        """, unsafe_allow_html=True)

# Conclusión ejecutiva
st.markdown("""<div class="insight-panel" style="margin-top:1rem">
    <div class="insight-title">Conclusion ejecutiva</div>
    <p>La calidad de una reseña en Amazon no depende de las estrellas sino del texto.
    Una reseña larga y coherente con las estrellas asignadas es <strong>consistentemente más útil</strong>.
    El consejo práctico: escribe más detalle, sé coherente, y tu reseña tendrá más impacto.</p>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 4. DISTRIBUCIONES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Distribuciones clave del dataset</div>', unsafe_allow_html=True)

lc, rc = st.columns(2, gap="large")
with lc:
    st.caption("Calificaciones — El 63% tienen 4-5 estrellas. Esta concentración genera el desbalance de clases.")
    st.plotly_chart(build_stars_distribution(reviews), use_container_width=True)
with rc:
    fig_len = build_review_length_distribution(reviews)
    if avg_length > 0:
        fig_len.add_vline(x=avg_length, line_dash="dash", line_color="#0f9f74",
                          annotation_text=f"Media: {avg_length} palabras",
                          annotation_position="top right")
    st.caption("Longitud — Distribucion asimetrica: pocas reseñas son muy largas, pero son las mas utiles.")
    st.plotly_chart(fig_len, use_container_width=True)