"""Modelos y evaluación."""
import plotly.express as px
import streamlit as st
from shared_sidebar import render_sidebar
from components.cards import render_metric_card
from plots.model_charts import build_confusion_matrix_chart, build_model_metrics_chart, build_roc_chart
from services.model_eval_service import compute_model_evaluation
from utils.formatters import format_percentage

with open("styles/styles.css", "r", encoding="utf-8") as _f:
    st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)
render_sidebar()

st.title("Modelos y Evaluación")
st.caption("Comparamos tres clasificadores para predecir si una reseña de Amazon será útil o no. Usamos métricas pensadas para datos desbalanceados (donde una clase es mucho más frecuente que la otra).")

evaluation         = compute_model_evaluation()
metrics_df         = evaluation["metrics"]
feature_imp_df     = evaluation["feature_importance"]
roc_curves         = evaluation["roc_curves"]
confusion_matrices = evaluation["confusion_matrices"]

if metrics_df.empty:
    st.warning("No fue posible calcular métricas."); st.stop()

best      = metrics_df.sort_values("roc_auc", ascending=False).iloc[0]
best_name = best["modelo"]

st.markdown(
    """<div class="accuracy-warning">
        <div class="aw-title">¿Por qué no usamos Accuracy (exactitud)?</div>
        <p>Con ~70 % de reseñas clasificadas como "no útiles", un modelo que <em>siempre</em> prediga "no útil"
        obtendría 70 % de Accuracy <strong>sin haber aprendido nada</strong>. Por eso usamos métricas más honestas:
        <strong>F1-Score</strong> (balance entre precisión y cobertura) y
        <strong>ROC-AUC</strong> (qué tan bien separa las dos clases), ambas válidas cuando las clases están desbalanceadas.</p>
    </div>""", unsafe_allow_html=True,
)

st.markdown('<div class="section-label">Comparación de modelos</div>', unsafe_allow_html=True)
for _, row in metrics_df.iterrows():
    is_best = str(row["modelo"]) == best_name
    mc1, mc2, mc3, mc4, mc5 = st.columns([2,1,1,1,1], gap="medium")
    with mc1:
        st.markdown(
            f"""<div class="metric-card" style="{'border:2px solid var(--primary);' if is_best else ''}">
                <div class="metric-label">Modelo</div>
                <div class="metric-value" style="font-size:1.1rem">{row['modelo']}</div>
                <span class="metric-badge {'metric-badge-good' if is_best else 'metric-badge-info'}">{'Modelo ganador' if is_best else 'Referencia'}</span>
            </div>""", unsafe_allow_html=True,
        )
    with mc2: render_metric_card("Precisión", f"{float(row['precision']):.1%}", "De cada 100 reseñas que el modelo dice que son útiles, ¿cuántas realmente lo son?")
    with mc3: render_metric_card("Recall (Cobertura)", f"{float(row['recall']):.1%}", "De todas las reseñas útiles reales, ¿cuántas logra detectar el modelo?")
    with mc4: render_metric_card("F1-Score", f"{float(row['f1']):.1%}", "Promedio balanceado entre Precisión y Cobertura. Más alto = mejor.")
    with mc5: render_metric_card("ROC-AUC", f"{float(row['roc_auc']):.1%}", "Capacidad general de separar reseñas útiles de no útiles. 100% = perfecto, 50% = azar.")

st.plotly_chart(build_model_metrics_chart(metrics_df), use_container_width=True)

st.markdown('<div class="section-label">¿Qué variables influyen más en la predicción?</div>', unsafe_allow_html=True)
st.caption("Importancia relativa de cada variable según el modelo LightGBM. Una variable con mayor importancia tiene más peso en la decisión del modelo.")
if not feature_imp_df.empty:
    ordered = feature_imp_df.sort_values("importancia", ascending=False)
    feature_labels = {
        "review_len":      "Escribe más detalle — factor #1",
        "sentiment_score": "El tono importa, pero menos que la extensión",
        "incoherente":     "La incoherencia penaliza la utilidad",
        "Score":           "Las estrellas aportan contexto",
    }
    feature_names = {
        "review_len":      "Longitud de la reseña",
        "sentiment_score": "Puntuación de sentimiento",
        "incoherente":     "Texto incoherente",
        "Score":           "Calificación (estrellas)",
    }
    fig_imp = px.bar(ordered.sort_values("importancia", ascending=True),
        x="importancia", y="feature", orientation="h",
        title="Importancia relativa de variables — Modelo LightGBM",
        labels={"importancia": "Importancia relativa", "feature": "Variable"},
        template="plotly_white",
        color_discrete_sequence=["#1d4ed8"])
    fig_imp.update_yaxes(ticktext=[feature_names.get(f, f) for f in ordered.sort_values("importancia", ascending=True)["feature"]], tickvals=list(ordered.sort_values("importancia", ascending=True)["feature"]))
    for _, row in ordered.iterrows():
        label = feature_labels.get(row["feature"], "")
        if label:
            fig_imp.add_annotation(x=float(row["importancia"])+0.002, y=row["feature"],
                text=label, showarrow=False, xanchor="left", font=dict(size=11, color="#526277"))
    fig_imp.update_layout(height=320, margin=dict(r=260))
    st.plotly_chart(fig_imp, use_container_width=True)

    imp_cols = st.columns(len(ordered), gap="medium")
    for col, (_, row) in zip(imp_cols, ordered.iterrows()):
        with col:
            render_metric_card(
                feature_names.get(str(row["feature"]), str(row["feature"])),
                f"{float(row['importancia']):.1%}",
                feature_labels.get(row["feature"], "")
            )
else:
    st.info("No hay datos de importancia disponibles.")

st.markdown('<div class="section-label">Curva ROC — ¿Qué tan bien separa los modelos las clases?</div>', unsafe_allow_html=True)
st.caption("La curva ROC muestra cómo varía la tasa de aciertos según el umbral de decisión. Un área (AUC) de 1.0 = clasificador perfecto. La línea diagonal punteada representa el azar puro (AUC = 0.5).")
st.plotly_chart(build_roc_chart(metrics_df, roc_curves), use_container_width=True)

st.markdown(f'<div class="section-label">Matriz de Confusión — {best_name}</div>', unsafe_allow_html=True)
st.caption("Muestra cuántas predicciones fueron correctas e incorrectas. Los **Falsos Negativos** (reseñas útiles clasificadas como no útiles) son el error más costoso, porque perdemos reseñas valiosas.")
st.plotly_chart(build_confusion_matrix_chart(confusion_matrices.get(best_name), best_name), use_container_width=True)