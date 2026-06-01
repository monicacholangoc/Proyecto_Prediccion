import pandas as pd
import streamlit as st

from config.settings import AUDITED_REVIEWS_PATH, DATA_GENERATED_DIR, PRODUCT_CONTEXT_PATH, REPORTS_DIR, REVIEWS_PROCESSED_PATH


@st.cache_data(show_spinner=False)
def load_processed_reviews() -> pd.DataFrame:
    """Carga el parquet procesado principal del proyecto."""
    if REVIEWS_PROCESSED_PATH.exists():
        return pd.read_parquet(REVIEWS_PROCESSED_PATH)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_product_context() -> pd.DataFrame:
    """Carga el contexto de productos y topicos entrenados."""
    if PRODUCT_CONTEXT_PATH.exists():
        return pd.read_parquet(PRODUCT_CONTEXT_PATH)
    return pd.DataFrame()


def read_uploaded_csv(uploaded_file) -> pd.DataFrame:
    """Lee un CSV subido por el usuario desde Streamlit."""
    if uploaded_file is None:
        return pd.DataFrame()
    return pd.read_csv(uploaded_file)


def ensure_generated_data_dirs() -> None:
    """Crea carpetas operativas para datos generados por la app."""
    DATA_GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@st.cache_data(show_spinner=False)
def load_audited_reviews_file() -> pd.DataFrame:
    """Carga el CSV operativo de reseñas auditadas si existe."""
    ensure_generated_data_dirs()
    if AUDITED_REVIEWS_PATH.exists():
        return pd.read_csv(AUDITED_REVIEWS_PATH)
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_reviews_with_category() -> pd.DataFrame:
    """Carga las reseñas enriquecidas con categoria de alimento."""
    path = REVIEWS_PROCESSED_PATH.parent / "reviews_con_categoria.parquet"
    if path.exists():
        return pd.read_parquet(path)
    # Fallback: carga las reviews normales sin categoria
    return load_processed_reviews()