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
            Seminario Predictivo 2026 · Caso 06
        </div>
        <div style="font-size:clamp(1.4rem,3vw,1.9rem);font-weight:800;
                    letter-spacing:-0.02em;line-height:1.2;margin-bottom:0.3rem">
            Modelos y Evaluación
        </div>
        <div style="font-size:0.82rem;color:rgba(255,255,255,0.65)">Comparación de clasificadores · Métricas para datos desbalanceados · Importancia de variables</div>
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
    st.warning("No fue posible calcular métricas."); st.stop()

best      = metrics_df.sort_values("roc_auc", ascending=False).iloc[0]
best_name = best["modelo"]

import plotly.graph_objects as go

st.markdown('<div class="section-label">Comparación de modelos</div>', unsafe_allow_html=True)

MODEL_CONFIG = {
    "Logistic Regression": {"color": "#1d4ed8", "icon": "📐"},
    "LightGBM":            {"color": "#15803d", "icon": "⚡"},
    "XGBoost":             {"color": "#b45309", "icon": "🚀"},
    "CatBoost":            {"color": "#7c3aed", "icon": "🐱"},
}

cols = st.columns(len(metrics_df), gap="medium")
for col, (_, row) in zip(cols, metrics_df.iterrows()):
    model_name = str(row["modelo"])
    is_best    = model_name == best_name
    cfg        = MODEL_CONFIG.get(model_name, {"color": "#64748b", "icon": "🤖"})
    color      = cfg["color"]
    icon       = cfg["icon"]
    prec, rec, f1, auc = float(row["precision"]), float(row["recall"]), float(row["f1"]), float(row["roc_auc"])

    def bar(val, c):
        pct = int(val * 100)
        return (f'<div style="margin:0.25rem 0 0.1rem">'
                f'<div style="background:#e2e8f0;border-radius:999px;height:5px;overflow:hidden">'
                f'<div style="width:{pct}%;height:100%;background:{c};border-radius:999px"></div>'
                f'</div></div>')

    winner = (f'<div style="background:{color};color:#fff;font-size:0.6rem;font-weight:800;'
              f'padding:0.2rem 0.5rem;border-radius:999px;display:inline-block;margin-bottom:0.4rem">'
              f'Seleccionado</div>' if is_best else
              f'<div style="background:#f1f5f9;color:#64748b;font-size:0.6rem;font-weight:700;'
              f'padding:0.2rem 0.5rem;border-radius:999px;display:inline-block;margin-bottom:0.4rem">'
              f'Referencia</div>')

    with col:
        st.markdown(
            f'''<div style="background:{"linear-gradient(135deg,"+color+"12,#fff)" if is_best else "#fff"};
                border:{"2px solid "+color if is_best else "1px solid #e2e8f0"};
                border-radius:16px;padding:1rem 0.9rem;
                box-shadow:{"0 4px 20px "+color+"30" if is_best else "0 1px 4px rgba(0,0,0,0.06)"}">
                <div style="font-size:1.5rem;margin-bottom:0.2rem">{icon}</div>
                {winner}
                <div style="font-size:0.9rem;font-weight:800;color:#0f172a;margin-bottom:0.6rem">{model_name}</div>
                <div style="font-size:0.62rem;font-weight:700;color:#94a3b8;text-transform:uppercase">Precisión {prec:.1%}</div>{bar(prec,color)}
                <div style="font-size:0.62rem;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-top:0.3rem">Recall {rec:.1%}</div>{bar(rec,color)}
                <div style="font-size:0.62rem;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-top:0.3rem">F1-Score {f1:.1%}</div>{bar(f1,color)}
                <div style="font-size:0.62rem;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-top:0.3rem">ROC-AUC {auc:.1%}</div>{bar(auc,color)}
                <div style="margin-top:0.7rem;padding-top:0.6rem;border-top:1px solid #f1f5f9;
                            display:grid;grid-template-columns:1fr 1fr;gap:0.3rem;text-align:center">
                    <div><div style="font-size:1rem;font-weight:800;color:{color}">{f1:.1%}</div>
                         <div style="font-size:0.55rem;color:#94a3b8">F1</div></div>
                    <div><div style="font-size:1rem;font-weight:800;color:{color}">{auc:.1%}</div>
                         <div style="font-size:0.55rem;color:#94a3b8">ROC-AUC</div></div>
                </div>
            </div>''',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ── Radar comparativo ─────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Radar comparativo — los 4 modelos</div>', unsafe_allow_html=True)
categories  = ["Precisión", "Recall", "F1-Score", "ROC-AUC"]
metric_keys = ["precision", "recall", "f1", "roc_auc"]
fig_radar   = go.Figure()
for _, row in metrics_df.iterrows():
    model_name = str(row["modelo"])
    cfg        = MODEL_CONFIG.get(model_name, {"color": "#64748b"})
    vals       = [float(row[k]) for k in metric_keys]
    fig_radar.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], theta=categories + [categories[0]],
        fill="toself", name=model_name,
        line=dict(color=cfg["color"], width=2.5),
        fillcolor=cfg["color"], opacity=0.15,
        marker=dict(size=6, color=cfg["color"]),
    ))
fig_radar.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, range=[0.7, 1.0], tickformat=".0%",
                        gridcolor="#e2e8f0", tickfont=dict(size=9)),
        angularaxis=dict(gridcolor="#e2e8f0", tickfont=dict(size=11, color="#475569")),
        bgcolor="rgba(0,0,0,0)",
    ),
    showlegend=True,
    legend=dict(orientation="h", y=-0.18, font=dict(size=11)),
    height=400, margin=dict(l=40, r=40, t=20, b=60),
    paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_radar, use_container_width=True)

st.markdown(
    """<div class="accuracy-warning">
        <div class="aw-title">¿Por qué no usamos Accuracy (exactitud)?</div>
        <p>Con ~70 % de reseñas clasificadas como "no útiles", un modelo que <em>siempre</em> prediga "no útil"
        obtendría 70 % de Accuracy <strong>sin haber aprendido nada</strong>. Por eso usamos métricas más honestas:
        <strong>F1-Score</strong> (balance entre precisión y cobertura) y
        <strong>ROC-AUC</strong> (qué tan bien separa las dos clases), ambas válidas cuando las clases están desbalanceadas.</p>
    </div>""", unsafe_allow_html=True,
)

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

    st.markdown(
        """<div class="insight-panel">
            <div class="insight-title">Interpretación del modelo</div>
            <p>Las reseñas largas con sentimiento coherente con las estrellas son consistentemente más útiles.
            La longitud de la reseña es el predictor dominante: aporta más del doble del peso que el sentimiento.
            La incoherencia entre tono y calificación actúa como penalizador. La calificación en estrellas
            sola no es suficiente para predecir utilidad — confirma que el texto es lo que realmente importa.</p>
        </div>""", unsafe_allow_html=True,
    )

    total_imp = ordered["importancia"].sum()
    imp_cols = st.columns(len(ordered), gap="medium")
    for col, (_, row) in zip(imp_cols, ordered.iterrows()):
        with col:
            pct = float(row["importancia"]) / total_imp if total_imp > 0 else 0
            render_metric_card(
                feature_names.get(str(row["feature"]), str(row["feature"])),
                f"{pct:.1%}",
                feature_labels.get(row["feature"], "")
            )
else:
    st.info("No hay datos de importancia disponibles.")

st.markdown('<div class="section-label">Curva ROC — ¿Qué tan bien separa los modelos las clases?</div>', unsafe_allow_html=True)
st.caption("La curva ROC muestra cómo varía la tasa de aciertos según el umbral de decisión. Un área (AUC) de 1.0 = clasificador perfecto. La línea diagonal punteada representa el azar puro (AUC = 0.5).")
st.plotly_chart(build_roc_chart(metrics_df, roc_curves), use_container_width=True)

st.markdown(f'<div class="section-label">Matriz de Confusión — {best_name}</div>', unsafe_allow_html=True)
st.caption("Cada celda muestra cuántas reseñas clasificó el modelo. La diagonal principal (↘) son los aciertos. Los **Falsos Negativos** (reseñas útiles clasificadas como no útiles) son el error más costoso: el modelo pierde contenido de valor que nunca llega a los compradores.")
st.plotly_chart(build_confusion_matrix_chart(confusion_matrices.get(best_name), best_name), use_container_width=True)