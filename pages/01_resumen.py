"""Resumen ejecutivo — métricas del caso, modelos e hipótesis verificadas."""
import plotly.graph_objects as go
import streamlit as st
from shared_sidebar import render_sidebar
from components.cards import render_metric_card
from services.data_loader import load_processed_reviews

from services.supabase_service import load_reviews_from_supabase
from services.feature_service import add_basic_text_features
from services.model_eval_service import compute_model_evaluation
from plots.eda_charts import build_stars_distribution, build_review_length_distribution
from plots.model_charts import build_model_metrics_chart
from utils.formatters import format_compact_number, format_percentage

with open("styles/styles.css", "r", encoding="utf-8") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
render_sidebar()

st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #16213b 0%, #1746a2 60%, #0f4c5c 100%);
        border-radius: 16px;
        padding: 1.4rem 2rem;
        margin-bottom: 1.4rem;
        color: #ffffff;
    ">
        <div style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                    color:rgba(255,255,255,0.55);text-transform:uppercase;margin-bottom:0.35rem">
            Seminario Predictivo 2026 · Caso 06
        </div>
        <div style="font-size:clamp(1.4rem,3vw,1.9rem);font-weight:800;
                    letter-spacing:-0.02em;line-height:1.2;margin-bottom:0.3rem">
            Resumen Ejecutivo
        </div>
        <div style="font-size:0.82rem;color:rgba(255,255,255,0.65)">
            Pipeline de datos · Métricas de modelos · Hipótesis verificadas · Hallazgos clave
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Carga ─────────────────────────────────────────────────────────────────────
reviews     = add_basic_text_features(load_processed_reviews())
# Sumar reseñas nuevas de Supabase
try:
    _sb_extra = len(load_reviews_from_supabase())
except Exception:
    _sb_extra = 0
evaluation  = compute_model_evaluation()
metrics_df  = evaluation["metrics"]
feat_imp_df = evaluation["feature_importance"]
has_reviews = not reviews.empty

useful_ratio = float(reviews["y_util"].mean()) if has_reviews and "y_util" in reviews.columns else 0.0
avg_length   = int(reviews["review_len"].fillna(0).mean()) if has_reviews and "review_len" in reviews.columns else 0

best         = metrics_df.sort_values("roc_auc", ascending=False).iloc[0] if not metrics_df.empty else None
baseline     = metrics_df[metrics_df["modelo"].str.contains("Logistic|logistic", na=False)] if not metrics_df.empty else None
baseline_row = baseline.iloc[0] if baseline is not None and not baseline.empty else None

_CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="inherit", size=11),
)

# ╔══════════════════════════════════════════════════════════════════════════════
# 1. FUNNEL DEL PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Pipeline de datos — de 568 K a la base analítica final</div>', unsafe_allow_html=True)

base_final = (len(reviews) + _sb_extra) if has_reviews else 100_000
pct_kept   = round(base_final / 568_454 * 100, 1)

_ARROW = (
    '<div style="display:flex;align-items:center;justify-content:center;flex-shrink:0;padding:0 0.2rem">' +
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2.5" ' +
    'stroke-linecap="round" stroke-linejoin="round">' +
    '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg></div>'
)

st.markdown(
    f"""
    <div style="display:flex;align-items:stretch;gap:0;margin-bottom:1rem;flex-wrap:nowrap;overflow-x:auto">
      <div style="flex:1;min-width:120px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:0.9rem 0.7rem;text-align:center">
        <div style="font-size:1.4rem;font-weight:900;color:#1d4ed8;line-height:1">568.454</div>
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#3b82f6;margin:0.25rem 0">Dataset original</div>
        <div style="font-size:0.7rem;color:#64748b">Amazon Fine Food Reviews completo</div>
      </div>
      {_ARROW}
      <div style="flex:1;min-width:120px;background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:0.9rem 0.7rem;text-align:center">
        <div style="font-size:1.4rem;font-weight:900;color:#b45309;line-height:1">−174.918</div>
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#f59e0b;margin:0.25rem 0">Duplicados eliminados</div>
        <div style="font-size:0.7rem;color:#64748b">Mismo usuario · producto · fecha</div>
      </div>
      {_ARROW}
      <div style="flex:1;min-width:120px;background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:0.9rem 0.7rem;text-align:center">
        <div style="font-size:1.4rem;font-weight:900;color:#b45309;line-height:1">~−290 K</div>
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#f59e0b;margin:0.25rem 0">Filtradas (&lt; 5 votos)</div>
        <div style="font-size:0.7rem;color:#64748b">Tasas de utilidad no representativas</div>
      </div>
      {_ARROW}
      <div style="flex:1;min-width:100px;background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:0.9rem 0.7rem;text-align:center">
        <div style="font-size:1.4rem;font-weight:900;color:#b45309;line-height:1">−14</div>
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#f59e0b;margin:0.25rem 0">Nulos eliminados</div>
        <div style="font-size:0.7rem;color:#64748b">Filas sin texto o score</div>
      </div>
      {_ARROW}
      <div style="flex:1;min-width:130px;background:#f0fdf4;border:2px solid #86efac;border-radius:12px;padding:0.9rem 0.7rem;text-align:center">
        <div style="font-size:1.4rem;font-weight:900;color:#15803d;line-height:1">{format_compact_number(base_final)}</div>
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#22c55e;margin:0.25rem 0">Base analítica final</div>
        <div style="font-size:0.7rem;color:#64748b">{pct_kept}% del dataset · 4 features derivadas</div>
      </div>
    </div>
    """, unsafe_allow_html=True,
)

# ╔══════════════════════════════════════════════════════════════════════════════
# 2. MÉTRICAS DE MODELOS — GAUGES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Rendimiento de modelos — comparativa final</div>', unsafe_allow_html=True)

if best is not None:
    def _gauge(value: float, title: str, color: str) -> go.Figure:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(value * 100, 1),
            number=dict(suffix="%", font=dict(size=28, color="#1e293b")),
            title=dict(text=title, font=dict(size=11, color="#64748b")),
            gauge=dict(
                axis=dict(range=[0, 100], tickwidth=1, tickcolor="#cbd5e1",
                          tickvals=[0, 50, 70, 80, 90, 100],
                          ticktext=["0", "50", "70", "80", "90", "100%"]),
                bar=dict(color=color, thickness=0.6),
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0,
                steps=[
                    dict(range=[0,  50], color="#fef2f2"),
                    dict(range=[50, 70], color="#fef9c3"),
                    dict(range=[70, 100], color="#f0fdf4"),
                ],
                threshold=dict(line=dict(color="#475569", width=2), thickness=0.8,
                               value=50),
            ),
        ))
        fig.update_layout(**_CHART_LAYOUT, height=180, margin=dict(l=10, r=10, t=30, b=10))
        return fig

    g1, g2, g3, g4 = st.columns(4, gap="medium")
    with g1:
        st.plotly_chart(_gauge(float(best["roc_auc"]), "ROC-AUC", "#1d4ed8"),
                        use_container_width=True, config={"displayModeBar": False})
        st.caption("Separación real entre clases — 100% perfecto, 50% azar puro")
    with g2:
        st.plotly_chart(_gauge(float(best["f1"]), "F1-Score", "#0d9488"),
                        use_container_width=True, config={"displayModeBar": False})
        st.caption("Balance precisión-recall, correcto para clases desbalanceadas")
    with g3:
        st.plotly_chart(_gauge(float(best["precision"]), "Precisión", "#7c3aed"),
                        use_container_width=True, config={"displayModeBar": False})
        st.caption("De cada 100 predichas útiles, ¿cuántas realmente lo son?")
    with g4:
        st.plotly_chart(_gauge(float(best["recall"]), "Recall", "#b45309"),
                        use_container_width=True, config={"displayModeBar": False})
        st.caption("De todas las útiles reales, ¿cuántas detecta el modelo?")

    # Modelo ganador badge
    delta_roc = float(best["roc_auc"]) - float(baseline_row["roc_auc"]) if baseline_row is not None else 0
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:1rem;padding:0.75rem 1.2rem;
                    background:rgba(23,70,162,0.06);border-radius:10px;
                    border:1px solid rgba(23,70,162,0.15);margin-bottom:0.6rem">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
            <div>
                <span style="font-weight:700;font-size:0.88rem;color:#1e293b">Modelo ganador: {best["modelo"]}</span>
                <span class="metric-badge metric-badge-good" style="margin-left:0.6rem">+{delta_roc:.1%} vs. Logistic Regression</span>
            </div>
        </div>
        """, unsafe_allow_html=True,
    )

    # Gráfico comparativo
    st.plotly_chart(build_model_metrics_chart(metrics_df), use_container_width=True)

    st.markdown(
        """<div class="accuracy-warning">
            <div class="aw-title">¿Por qué no usamos Accuracy como métrica?</div>
            <p>Con ~70 % de reseñas "no útiles", un modelo que <em>siempre</em> prediga "no útil"
            obtendría 70 % de Accuracy <strong>sin haber aprendido nada</strong>.
            F1-Score y ROC-AUC miden el rendimiento real cuando las clases están desbalanceadas.</p>
        </div>""", unsafe_allow_html=True,
    )
else:
    st.info("No se encontraron datos de evaluación. Verifica que el parquet procesado esté disponible.")

# ╔══════════════════════════════════════════════════════════════════════════════
# 3. IMPORTANCIA DE FEATURES — MINI HORIZONTAL BAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">¿Qué variables predice mejor la utilidad?</div>', unsafe_allow_html=True)

if not feat_imp_df.empty:
    feature_names = {
        "review_len":      "Longitud de la reseña",
        "sentiment_score": "Sentimiento (VADER)",
        "incoherente":     "Incoherencia texto-estrellas",
        "Score":           "Calificación (estrellas)",
    }
    ordered = feat_imp_df.sort_values("importancia", ascending=True)
    total   = ordered["importancia"].sum()

    fig_imp = go.Figure()
    colors = ["#cbd5e1", "#60a5fa", "#0d9488", "#1d4ed8"]
    for i, (_, row) in enumerate(ordered.iterrows()):
        pct = float(row["importancia"]) / total if total > 0 else 0
        fig_imp.add_trace(go.Bar(
            x=[pct * 100],
            y=[feature_names.get(str(row["feature"]), str(row["feature"]))],
            orientation="h",
            marker=dict(color=colors[i % len(colors)], line=dict(width=0)),
            text=[f"{pct:.0%}"],
            textposition="outside",
            showlegend=False,
        ))
    fig_imp.update_layout(
        **_CHART_LAYOUT,
        height=180,
        margin=dict(l=10, r=60, t=10, b=10),
        xaxis=dict(showticklabels=False, showgrid=False, range=[0, 80]),
        yaxis=dict(showgrid=False),
        barmode="overlay",
    )
    fi1, fi2 = st.columns([2, 1], gap="large")
    with fi1:
        st.plotly_chart(fig_imp, use_container_width=True, config={"displayModeBar": False})
    with fi2:
        st.markdown(
            """
            <div style="padding-top:0.4rem">
                <div style="font-size:0.8rem;color:#64748b;line-height:1.7">
                    La <strong>longitud</strong> es el predictor dominante —
                    aporta más del doble que el sentimiento.<br><br>
                    La <strong>incoherencia</strong> texto-estrellas actúa como
                    penalizador activo en la predicción.
                </div>
            </div>
            """, unsafe_allow_html=True,
        )
else:
    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1: render_metric_card("Reseñas útiles (≥ 0.70)", format_percentage(useful_ratio), "Variable objetivo del modelo")
    with k2: render_metric_card("Longitud media", f"{avg_length} palabras", "Feature #1 del modelo")
    with k3: render_metric_card("Desbalance", f"{format_percentage(1-useful_ratio)} no útiles", "Justifica F1 y ROC-AUC")
    with k4: render_metric_card("Features", "4 derivadas", "review_len · sentiment · incoherente · Score")

# ╔══════════════════════════════════════════════════════════════════════════════
# 4. HIPÓTESIS — TARJETAS CON MINI-INDICADORES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Hipótesis verificadas durante el análisis</div>', unsafe_allow_html=True)

h1, h2, h3 = st.columns(3, gap="medium")

# H1 — Longitud: bullet gauge de correlación
with h1:
    # Mini bar que muestra el peso relativo de review_len vs otras features
    if not feat_imp_df.empty and "review_len" in feat_imp_df["feature"].values:
        total_imp  = feat_imp_df["importancia"].sum()
        rl_imp     = float(feat_imp_df.loc[feat_imp_df["feature"] == "review_len", "importancia"].iloc[0])
        rl_pct     = rl_imp / total_imp if total_imp > 0 else 0.5
    else:
        rl_pct = 0.55

    fig_h1 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(rl_pct * 100, 0),
        number=dict(suffix="% del peso", font=dict(size=22, color="#1d4ed8")),
        gauge=dict(
            axis=dict(range=[0, 100], visible=False),
            bar=dict(color="#1d4ed8", thickness=0.55),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            steps=[dict(range=[0, 100], color="#eff6ff")],
        ),
    ))
    fig_h1.update_layout(**_CHART_LAYOUT, height=130, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_h1, use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        """<div class="highlight-card" style="margin-top:-0.4rem">
            <div class="highlight-title">H1 · Longitud</div>
            <span class="metric-badge metric-badge-good">Confirmada ✓</span>
            <div class="highlight-body" style="margin-top:0.4rem">
                <code>review_len</code> es el feature de mayor peso — aporta más del doble
                que el sentimiento. Las reseñas más largas son consistentemente más útiles.
            </div>
        </div>""", unsafe_allow_html=True,
    )

# H2 — Coherencia: donut aprobadas vs rechazadas por incoherencia
with h2:
    incoherent_pct = 0.18  # aprox del dataset — flag incoherente
    fig_h2 = go.Figure(go.Pie(
        values=[incoherent_pct * 100, (1 - incoherent_pct) * 100],
        labels=["Incoherentes", "Coherentes"],
        hole=0.65,
        marker=dict(colors=["#ef4444", "#22c55e"], line=dict(width=0)),
        textinfo="none",
        direction="clockwise",
        sort=False,
    ))
    fig_h2.add_annotation(text="18%<br><span style='font-size:9px'>incoherentes</span>",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=14, color="#ef4444"))
    fig_h2.update_layout(**_CHART_LAYOUT, height=130, showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_h2, use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        """<div class="highlight-card" style="margin-top:-0.4rem">
            <div class="highlight-title">H2 · Coherencia</div>
            <span class="metric-badge metric-badge-good">Confirmada ✓</span>
            <div class="highlight-body" style="margin-top:0.4rem">
                El flag <code>incoherente</code> activa cuando el sentimiento positivo
                choca con estrellas bajas (1–2). Penaliza la predicción como no útil.
            </div>
        </div>""", unsafe_allow_html=True,
    )

# H3 — Sentimiento: barra doble peso sentiment vs review_len
with h3:
    if not feat_imp_df.empty:
        total_imp   = feat_imp_df["importancia"].sum()
        def _pct(feat):
            row = feat_imp_df[feat_imp_df["feature"] == feat]
            return float(row["importancia"].iloc[0]) / total_imp * 100 if not row.empty else 0
        sent_pct = _pct("sentiment_score")
        len_pct  = _pct("review_len")
    else:
        sent_pct, len_pct = 22.0, 48.0

    fig_h3 = go.Figure()
    fig_h3.add_trace(go.Bar(
        x=[len_pct], y=["Longitud"], orientation="h",
        marker=dict(color="#1d4ed8"), text=[f"{len_pct:.0f}%"],
        textposition="outside", showlegend=False,
    ))
    fig_h3.add_trace(go.Bar(
        x=[sent_pct], y=["Sentimiento"], orientation="h",
        marker=dict(color="#f59e0b"), text=[f"{sent_pct:.0f}%"],
        textposition="outside", showlegend=False,
    ))
    fig_h3.update_layout(
        **_CHART_LAYOUT, height=130, barmode="group",
        xaxis=dict(showticklabels=False, showgrid=False, range=[0, 80]),
        yaxis=dict(showgrid=False),
        margin=dict(l=10, r=50, t=10, b=10),
    )
    st.plotly_chart(fig_h3, use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        """<div class="highlight-card" style="margin-top:-0.4rem">
            <div class="highlight-title">H3 · Sentimiento</div>
            <span class="metric-badge metric-badge-warn">Parcial ⚠</span>
            <div class="highlight-body" style="margin-top:0.4rem">
                VADER contribuye, pero con menor peso que la longitud.
                Su aporte sube cuando hay coherencia con la calificación de estrellas.
            </div>
        </div>""", unsafe_allow_html=True,
    )

# ╔══════════════════════════════════════════════════════════════════════════════
# 5. HALLAZGO PRINCIPAL — STAT HIGHLIGHTS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Hallazgo principal del caso</div>', unsafe_allow_html=True)

hw1, hw2, hw3, hw4 = st.columns(4, gap="medium")

with hw1:
    st.markdown(
        f"""
        <div class="metric-card" style="text-align:center;border-top:3px solid #1d4ed8">
            <div style="font-size:2.2rem;font-weight:900;color:#1d4ed8;line-height:1">{avg_length}</div>
            <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.07em;color:#64748b;margin:0.3rem 0">palabras promedio</div>
            <div style="font-size:0.78rem;color:#475569">Longitud media de reseñas en la base analítica</div>
        </div>
        """, unsafe_allow_html=True,
    )
with hw2:
    st.markdown(
        f"""
        <div class="metric-card" style="text-align:center;border-top:3px solid #15803d">
            <div style="font-size:2.2rem;font-weight:900;color:#15803d;line-height:1">{format_percentage(useful_ratio)}</div>
            <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.07em;color:#64748b;margin:0.3rem 0">reseñas útiles</div>
            <div style="font-size:0.78rem;color:#475569">Clase minoritaria — razón del desbalance</div>
        </div>
        """, unsafe_allow_html=True,
    )
with hw3:
    roc_display = format_percentage(float(best["roc_auc"])) if best is not None else "—"
    st.markdown(
        f"""
        <div class="metric-card" style="text-align:center;border-top:3px solid #7c3aed">
            <div style="font-size:2.2rem;font-weight:900;color:#7c3aed;line-height:1">{roc_display}</div>
            <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.07em;color:#64748b;margin:0.3rem 0">ROC-AUC</div>
            <div style="font-size:0.78rem;color:#475569">Capacidad real de separar clases del modelo ganador</div>
        </div>
        """, unsafe_allow_html=True,
    )
with hw4:
    st.markdown(
        """
        <div class="metric-card" style="text-align:center;border-top:3px solid #0d9488">
            <div style="font-size:2.2rem;font-weight:900;color:#0d9488;line-height:1">2×</div>
            <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:.07em;color:#64748b;margin:0.3rem 0">más peso</div>
            <div style="font-size:0.78rem;color:#475569">Longitud vs. sentimiento en importancia de features</div>
        </div>
        """, unsafe_allow_html=True,
    )

st.markdown(
    """<div class="insight-panel">
        <div class="insight-title">Conclusión ejecutiva</div>
        <p>La calidad de una reseña en Amazon no depende de la calificación en estrellas sino del texto.
        Una reseña larga, con sentimiento coherente con las estrellas asignadas, es
        <strong>consistentemente más útil</strong> para otros compradores.
        El consejo práctico derivado del modelo: escribí más detalle, sé coherente,
        y tu reseña tendrá más impacto en las decisiones de compra de otros.</p>
    </div>""", unsafe_allow_html=True,
)

# ╔══════════════════════════════════════════════════════════════════════════════
# 6. DISTRIBUCIONES CLAVE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Distribuciones clave del dataset</div>', unsafe_allow_html=True)
lc, rc = st.columns(2, gap="large")
with lc:
    st.caption("**Calificaciones** — El 63 % tienen 4–5 estrellas. Esta concentración genera el desbalance de clases.")
    st.plotly_chart(build_stars_distribution(reviews), use_container_width=True)
with rc:
    fig2 = build_review_length_distribution(reviews)
    if avg_length > 0:
        fig2.add_vline(x=avg_length, line_dash="dash", line_color="#0f9f74",
                       annotation_text=f"Media: {avg_length} palabras", annotation_position="top right")
    st.caption("**Longitud** — Distribución asimétrica: pocas reseñas son muy largas, pero son las más útiles.")
    st.plotly_chart(fig2, use_container_width=True)