"""Pagina inicial para comparar modelos y metricas.

En esta etapa aun muestra una estructura base, pero ya esta separada
de la logica de entrenamiento e inferencia.
"""

import pandas as pd
import streamlit as st

from components.cards import render_highlight_card, render_metric_card
from components.feedback import render_bullet_panel, render_info_panel
from plots.model_charts import (
    build_confusion_matrix_chart,
    build_feature_importance_chart,
    build_model_metrics_chart,
    build_roc_chart,
)
from services.model_eval_service import compute_model_evaluation
from utils.formatters import format_percentage


st.title("Modelos y Evaluación")
st.caption("Comparación de clasificadores, lectura de métricas y justificación del modelo principal.")

evaluation = compute_model_evaluation()
metrics_df = evaluation["metrics"]
feature_importance_df = evaluation["feature_importance"]
roc_curves = evaluation["roc_curves"]
confusion_matrices = evaluation["confusion_matrices"]

if metrics_df.empty:
    st.warning("No fue posible calcular métricas reales todavía. Revisa que el parquet procesado tenga las columnas esperadas.")
    st.stop()

best_model = metrics_df.sort_values(by="roc_auc", ascending=False).iloc[0]
best_model_name = best_model["modelo"]

metric_cols = st.columns(4, gap="medium")
with metric_cols[0]:
    render_metric_card("Modelo líder", best_model["modelo"], "Mayor ROC-AUC en la comparación actual")
with metric_cols[1]:
    render_metric_card("ROC-AUC líder", format_percentage(float(best_model["roc_auc"])), "Capacidad global de discriminación")
with metric_cols[2]:
    render_metric_card("F1 líder", format_percentage(float(best_model["f1"])), "Balance entre precision y recall")
with metric_cols[3]:
    render_metric_card("Baseline", "Logistic Regression", "Referencia interpretable del proyecto")

hero_left, hero_right = st.columns([1.2, 0.8], gap="large")
with hero_left:
    st.markdown(
        """
        <div class="section-panel">
            <div class="section-kicker">Lectura técnica</div>
            <h3>Cómo se interpreta esta comparación de modelos</h3>
            <p>
                Esta sección busca justificar por qué el modelo principal no se elige
                solo por intuición, sino por desempeño comparado y por utilidad de negocio.
            </p>
            <p>
                El baseline aporta interpretabilidad. El modelo principal aporta una mejor
                capacidad de discriminación sobre reseñas útiles y no útiles.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hero_right:
    render_highlight_card(
        "Modelo principal",
        best_model["modelo"],
        "Actualmente se prioriza por su mejor equilibrio entre discriminación y capacidad predictiva.",
    )
    render_highlight_card(
        "Criterio de negocio",
        "No usar accuracy sola",
        "El problema requiere métricas más finas por el posible desbalance entre clases útiles y no útiles.",
    )

st.markdown("### Comparación de Métricas")
st.dataframe(metrics_df, use_container_width=True, hide_index=True)
st.plotly_chart(build_model_metrics_chart(metrics_df), use_container_width=True)

chart_left, chart_right = st.columns(2, gap="large")
with chart_left:
    st.plotly_chart(build_roc_chart(metrics_df, roc_curves), use_container_width=True)
with chart_right:
    st.plotly_chart(build_feature_importance_chart(feature_importance_df), use_container_width=True)

st.plotly_chart(
    build_confusion_matrix_chart(confusion_matrices.get(best_model_name), best_model_name),
    use_container_width=True,
)

insight_left, insight_right = st.columns(2, gap="large")
with insight_left:
    render_bullet_panel(
        "Qué defender aquí",
        [
            "El baseline sirve para entender la dirección de las variables.",
            "El modelo principal captura relaciones no lineales con mejor desempeño.",
            "ROC-AUC y F1 ayudan más que accuracy para evaluar este caso.",
        ],
    )
with insight_right:
    render_bullet_panel(
        "Lectura de variables",
        [
            "La longitud de la reseña aparece como señal dominante.",
            "El sentimiento y la coherencia complementan el valor predictivo.",
            "La calificación ayuda, pero no explica sola la utilidad percibida.",
        ],
    )

render_info_panel(
    "Lectura de esta fase",
    "La página ya está conectada a una evaluación reproducible sobre el parquet limpio. "
    "Esto permite justificar la elección del modelo con métricas reales, ROC y matriz de confusión.",
)
