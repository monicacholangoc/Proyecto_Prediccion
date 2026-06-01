import pandas as pd


def add_basic_text_features(df: pd.DataFrame, text_column: str = "Text") -> pd.DataFrame:
    """Agrega longitud y conteo simple de oraciones a un DataFrame."""
    enriched = df.copy()
    if text_column not in enriched.columns:
        return enriched

    enriched["review_len"] = enriched[text_column].astype(str).str.split().str.len()
    enriched["sentence_count"] = (
        enriched[text_column].astype(str).str.count(r"[.!?]") + 1
    )
    return enriched


def build_sentiment_proxy(score: int) -> float:
    """Proxy temporal de sentimiento basado en stars.

    Se usa en la app mientras conectamos el pipeline completo de VADER
    dentro de la nueva arquitectura.
    """
    return max(-1.0, min(1.0, 0.15 * float(score)))


def build_incoherence_flag(stars: int, sentiment_score: float) -> int:
    """Marca incoherencia basica entre polaridad y calificacion baja."""
    return int(sentiment_score > 0.05 and stars <= 2)
