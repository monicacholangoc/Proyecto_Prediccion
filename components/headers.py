import streamlit as st


def render_app_hero(title: str, subtitle: str, tag: str) -> None:
    """Renderiza el bloque principal de bienvenida de la app."""
    st.markdown(
        f"""
        <div class="hero-panel">
            <span class="hero-tag">{tag}</span>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
