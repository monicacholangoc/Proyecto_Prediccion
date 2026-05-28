"""Tarjetas reutilizables para KPIs y metricas resumidas."""

import streamlit as st


def render_metric_card(label: str, value: str, caption: str) -> None:
    """Pinta una tarjeta simple con metrica principal y contexto."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_nav_card(title: str, description: str) -> None:
    """Resume una seccion clave de la app en la portada principal."""
    st.markdown(
        f"""
        <div class="nav-card">
            <div class="nav-card-title">{title}</div>
            <div class="nav-card-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_highlight_card(title: str, value: str, body: str) -> None:
    """Tarjeta para destacar un insight o estado puntual."""
    st.markdown(
        f"""
        <div class="highlight-card">
            <div class="highlight-title">{title}</div>
            <div class="highlight-value">{value}</div>
            <div class="highlight-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_review_card(
    user_name: str,
    stars: int,
    review_text: str,
    meta_line: str,
    badge: str,
    helpfulness: str,
    highlighted: bool = False,
) -> None:
    """Muestra una reseña en formato legible tipo plataforma de opiniones."""
    highlighted_class = " review-card-highlighted" if highlighted else ""
    stars_text = "★" * int(stars) + "☆" * max(0, 5 - int(stars))
    st.markdown(
        f"""
        <div class="review-card{highlighted_class}">
            <div class="review-card-header">
                <div class="review-user">{user_name}</div>
                <div class="review-badge">{badge}</div>
            </div>
            <div class="review-stars">{stars_text}</div>
            <div class="review-meta">{meta_line}</div>
            <div class="review-text">{review_text}</div>
            <div class="review-helpfulness">Utilidad estimada: {helpfulness}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
