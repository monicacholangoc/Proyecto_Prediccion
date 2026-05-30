"""Modelos y evaluación — comparación en tarjetas, sin texto de relleno."""

import plotly.express as px
import streamlit as st

from components.cards import render_metric_card
from plots.model_charts import (
    build_confusion_matrix_chart,
    build_model_metrics_chart,
    build_roc_chart,
)
from services.model_eval_service import compute_model_evaluation
from utils.formatters import format_percentage


def load_css() -> None:
    with open("styles/styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def _render_logo() -> str:
    return """
    <svg class="sidebar-logo-svg" width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="38" height="38" rx="10" fill="url(#lg1m)"/>
      <path d="M10 26 L19 12 L28 26 Z" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.5)" stroke-width="1.2"/>
      <path d="M14 26 L19 17 L24 26 Z" fill="rgba(255,255,255,0.9)"/>
      <circle cx="19" cy="11" r="2.5" fill="#7dd3fc"/>
      <defs>
        <linearGradient id="lg1m" x1="0" y1="0" x2="38" y2="38" gradientUnits="userSpaceOnUse">
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

st.title("Modelos y Evaluación")
st.caption("Comparación de clasificadores con métricas apropiadas para datos desbalanceados.")

evaluation         = compute_model_evaluation()
metrics_df         = evaluation["metrics"]
feature_imp_df     = evaluation["feature_importance"]
roc_curves         = evaluation["roc_curves"]
confusion_matrices = evaluation["confusion_matrices"]

if metrics_df.empty:
    st.warning("No fue posible calcular métricas. Verifica que el parquet procesado tenga las columnas esperadas.")
    st.stop()

best      = metrics_df.sort_values("roc_auc", ascending=False).iloc[0]
best_name = best["modelo"]

# ── Por qué no Accuracy ────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="accuracy-warning">
        <div class="aw-title">Por qué no se usa Accuracy</div>
        <p>Con ~70 % de reseñas "no útiles", un modelo que prediga siempre "no útil" alcanzaría ~70 % de Accuracy
        <strong>sin aprender nada</strong>. Se usan <strong>F1-Score</strong> y <strong>ROC-AUC</strong>,
        válidos con clases desbalanceadas.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Comparación por modelo — una fila de tarjetas por modelo ──────────────────
st.markdown('<div class="section-label">Comparación de modelos</div>', unsafe_allow_html=True)

for _, row in metrics_df.iterrows():
    is_best      = str(row["modelo"]) == best_name
    border_style = "border: 2px solid var(--primary);" if is_best else ""
    badge_class  = "metric-badge-good" if is_best else "metric-badge-info"
    badge_label  = "Modelo ganador" if is_best else "Baseline"

    mc1, mc2, mc3, mc4, mc5 = st.columns([2, 1, 1, 1, 1], gap="medium")
    with mc1:
        st.markdown(
            f"""
            <div class="metric-card" style="{border_style}">
                <div class="metric-label">Modelo</div>
                <div class="metric-value" style="font-size:1.1rem">{row['modelo']}</div>
                <span class="metric-badge {badge_class}">{badge_label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with mc2:
        render_metric_card("Precisión", f"{float(row['precision']):.4f}", "TP / (TP + FP)")
    with mc3:
        render_metric_card("Recall", f"{float(row['recall']):.4f}", "TP / (TP + FN)")
    with mc4:
        render_metric_card("F1-Score", f"{float(row['f1']):.4f}", "Precisión + Recall")
    with mc5:
        render_metric_card("ROC-AUC", f"{float(row['roc_auc']):.4f}", "Capacidad discriminativa")

st.plotly_chart(build_model_metrics_chart(metrics_df), use_container_width=True)

# ── Importancia de variables ───────────────────────────────────────────────────
st.markdown('<div class="section-label">Importancia de variables</div>', unsafe_allow_html=True)
st.caption("El feature de mayor peso define qué acción concreta puede mejorar la utilidad de una reseña.")

if not feature_imp_df.empty:
    ordered     = feature_imp_df.sort_values("importancia", ascending=False)
    ordered_asc = ordered.sort_values("importancia", ascending=True)

    feature_labels = {
        "review_len":      "Escribe más detalle — factor #1",
        "sentiment_score": "El tono importa, pero menos que la extensión",
        "incoherente":     "La incoherencia penaliza la utilidad",
        "Score":           "Las estrellas aportan contexto",
    }

    fig_imp = px.bar(
        ordered_asc, x="importancia", y="feature", orientation="h",
        title="Importancia relativa — LightGBM",
        template="plotly_white", color_discrete_sequence=["#1d4ed8"],
    )
    for _, row in ordered.iterrows():
        label = feature_labels.get(row["feature"], "")
        if label:
            fig_imp.add_annotation(
                x=float(row["importancia"]) + 0.002, y=row["feature"],
                text=label, showarrow=False, xanchor="left",
                font=dict(size=11, color="#526277"),
            )
    fig_imp.update_layout(height=320, margin=dict(r=260))
    st.plotly_chart(fig_imp, use_container_width=True)

    # Tarjetas por variable
    imp_cols = st.columns(len(ordered), gap="medium")
    for col, (_, row) in zip(imp_cols, ordered.iterrows()):
        with col:
            render_metric_card(
                str(row["feature"]),
                f"{float(row['importancia']):.1%}",
                feature_labels.get(row["feature"], ""),
            )
else:
    st.info("No hay datos de importancia de variables disponibles.")

# ── Curva ROC ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Curva ROC</div>', unsafe_allow_html=True)
st.caption("Área = 1.0 es el clasificador perfecto. La diagonal es el azar puro (AUC = 0.5).")
st.plotly_chart(build_roc_chart(metrics_df, roc_curves), use_container_width=True)

# ── Matriz de confusión ────────────────────────────────────────────────────────
st.markdown(f'<div class="section-label">Matriz de confusión — {best_name}</div>', unsafe_allow_html=True)
st.caption("Los falsos negativos (útiles clasificadas como no útiles) son el error más costoso.")
st.plotly_chart(
    build_confusion_matrix_chart(confusion_matrices.get(best_name), best_name),
    use_container_width=True,
)