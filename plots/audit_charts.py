"""Graficos orientados a la experiencia de auditoria en tiempo real."""

import plotly.graph_objects as go


def build_helpfulness_gauge(probability: float) -> go.Figure:
    """Construye un gauge para comunicar utilidad predicha — fondo transparente para panel oscuro."""
    pct = probability * 100
    # Color dinámico del arco según umbral
    bar_color = "#1D9E75" if pct >= 70 else ("#EF9F27" if pct >= 40 else "#E24B4A")

    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=pct,
            number={
                "suffix": "%",
                "font": {"size": 38, "color": "#f8fafc", "family": "Inter, sans-serif"},
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickcolor": "rgba(248,250,252,0.3)",
                    "tickfont": {"color": "rgba(248,250,252,0.4)", "size": 10},
                },
                "bar": {"color": bar_color, "thickness": 0.65},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0,  40], "color": "rgba(226,75,74,0.15)"},
                    {"range": [40, 70], "color": "rgba(239,159,39,0.15)"},
                    {"range": [70,100], "color": "rgba(29,158,117,0.15)"},
                ],
                "threshold": {
                    "line": {"color": "rgba(248,250,252,0.4)", "width": 2},
                    "thickness": 0.75,
                    "value": 70,
                },
            },
        )
    )
    figure.update_layout(
        margin=dict(l=16, r=16, t=40, b=10),
        height=200,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "rgba(248,250,252,0.5)"},
    )
    return figure