"""Graficos para comparar modelos y metricas."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_model_metrics_chart(metrics_df: pd.DataFrame):
    """Barras agrupadas para comparar metricas entre modelos."""
    if metrics_df.empty:
        return px.bar(title="Comparacion de modelos")
    return px.bar(
        metrics_df,
        x="modelo",
        y=["precision", "recall", "f1", "roc_auc"],
        barmode="group",
        title="Comparacion de metricas por modelo",
        template="plotly_white",
    )


def build_roc_chart(metrics_df: pd.DataFrame, roc_curves: dict):
    """Construye curvas ROC reales si existen, con fallback simple."""
    if roc_curves:
        figure = go.Figure()
        for model_name, curve in roc_curves.items():
            figure.add_trace(
                go.Scatter(x=curve["fpr"], y=curve["tpr"], mode="lines", name=model_name)
            )
        figure.add_trace(
            go.Scatter(
                x=[0, 1], y=[0, 1], mode="lines", name="Azar",
                line={"dash": "dash", "color": "#94a3b8"},
            )
        )
        figure.update_layout(
            title="Curvas ROC comparativas",
            xaxis_title="False Positive Rate",
            yaxis_title="True Positive Rate",
            template="plotly_white",
        )
        return figure

    if metrics_df.empty or "modelo" not in metrics_df.columns or "roc_auc" not in metrics_df.columns:
        return px.line(title="Curva ROC")

    figure = go.Figure()
    for _, row in metrics_df.iterrows():
        auc_value    = float(row["roc_auc"])
        curve_height = max(0.55, min(0.95, auc_value))
        figure.add_trace(
            go.Scatter(
                x=[0.0, 0.15, 0.35, 0.6, 1.0],
                y=[0.0, curve_height * 0.55, curve_height * 0.78, curve_height * 0.92, 1.0],
                mode="lines",
                name=f"{row['modelo']} (AUC={auc_value:.3f})",
            )
        )

    figure.add_trace(
        go.Scatter(
            x=[0, 1], y=[0, 1], mode="lines", name="Azar (AUC=0.5)",
            line={"dash": "dash", "color": "#94a3b8"},
        )
    )
    figure.update_layout(
        title="Referencia visual ROC",
        xaxis_title="False Positive Rate",
        yaxis_title="True Positive Rate",
        template="plotly_white",
    )
    return figure


def build_feature_importance_chart(features_df: pd.DataFrame):
    """Grafico horizontal para importancia relativa de variables, con anotaciones de negocio."""
    if features_df.empty:
        return px.bar(title="Importancia de variables")

    ordered = features_df.sort_values(by="importancia", ascending=True)
    fig = px.bar(
        ordered,
        x="importancia",
        y="feature",
        orientation="h",
        title="Importancia relativa de variables",
        template="plotly_white",
        color_discrete_sequence=["#1d4ed8"],
    )

    feature_labels = {
        "review_len":       "Feature #1 — escribe más detalle",
        "sentiment_score":  "Tono del texto (VADER)",
        "incoherente":      "Penaliza incoherencia tono-estrellas",
        "Score":            "Calificación en estrellas",
    }

    for _, row in features_df.iterrows():
        label = feature_labels.get(row["feature"], "")
        if label:
            fig.add_annotation(
                x=float(row["importancia"]) + 0.003,
                y=row["feature"],
                text=label,
                showarrow=False,
                xanchor="left",
                font=dict(size=11, color="#526277"),
            )

    fig.update_layout(height=300, margin=dict(r=220))
    return fig


def build_confusion_matrix_chart(matrix, model_name: str):
    """Heatmap sencillo para visualizar errores por clase."""
    if matrix is None or len(matrix) == 0:
        return px.imshow([[0]], text_auto=True, title="Matriz de confusion")

    return px.imshow(
        matrix,
        text_auto=True,
        title=f"Matriz de confusion — {model_name}",
        x=["Pred. no útil", "Pred. útil"],
        y=["Real no útil", "Real útil"],
        color_continuous_scale="Blues",
    )