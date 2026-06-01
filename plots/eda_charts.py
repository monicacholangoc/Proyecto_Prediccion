import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


def build_stars_distribution(df: pd.DataFrame):
    """Histograma de calificaciones."""
    if df.empty or "Score" not in df.columns:
        return px.bar(title="Distribucion de calificaciones")
    return px.histogram(
        df,
        x="Score",
        color="Score",
        title="Distribucion de calificaciones",
        template="plotly_white",
    )


def build_review_length_distribution(df: pd.DataFrame):
    """Histograma de longitud de reseñas."""
    if df.empty or "review_len" not in df.columns:
        return px.bar(title="Distribucion de longitud de resenas")
    return px.histogram(
        df,
        x="review_len",
        nbins=30,
        title="Distribucion de longitud de resenas",
        template="plotly_white",
        color_discrete_sequence=["#1d4ed8"],
    )


def build_helpfulness_distribution(df: pd.DataFrame):
    """Distribucion de utilidad observada o estimada."""
    helpfulness_column = None
    for candidate in ["Helpfulness", "helpfulness_ratio"]:
        if candidate in df.columns:
            helpfulness_column = candidate
            break

    if df.empty or helpfulness_column is None:
        return px.bar(title="Distribucion de utilidad")

    return px.histogram(
        df,
        x=helpfulness_column,
        nbins=25,
        title="Distribucion de utilidad",
        template="plotly_white",
        color_discrete_sequence=["#059669"],
    )


def build_stars_vs_helpfulness(df: pd.DataFrame):
    """Relacion entre estrellas y utilidad estimada."""
    score_column = "Score" if "Score" in df.columns else "Stars" if "Stars" in df.columns else None
    helpfulness_column = "Helpfulness" if "Helpfulness" in df.columns else "helpfulness_ratio" if "helpfulness_ratio" in df.columns else None

    if df.empty or score_column is None or helpfulness_column is None:
        return px.scatter(title="Estrellas vs utilidad")

    return px.box(
        df,
        x=score_column,
        y=helpfulness_column,
        color=score_column,
        title="Utilidad por calificacion",
        template="plotly_white",
    )


def build_length_vs_helpfulness(df: pd.DataFrame):
    """Dispersion entre longitud textual y utilidad."""
    score_column = "Score" if "Score" in df.columns else "Stars" if "Stars" in df.columns else None
    helpfulness_column = "Helpfulness" if "Helpfulness" in df.columns else "helpfulness_ratio" if "helpfulness_ratio" in df.columns else None

    if df.empty or "review_len" not in df.columns or helpfulness_column is None:
        return px.scatter(title="Longitud vs utilidad")

    return px.scatter(
        df,
        x="review_len",
        y=helpfulness_column,
        color=score_column if score_column else None,
        title="Longitud vs utilidad",
        template="plotly_white",
        opacity=0.75,
    )


def build_category_distribution(df: pd.DataFrame):
    """Volumen por categoria del catalogo."""
    if df.empty or "Categoria_Real" not in df.columns:
        return px.bar(title="Distribucion por categoria")

    category_counts = (
        df["Categoria_Real"]
        .fillna("Alimentos generales")
        .value_counts()
        .reset_index()
    )
    category_counts.columns = ["Categoria_Real", "conteo"]

    return px.bar(
        category_counts,
        x="conteo",
        y="Categoria_Real",
        orientation="h",
        title="Volumen por categoria",
        template="plotly_white",
        color_discrete_sequence=["#0f4c5c"],
    )


def build_metric_summary_bar(summary_items: list[tuple[str, float]]):
    """Grafico compacto para resumir indicadores del EDA."""
    if not summary_items:
        return px.bar(title="Resumen de indicadores")

    summary_df = pd.DataFrame(summary_items, columns=["indicador", "valor"])
    return px.bar(
        summary_df,
        x="indicador",
        y="valor",
        title="Resumen visual de indicadores",
        template="plotly_white",
        color="indicador",
    )


def build_target_balance(df: pd.DataFrame):
    """Balance de la variable objetivo útil / no útil."""
    if df.empty or "y_util" not in df.columns:
        return px.bar(title="Balance de la variable objetivo")

    target_df = (
        df["y_util"]
        .map({1: "Util", 0: "No util"})
        .fillna("No clasificado")
        .value_counts()
        .reset_index()
    )
    target_df.columns = ["clase", "conteo"]
    return px.bar(
        target_df,
        x="clase",
        y="conteo",
        color="clase",
        title="Balance de la variable objetivo",
        template="plotly_white",
    )


def build_sentiment_distribution(df: pd.DataFrame):
    """Distribucion del sentimiento VADER."""
    if df.empty or "sentiment_score" not in df.columns:
        return px.bar(title="Distribucion de sentimiento")

    return px.histogram(
        df,
        x="sentiment_score",
        nbins=30,
        title="Distribucion de sentimiento",
        template="plotly_white",
        color_discrete_sequence=["#f59e0b"],
    )


def build_incoherence_distribution(df: pd.DataFrame):
    """Conteo de reseñas coherentes e incoherentes."""
    if df.empty or "incoherente" not in df.columns:
        return px.bar(title="Distribucion de incoherencia")

    incoherence_df = (
        df["incoherente"]
        .map({1: "Incoherente", 0: "Coherente"})
        .fillna("Sin dato")
        .value_counts()
        .reset_index()
    )
    incoherence_df.columns = ["estado", "conteo"]
    return px.bar(
        incoherence_df,
        x="estado",
        y="conteo",
        color="estado",
        title="Coherencia texto-estrellas",
        template="plotly_white",
    )


def build_sentiment_vs_score(df: pd.DataFrame):
    """Distribucion del sentimiento por estrellas."""
    score_column = "Score" if "Score" in df.columns else "Stars" if "Stars" in df.columns else None
    if df.empty or score_column is None or "sentiment_score" not in df.columns:
        return px.box(title="Sentimiento por estrellas")

    return px.box(
        df,
        x=score_column,
        y="sentiment_score",
        color=score_column,
        title="Sentimiento por estrellas",
        template="plotly_white",
    )


def build_correlation_heatmap(df: pd.DataFrame):
    """Mapa de correlacion para features clave del proyecto."""
    candidate_columns = [
        column
        for column in ["Score", "review_len", "sentiment_score", "incoherente", "Helpfulness", "y_util"]
        if column in df.columns
    ]
    if df.empty or len(candidate_columns) < 2:
        return px.imshow(np.array([[1.0]]), text_auto=True, title="Correlacion de variables")

    corr = df[candidate_columns].corr(numeric_only=True)
    return px.imshow(
        corr,
        text_auto=True,
        title="Correlacion de variables clave",
        color_continuous_scale="RdBu_r",
    )
