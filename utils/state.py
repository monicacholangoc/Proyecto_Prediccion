"""Helpers para inicializar y centralizar session state.

La idea es evitar claves sueltas repartidas por todas las paginas.
"""

import pandas as pd
import streamlit as st

from config.constants import DEFAULT_METRICS


def initialize_state() -> None:
    """Declara las claves compartidas que usa la aplicacion."""
    st.session_state.setdefault("app_initialized", True)
    st.session_state.setdefault("selected_product_id", None)
    st.session_state.setdefault("latest_audit_result", None)
    st.session_state.setdefault("latest_review_text", "")
    st.session_state.setdefault("latest_stars", 5)
    st.session_state.setdefault("global_metrics", DEFAULT_METRICS.copy())
    st.session_state.setdefault("audit_history", pd.DataFrame())
    st.session_state.setdefault("db_central_corporativa", None)
