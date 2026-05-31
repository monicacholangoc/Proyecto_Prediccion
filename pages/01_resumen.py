"""Resumen ejecutivo — métricas del caso, modelos e hipótesis verificadas."""
import streamlit as st
from shared_sidebar import render_sidebar
from components.cards import render_metric_card
from services.data_loader import load_processed_reviews
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
            Indicadores del pipeline · Métricas de modelos · Hipótesis verificadas · Hallazgos clave
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Carga de datos ────────────────────────────────────────────────────────────
reviews    = add_basic_text_features(load_processed_reviews())
evaluation = compute_model_evaluation()
metrics_df = evaluation["metrics"]
has_reviews = not reviews.empty

useful_ratio = float(reviews["y_util"].mean()) if has_reviews and "y_util" in reviews.columns else 0.0
avg_length   = int(reviews["review_len"].fillna(0).mean()) if has_reviews and "review_len" in reviews.columns else 0

best         = metrics_df.sort_values("roc_auc", ascending=False).iloc[0] if not metrics_df.empty else None
baseline     = metrics_df[metrics_df["modelo"].str.contains("Logistic|logistic", na=False)] if not metrics_df.empty else None
baseline_row = baseline.iloc[0] if baseline is not None and not baseline.empty else None

# ── 1. Pipeline de datos ──────────────────────────────────────────────────────
st.markdown('<div class="section-label">Pipeline de datos — de 568 K a la base analítica final</div>', unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="stat-row">
        <div class="stat-pill">
            <div class="stat-pill-icon stat-pill-icon-blue">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/></svg>
            </div>
            <div><div class="stat-pill-value">568.454</div><div class="stat-pill-label">Reseñas originales</div></div>
        </div>
        <div class="stat-pill">
            <div class="stat-pill-icon stat-pill-icon-amber">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b45309" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
            </div>
            <div><div class="stat-pill-value">174.918</div><div class="stat-pill-label">Duplicados eliminados</div></div>
        </div>
        <div class="stat-pill">
            <div class="stat-pill-icon stat-pill-icon-amber">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b45309" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
            </div>
            <div><div class="stat-pill-value">~290 K</div><div class="stat-pill-label">Filtradas (&lt; 5 votos)</div></div>
        </div>
        <div class="stat-pill">
            <div class="stat-pill-icon stat-pill-icon-teal">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0d9488" stroke-width="2" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            </div>
            <div><div class="stat-pill-value">{format_compact_number(len(reviews)) if has_reviews else '—'}</div><div class="stat-pill-label">Base analítica final (≥ 5 votos)</div></div>
        </div>
        <div class="stat-pill">
            <div class="stat-pill-icon stat-pill-icon-green">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#15803d" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
            <div><div class="stat-pill-value">4 features</div><div class="stat-pill-label">Derivadas del texto</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True,
)

# ── 2. Métricas de modelos ────────────────────────────────────────────────────
st.markdown('<div class="section-label">Rendimiento de modelos — comparativa final</div>', unsafe_allow_html=True)

if best is not None:
    delta_roc = float(best["roc_auc"]) - float(baseline_row["roc_auc"]) if baseline_row is not None else 0
    delta_f1  = float(best["f1"])      - float(baseline_row["f1"])      if baseline_row is not None else 0

    m1, m2, m3, m4, m5 = st.columns(5, gap="medium")
    with m1:
        render_metric_card(
            "Modelo ganador",
            str(best["modelo"]),
            f"+{delta_roc:.1%} ROC-AUC vs. Logistic Regression"
        )
    with m2:
        render_metric_card("ROC-AUC", format_percentage(float(best["roc_auc"])), "Separación real entre clases. 100% = perfecto, 50% = azar")
    with m3:
        render_metric_card("F1-Score", format_percentage(float(best["f1"])),  "Balance precisión-recall. Correcto para clases desbalanceadas")
    with m4:
        render_metric_card("Precisión", format_percentage(float(best["precision"])), "De cada 100 predichas útiles, ¿cuántas realmente lo son?")
    with m5:
        render_metric_card("Recall",    format_percentage(float(best["recall"])),    "De todas las útiles reales, ¿cuántas detecta el modelo?")

    st.plotly_chart(build_model_metrics_chart(metrics_df), use_container_width=True)

    # Explicación de por qué no accuracy
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

# ── 3. Indicadores del dataset ────────────────────────────────────────────────
st.markdown('<div class="section-label">Indicadores clave del dataset</div>', unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4, gap="medium")
with k1: render_metric_card("Reseñas útiles (≥ 0.70)", format_percentage(useful_ratio),     "Proporción de la variable objetivo — confirma el desbalance de clases")
with k2: render_metric_card("Longitud media",            f"{avg_length} palabras",           "Feature #1 del modelo — las reseñas largas tienden a ser más útiles")
with k3: render_metric_card("Desbalance de clases",      f"{format_percentage(1-useful_ratio)} no útiles", "Justifica F1 y ROC-AUC en lugar de Accuracy")
with k4: render_metric_card("Features del modelo",       "4 derivadas",                     "review_len · sentiment_score · incoherente · Score")

# ── 4. Hipótesis verificadas ──────────────────────────────────────────────────
st.markdown('<div class="section-label">Hipótesis verificadas durante el análisis</div>', unsafe_allow_html=True)
h1, h2, h3 = st.columns(3, gap="medium")
hypotheses = [
    ("H1 · Longitud",    "Confirmada ✓", "metric-badge-good",
     "Las reseñas más largas son consistentemente más útiles. <code>review_len</code> es el feature de mayor peso en el modelo — aporta más del doble que el sentimiento."),
    ("H2 · Coherencia",  "Confirmada ✓", "metric-badge-good",
     "La incoherencia tono-estrellas activa el flag <code>incoherente</code> y penaliza la predicción. Las reseñas con sentimiento positivo y 1–2 estrellas son clasificadas como no útiles."),
    ("H3 · Sentimiento", "Parcial ⚠",    "metric-badge-warn",
     "VADER contribuye a la predicción, pero con menor peso que la longitud. El sentimiento importa más cuando hay coherencia con la calificación de estrellas."),
]
for col, (title, result, badge_class, body) in zip([h1, h2, h3], hypotheses):
    with col:
        st.markdown(
            f"""<div class="highlight-card">
                <div class="highlight-title">{title}</div>
                <span class="metric-badge {badge_class}" style="margin-bottom:0.5rem;display:inline-block">{result}</span>
                <div class="highlight-body">{body}</div>
            </div>""", unsafe_allow_html=True,
        )

# ── 5. Hallazgo principal ─────────────────────────────────────────────────────
st.markdown(
    """<div class="insight-panel">
        <div class="insight-title">Hallazgo principal del caso</div>
        <p>La calidad de una reseña en Amazon no depende de la calificación en estrellas sino del texto.
        Una reseña larga, con sentimiento coherente con las estrellas asignadas, es
        <strong>consistentemente más útil</strong> para otros compradores.
        El consejo práctico derivado del modelo: escribí más detalle, sé coherente,
        y tu reseña tendrá más impacto en las decisiones de compra de otros.</p>
    </div>""", unsafe_allow_html=True,
)

# ── 6. Distribuciones clave ───────────────────────────────────────────────────
st.markdown('<div class="section-label">Distribuciones clave del dataset</div>', unsafe_allow_html=True)
lc, rc = st.columns(2, gap="large")
with lc:
    st.caption("**Calificaciones** — El 63 % de las reseñas tienen 4–5 estrellas. Esta concentración genera desbalance de clases y es la razón principal por la que Accuracy no es una métrica válida aquí.")
    st.plotly_chart(build_stars_distribution(reviews), use_container_width=True)
with rc:
    fig2 = build_review_length_distribution(reviews)
    if avg_length > 0:
        fig2.add_vline(x=avg_length, line_dash="dash", line_color="#0f9f74",
                       annotation_text=f"Media: {avg_length} palabras", annotation_position="top right")
    st.caption("**Longitud** — Distribución asimétrica: pocas reseñas son muy largas, pero son consistentemente las más útiles. Confirma la hipótesis H1 del caso.")
    st.plotly_chart(fig2, use_container_width=True)