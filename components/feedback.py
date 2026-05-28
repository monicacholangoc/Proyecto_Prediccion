"""Paneles de texto explicativo y retroalimentacion visual."""

import streamlit as st


def render_info_panel(title: str, body: str) -> None:
    """Renderiza una tarjeta informativa para contexto o diagnostico."""
    st.markdown(
        f"""
        <div class="info-panel">
            <strong>{title}</strong>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bullet_panel(title: str, items: list[str]) -> None:
    """Muestra una lista corta de hallazgos o siguientes pasos."""
    bullet_items = "".join(f"<li>{item}</li>" for item in items)
    st.markdown(
        f"""
        <div class="info-panel">
            <strong>{title}</strong>
            <ul class="info-list">{bullet_items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_panel(title: str, status: str, body: str, tone: str = "info") -> None:
    """Panel destacado para mostrar decisiones o estados operativos."""
    st.markdown(
        f"""
        <div class="status-panel status-{tone}">
            <div class="status-title">{title}</div>
            <div class="status-label">{status}</div>
            <div class="status-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
