"""Comparacion de modelos y metricas del proyecto.

Estructura limpia:
1. Por que no accuracy (contexto)
2. Resultado de la comparacion (metricas + tabla)
3. Importancia de variables como hero visual — con anotaciones directas
4. Curva ROC
5. Matriz de confusion
Sin panels duplicados de interpretacion, sin highlight-cards de relleno.
"""

import plotly.graph_objects as go
import streamlit as st

from components.cards import render_metric_card
from plots.model_charts import (
    build_confusion_matrix_chart,
    build_feature_importance_chart,
    build_model_metrics_chart,
    build_roc_chart,
)
from services.model_eval_service import compute_model_evaluation
from utils.formatters import format_percentage


st.title("Modelos y Evaluación")
st.caption("Comparación de clasificadores, métricas apropiadas e interpretación de resultados.")

# ── Carga ─────────────────────────────────────────────────────────────────────

evaluation        = compute_model_evaluation()
metrics_df        = evaluation["metrics"]
feature_imp_df    = evaluation["feature_importance"]
roc_curves        = evaluation["roc_curves"]
confusion_matrices = evaluation["confusion_matrices"]

if metrics_df.empty:
    st.warning("No fue posible calcular métricas reales. Verifica que el parquet procesado tenga las columnas esperadas.")
    st.stop()

best       = metrics_df.sort_values("roc_auc", ascending=False).iloc[0]
best_name  = best["modelo"]

# ── 1. Por que no accuracy ────────────────────────────────────────────────────

st.markdown(
    """
    <div class="accuracy-warning">
        <div class="aw-title">¿Por qué no usamos Accuracy como métrica?</div>
        <p>
            Si el 65–70 % de las reseñas son "no útiles", un modelo que siempre prediga "no útil"
            tendría ~70 % de accuracy <strong>sin aprender nada</strong>.
            Usamos <strong>F1-Score</strong> (equilibrio entre precisión y recall)
            y <strong>ROC-AUC</strong> (capacidad discriminativa global), que funcionan
            correctamente con clases desbalanceadas.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 2. Resultado de la comparacion ───────────────────────────────────────────

st.markdown("### Resultado de la comparación")

baseline = metrics_df[metrics_df["modelo"].str.contains("Logistic|logistic", na=False)]
baseline_row = baseline.iloc[0] if not baseline.empty else None

m1, m2, m3, m4 = st.columns(4, gap="medium")
with m1:
    render_metric_card("Modelo ganador", best_name, "Mayor ROC-AUC en test (20 %)")
with m2:
    render_metric_card("ROC-AUC", format_percentage(float(best["roc_auc"])), "Capacidad de separar clases")
with m3:
    render_metric_card("F1-Score", format_percentage(float(best["f1"])), "Precisión + Recall balanceados")
with m4:
    if baseline_row is not None:
        delta = float(best["roc_auc"]) - float(baseline_row["roc_auc"])
        render_metric_card("Mejora sobre baseline", f"+{delta:.1%}", "vs. Regresión Logística")
    else:
        render_metric_card("Baseline", "Reg. Logística", "Modelo interpretable de referencia")

# Tabla comparativa
st.markdown("#### Tabla comparativa de métricas")
st.caption("Todas las métricas calculadas sobre el 20 % de datos de prueba con `random_state=42`.")

display_df = metrics_df.copy()
for col in ["precision", "recall", "f1", "roc_auc"]:
    if col in display_df.columns:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.4f}")

display_df = display_df.rename(columns={
    "modelo": "Modelo", "precision": "Precisión",
    "recall": "Recall", "f1": "F1-Score", "roc_auc": "ROC-AUC",
})
st.dataframe(display_df, use_container_width=True, hide_index=True)
st.plotly_chart(build_model_metrics_chart(metrics_df), use_container_width=True)

# ── 3. Importancia de variables — HERO VISUAL ─────────────────────────────────

st.markdown("### ¿Qué features explican la utilidad?")
st.caption(
    "El feature de mayor peso define qué acción concreta puede tomar un usuario para "
    "mejorar la utilidad de su reseña."
)

if not feature_imp_df.empty:
    # Ordenar y agregar anotaciones contextuales
    ordered = feature_imp_df.sort_values("importancia", ascending=False)

    feature_labels = {
        "review_len":       "Escribe más detalle — es el factor #1",
        "sentiment_score":  "El tono del texto importa, pero menos que la extensión",
        "incoherente":      "La incoherencia tono-estrellas penaliza la utilidad",
        "Score":            "Las estrellas aportan contexto al modelo",
    }

    import plotly.express as px
    ordered_asc = ordered.sort_values("importancia", ascending=True)
    fig_imp = px.bar(
        ordered_asc,
        x="importancia",
        y="feature",
        orientation="h",
        title="Importancia relativa de variables — LightGBM",
        template="plotly_white",
        color_discrete_sequence=["#1d4ed8"],
    )

    # Anotaciones directas en las barras
    for _, row in ordered.iterrows():
        label = feature_labels.get(row["feature"], "")
        if label:
            fig_imp.add_annotation(
                x=float(row["importancia"]) + 0.002,
                y=row["feature"],
                text=label,
                showarrow=False,
                xanchor="left",
                font=dict(size=11, color="#526277"),
            )

    fig_imp.update_layout(height=320, margin=dict(r=250))
    st.plotly_chart(fig_imp, use_container_width=True)

    # Interpretacion visual directa
    top_feature = ordered.iloc[0]["feature"] if len(ordered) > 0 else "review_len"
    top_pct     = float(ordered.iloc[0]["importancia"]) if len(ordered) > 0 else 0.0
    st.markdown(
        f"""
        <div class="insight-panel">
            <div class="insight-title">Lectura del modelo</div>
            <p>
                <strong>{top_feature}</strong> explica el {top_pct:.0%} de la importancia total.
                Una reseña larga con sentimiento coherente a las estrellas tiene alta probabilidad
                de ser útil — independientemente de si es positiva o negativa.
                Escribir al menos 80–100 palabras con detalle concreto es el cambio de mayor impacto.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info("No hay datos de importancia de variables disponibles.")

# ── 4. Curva ROC ──────────────────────────────────────────────────────────────

st.markdown("### Curva ROC")
st.caption(
    "Un clasificador perfecto tiene área = 1.0. La diagonal es el azar puro (AUC = 0.5). "
    "Cuanto más arriba y a la izquierda esté la curva, mejor discrimina el modelo."
)
st.plotly_chart(build_roc_chart(metrics_df, roc_curves), use_container_width=True)

# ── 5. Matriz de confusion ────────────────────────────────────────────────────

st.markdown(f"### Matriz de confusión — {best_name}")
st.caption(
    "Los **falsos negativos** (reseñas útiles clasificadas como no útiles) son el error más costoso: "
    "el sistema rechaza buenas reseñas. Los **falsos positivos** publican reseñas de baja calidad."
)
st.plotly_chart(
    build_confusion_matrix_chart(confusion_matrices.get(best_name), best_name),
    use_container_width=True,
)