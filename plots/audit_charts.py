import plotly.graph_objects as go


def build_helpfulness_gauge(probability: float) -> go.Figure:
    """Gauge de utilidad — colores vivos, legible sobre fondo claro."""
    pct = probability * 100
    bar_color = "#22c55e" if pct >= 70 else ("#f59e0b" if pct >= 40 else "#f87171")

    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=pct,
            number={
                "suffix": "%",
                "font": {"size": 42, "color": "#0f172a", "family": "Inter, sans-serif"},
                "valueformat": ".1f",
            },
            title={
                "text": "Probabilidad de utilidad",
                "font": {"size": 13, "color": "#64748b"},
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickcolor": "#cbd5e1",
                    "tickfont": {"color": "#94a3b8", "size": 10},
                    "tickwidth": 1,
                },
                "bar": {"color": bar_color, "thickness": 0.7},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0,  40], "color": "#fee2e2"},
                    {"range": [40, 70], "color": "#fef9c3"},
                    {"range": [70,100], "color": "#dcfce7"},
                ],
                "threshold": {
                    "line": {"color": "#475569", "width": 2},
                    "thickness": 0.8,
                    "value": 70,
                },
            },
        )
    )
    figure.update_layout(
        margin=dict(l=20, r=20, t=50, b=10),
        height=240,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#64748b"},
    )
    return figure