"""Comparación de modelos y métricas del proyecto.

Cubre el requisito del caso de:
- Comparar Logistic Regression vs LightGBM
- Justificar por qué no se usa Accuracy
- Interpretar la importancia de features en lenguaje natural
- Mostrar curva ROC y matriz de confusión
"""

import pandas as pd
import streamlit as st

from components.cards import render_highlight_card, render_metric_card
from plots.model_charts import (
    build_confusion_matrix_chart,
    build_feature_importance_chart,
    build_model_metrics_chart,
    build_roc_chart,
)
from services.model_eval_service import compute_model_evaluation
from utils.formatters import format_percentage


st.title("Modelos y Evaluación")
st.caption("Comparación de clasificadores, justificación de métricas e interpretación de resultados.")

# ── Carga de resultados ───────────────────────────────────────────────────────

evaluation = compute_model_evaluation()
metrics_df = evaluation["metrics"]
feature_importance_df = evaluation["feature_importance"]
roc_curves = evaluation["roc_curves"]
confusion_matrices = evaluation["confusion_matrices"]

if metrics_df.empty:
    st.warning(
        "No fue posible calcular métricas reales. "
        "Verifica que el parquet procesado tenga las columnas esperadas."
    )
    st.stop()

best_model = metrics_df.sort_values(by="roc_auc", ascending=False).iloc[0]
best_model_name = best_model["modelo"]

# ── Por qué no usamos Accuracy ────────────────────────────────────────────────

st.markdown(
    """
    <div class="accuracy-warning">
        <div class="aw-title">¿Por qué no usamos Accuracy como métrica principal?</div>
        <p>
            Las reseñas con ≥ 5 votos están desbalanceadas: la mayoría son "no útiles".
            Un modelo que siempre prediga "no útil" tendría alta accuracy sin aprender nada útil.
            Usamos <strong>F1-Score</strong> para balancear precisión y recall, y
            <strong>ROC-AUC</strong> para medir la capacidad discriminativa general.
            Así evaluamos si el modelo realmente distingue reseñas útiles de las que no lo son.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Métricas resumen ──────────────────────────────────────────────────────────

st.markdown("### Resultado de la Comparación")
metric_cols = st.columns(4, gap="medium")
with metric_cols[0]:
    render_metric_card(
        "Modelo ganador",
        best_model["modelo"],
        "Mayor ROC-AUC en el split de prueba (20 %)",
    )
with metric_cols[1]:
    render_metric_card(
        "ROC-AUC del ganador",
        format_percentage(float(best_model["roc_auc"])),
        "Qué tan bien separa útiles de no útiles",
    )
with metric_cols[2]:
    render_metric_card(
        "F1-Score del ganador",
        format_percentage(float(best_model["f1"])),
        "Balance entre precisión y recall",
    )
with metric_cols[3]:
    render_metric_card(
        "Baseline comparado",
        "Regresión Logística",
        "Modelo interpretable de referencia del caso",
    )

# ── Tabla comparativa ─────────────────────────────────────────────────────────

st.markdown("### Tabla Comparativa de Métricas")
st.caption("Todas las métricas calculadas sobre el 20 % de datos de prueba con split reproducible (random_state=42).")

display_df = metrics_df.copy()
for col in ["precision", "recall", "f1", "roc_auc"]:
    if col in display_df.columns:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.4f}")

display_df = display_df.rename(columns={
    "modelo": "Modelo",
    "precision": "Precisión",
    "recall": "Recall",
    "f1": "F1-Score",
    "roc_auc": "ROC-AUC",
})
st.dataframe(display_df, use_container_width=True, hide_index=True)
st.plotly_chart(build_model_metrics_chart(metrics_df), use_container_width=True)

# ── Curva ROC e importancia ───────────────────────────────────────────────────

st.markdown("### Curva ROC e Importancia de Variables")
chart_left, chart_right = st.columns(2, gap="large")
with chart_left:
    st.caption("La curva ROC muestra qué tan bien cada modelo distingue entre clases. Más área = mejor.")
    st.plotly_chart(build_roc_chart(metrics_df, roc_curves), use_container_width=True)
with chart_right:
    st.caption("Las variables más importantes según el modelo LightGBM entrenado.")
    st.plotly_chart(build_feature_importance_chart(feature_importance_df), use_container_width=True)

# ── Interpretación en lenguaje natural ───────────────────────────────────────

st.markdown("### Interpretación de los Resultados")
st.caption("¿Qué nos dice el modelo sobre qué hace útil a una reseña?")

i1, i2, i3 = st.columns(3, gap="medium")
with i1:
    st.markdown(
        """
        <div class="insight-panel">
            <div class="insight-title">Feature más importante: longitud</div>
            <p>
                Las reseñas más largas tienen mayor probabilidad de ser percibidas como útiles.
                Escribir más detalle — experiencia de uso, sabor, empaque, comparaciones —
                aumenta directamente la utilidad predicha.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with i2:
    st.markdown(
        """
        <div class="insight-panel">
            <div class="insight-title">Coherencia entre nota y texto</div>
            <p>
                Una reseña con texto positivo y 1–2 estrellas (o texto negativo con 5 estrellas)
                activa el flag de incoherencia y reduce la probabilidad de utilidad.
                Los compradores confían más en reseñas coherentes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with i3:
    st.markdown(
        """
        <div class="insight-panel">
            <div class="insight-title">Sentimiento: útil pero secundario</div>
            <p>
                El score de sentimiento VADER contribuye al modelo, pero con menor peso que
                la longitud. Una reseña entusiasta sin detalle concreto no supera a una
                reseña neutra y bien argumentada.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Consejo concreto ──────────────────────────────────────────────────────────

st.markdown("### Consejo para Escribir una Reseña Más Útil")
c1, c2 = st.columns(2, gap="large")
with c1:
    render_highlight_card(
        "Lo que sí funciona",
        "Reseñas largas y coherentes",
        "Escribe al menos 80–100 palabras. Menciona el sabor, el empaque, "
        "la frecuencia de uso y si lo recomendarías. Asegúrate de que tu nota "
        "coincida con el tono del texto.",
    )
with c2:
    render_highlight_card(
        "Lo que no funciona",
        "Reseñas cortas o incoherentes",
        "\"Muy rico!\" con 5 estrellas tiene baja probabilidad de ser útil. "
        "Una nota de 1 estrella con texto entusiasta tampoco. La coherencia "
        "y el detalle son lo que otros compradores valoran.",
    )

# ── Matriz de confusión ───────────────────────────────────────────────────────

st.markdown("### Matriz de Confusión — Modelo Principal")
st.caption(
    f"Muestra cuántas predicciones del modelo {best_model_name} fueron correctas e incorrectas "
    "en el conjunto de prueba. Los errores más costosos son los falsos negativos "
    "(reseñas útiles clasificadas como no útiles)."
)
st.plotly_chart(
    build_confusion_matrix_chart(confusion_matrices.get(best_model_name), best_model_name),
    use_container_width=True,
)