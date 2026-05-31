"""Modelos y evaluaciÃ³n."""
# â”€â”€ Guard: redirige a main.py si se accede directamente sin sesiÃ³n â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    import streamlit as _st
    if not _st.session_state.get("app_initialized"):
        _st.switch_page("main.py")
except Exception:
    pass
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


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
            Seminario Predictivo 2026 Â· Caso 06
        </div>
        <div style="font-size:clamp(1.4rem,3vw,1.9rem);font-weight:800;
                    letter-spacing:-0.02em;line-height:1.2;margin-bottom:0.3rem">
            Modelos y EvaluaciÃ³n
        </div>
        <div style="font-size:0.82rem;color:rgba(255,255,255,0.65)">ComparaciÃ³n de clasificadores Â· MÃ©tricas para datos desbalanceados</div>
    </div>
    """,
    unsafe_allow_html=True,
)


evaluation         = compute_model_evaluation()
metrics_df         = evaluation["metrics"]
feature_imp_df     = evaluation["feature_importance"]
roc_curves         = evaluation["roc_curves"]
confusion_matrices = evaluation["confusion_matrices"]

if metrics_df.empty:
    st.warning("No fue posible calcular mÃ©tricas."); st.stop()

best      = metrics_df.sort_values("roc_auc", ascending=False).iloc[0]
best_name = best["modelo"]

st.markdown(
    """<div class="accuracy-warning">
        <div class="aw-title">Por quÃ© no se usa Accuracy</div>
        <p>Con ~70 % de reseÃ±as "no Ãºtiles", un modelo que prediga siempre "no Ãºtil" alcanzarÃ­a ~70 % de Accuracy
        <strong>sin aprender nada</strong>. Se usan <strong>F1-Score</strong> y <strong>ROC-AUC</strong>,
        vÃ¡lidos con clases desbalanceadas.</p>
    </div>""", unsafe_allow_html=True,
)

st.markdown('<div class="section-label">ComparaciÃ³n de modelos</div>', unsafe_allow_html=True)
for _, row in metrics_df.iterrows():
    is_best = str(row["modelo"]) == best_name
    mc1, mc2, mc3, mc4, mc5 = st.columns([2,1,1,1,1], gap="medium")
    with mc1:
        st.markdown(
            f"""<div class="metric-card" style="{'border:2px solid var(--primary);' if is_best else ''}">
                <div class="metric-label">Modelo</div>
                <div class="metric-value" style="font-size:1.1rem">{row['modelo']}</div>
                <span class="metric-badge {'metric-badge-good' if is_best else 'metric-badge-info'}">{'Modelo ganador' if is_best else 'Baseline'}</span>
            </div>""", unsafe_allow_html=True,
        )
    with mc2: render_metric_card("PrecisiÃ³n", f"{float(row['precision']):.4f}", "TP / (TP + FP)")
    with mc3: render_metric_card("Recall",    f"{float(row['recall']):.4f}",    "TP / (TP + FN)")
    with mc4: render_metric_card("F1-Score",  f"{float(row['f1']):.4f}",        "PrecisiÃ³n + Recall")
    with mc5: render_metric_card("ROC-AUC",   f"{float(row['roc_auc']):.4f}",   "Capacidad discriminativa")

st.plotly_chart(build_model_metrics_chart(metrics_df), use_container_width=True)

st.markdown('<div class="section-label">Importancia de variables</div>', unsafe_allow_html=True)
if not feature_imp_df.empty:
    ordered = feature_imp_df.sort_values("importancia", ascending=False)
    feature_labels = {
        "review_len":      "Escribe mÃ¡s detalle â€” factor #1",
        "sentiment_score": "El tono importa, pero menos que la extensiÃ³n",
        "incoherente":     "La incoherencia penaliza la utilidad",
        "Score":           "Las estrellas aportan contexto",
    }
    fig_imp = px.bar(ordered.sort_values("importancia", ascending=True),
        x="importancia", y="feature", orientation="h",
        title="Importancia relativa â€” LightGBM", template="plotly_white",
        color_discrete_sequence=["#1d4ed8"])
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
            render_metric_card(str(row["feature"]), f"{float(row['importancia']):.0f}", feature_labels.get(row["feature"], ""))
else:
    st.info("No hay datos de importancia disponibles.")

st.markdown('<div class="section-label">Curva ROC</div>', unsafe_allow_html=True)
st.caption("Ãrea = 1.0 es el clasificador perfecto. La diagonal es el azar puro (AUC = 0.5).")
st.plotly_chart(build_roc_chart(metrics_df, roc_curves), use_container_width=True)

st.markdown(f'<div class="section-label">Matriz de confusiÃ³n â€” {best_name}</div>', unsafe_allow_html=True)
st.caption("Los falsos negativos (Ãºtiles clasificadas como no Ãºtiles) son el error mÃ¡s costoso.")
st.plotly_chart(build_confusion_matrix_chart(confusion_matrices.get(best_name), best_name), use_container_width=True)
