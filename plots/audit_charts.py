"""Graficos orientados a la experiencia de auditoria en tiempo real."""

import plotly.graph_objects as go


def build_helpfulness_gauge(probability: float) -> go.Figure:
    """Construye un gauge simple para comunicar utilidad predicha."""
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=probability * 100,
            number={"suffix": "%"},
            title={"text": "Probabilidad de utilidad"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#1d4ed8"},
                "steps": [
                    {"range": [0, 40], "color": "#fee2e2"},
                    {"range": [40, 70], "color": "#fef3c7"},
                    {"range": [70, 100], "color": "#dcfce7"},
                ],
            },
        )
    )
    figure.update_layout(margin=dict(l=20, r=20, t=60, b=20), height=320)
    return figure
