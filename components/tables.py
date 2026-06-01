import pandas as pd
import streamlit as st


def render_dataframe(df: pd.DataFrame, height: int = 320) -> None:
    """Muestra dataframes con un estilo de uso consistente."""
    st.dataframe(df, use_container_width=True, height=height)
