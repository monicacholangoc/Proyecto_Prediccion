"""Servicios relacionados con inferencia y auditoria.

Este modulo encapsula:
- carga del modelo entrenado
- prediccion de utilidad
- reglas de auditoria para la experiencia en tiempo real
"""

import re

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from config.constants import MODEL_FEATURES
from config.settings import LGB_MODEL_PATH
from services.feature_service import build_incoherence_flag


TECH_KEYWORDS = {
    "celular",
    "celulares",
    "phone",
    "telefono",
    "telefono móvil",
    "movil",
    "bateria",
    "pantalla",
    "graphic",
    "interfaz",
    "cargador",
    "smartphone",
    "tablet",
    "laptop",
    "computador",
    "audifonos",
    "usb",
}

FOOD_CONTEXT_KEYWORDS = {
    "alimento",
    "comida",
    "sabor",
    "ingrediente",
    "snack",
    "sopa",
    "caldo",
    "te",
    "té",
    "cafe",
    "café",
    "galleta",
    "chocolate",
    "dulce",
    "mascota",
    "perro",
    "gato",
    "organico",
    "orgánico",
    "suplemento",
    "condimento",
    "bebida",
}


@st.cache_resource(show_spinner=False)
def load_trained_model():
    """Carga el modelo serializado solo una vez por sesion."""
    if LGB_MODEL_PATH.exists():
        return joblib.load(LGB_MODEL_PATH)
    return None


@st.cache_resource(show_spinner=False)
def load_sentiment_analyzer() -> SentimentIntensityAnalyzer:
    """Carga VADER una sola vez para reutilizarlo en la auditoría."""
    return SentimentIntensityAnalyzer()


def predict_helpfulness(
    stars: int,
    sentiment_score: float,
    review_len: int,
    incoherente: int,
) -> float:
    """Predice la probabilidad de utilidad con features ya calculadas."""
    model = load_trained_model()
    feature_frame = pd.DataFrame(
        [[stars, sentiment_score, review_len, incoherente]],
        columns=["Score", "sentiment_score", "review_len", "incoherente"],
    )

    if model is None:
        return 0.75 if review_len > 100 and incoherente == 0 else 0.30

    return float(model.predict_proba(feature_frame)[0][1])


def get_model_features() -> list[str]:
    """Expone el orden esperado de las features del modelo."""
    return MODEL_FEATURES.copy()


def _normalize_tokens(text: str) -> set[str]:
    """Normaliza texto a tokens simples para validaciones ligeras."""
    cleaned_text = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s]", " ", text.lower())
    tokens = {token for token in cleaned_text.split() if len(token) > 2}
    return tokens


def detect_context_blind_spot(
    text: str,
    product_name: str | None = None,
    category_name: str | None = None,
) -> dict:
    """Valida si la reseña parece hablar del contexto correcto del producto.

    La lógica es intencionalmente interpretable: busca menciones de tecnología
    y contrasta algunas palabras del nombre/categoría del producto con el texto.
    """
    tokens = _normalize_tokens(text)
    product_tokens = _normalize_tokens(product_name or "")
    category_tokens = _normalize_tokens(category_name or "")

    product_context_tokens = {
        token
        for token in product_tokens.union(category_tokens).union(FOOD_CONTEXT_KEYWORDS)
        if token not in {"productos", "producto", "categoria", "modelo", "real", "food"}
    }

    tech_hits = sorted(tokens.intersection(TECH_KEYWORDS))
    context_hits = sorted(tokens.intersection(product_context_tokens))
    is_food_context = any(token in product_context_tokens for token in FOOD_CONTEXT_KEYWORDS)

    # Si detectamos lenguaje tecnológico en un producto alimenticio, marcamos punto ciego.
    blind_spot_detected = bool(tech_hits) and is_food_context

    if blind_spot_detected:
        explanation = (
            "La reseña parece hablar de un contexto tecnológico que no coincide con "
            "el producto o categoría alimenticia seleccionados."
        )
    elif not context_hits and is_food_context:
        explanation = (
            "No se detectaron referencias claras al producto o a su categoría. "
            "La reseña podría ser útil, pero su contexto es ambiguo."
        )
    else:
        explanation = (
            "El texto mantiene una relación razonable con el producto o categoría "
            "seleccionados."
        )

    return {
        "blind_spot_detected": blind_spot_detected,
        "context_hits": context_hits,
        "tech_hits": tech_hits,
        "explanation": explanation,
    }


def audit_review_text(
    text: str,
    stars: int,
    product_id: str,
    product_name: str | None = None,
    category_name: str | None = None,
    validate_context: bool = True,
) -> dict:
    """Evalua una reseña con reglas de negocio y scoring del modelo.

    Devuelve un diccionario listo para alimentar la UI:
    probabilidad, estado, longitud y banderas auxiliares.
    """
    review_len = len(text.split())
    sentiment_score = load_sentiment_analyzer().polarity_scores(text)["compound"]
    incoherente = build_incoherence_flag(stars, sentiment_score)
    probability = predict_helpfulness(stars, sentiment_score, review_len, incoherente)
    context_validation = detect_context_blind_spot(text, product_name, category_name)
    blind_spot_detected = context_validation["blind_spot_detected"] if validate_context else False

    # La regla de "punto ciego" simula un control de consistencia tematica
    # alineado con la narrativa del proyecto.
    if blind_spot_detected:
        probability = 0.05
        status = "RECHAZADA (Punto Ciego)"
    elif probability >= 0.70:
        status = "APROBADA (Publicada)"
    else:
        status = "RECHAZADA (Baja Calidad)"

    return {
        "product_id": product_id,
        "probability": probability,
        "status": status,
        "review_len": review_len,
        "sentiment_score": sentiment_score,
        "incoherente": bool(incoherente),
        "habla_de_tecnologia": bool(context_validation["tech_hits"]),
        "context_validation_enabled": validate_context,
        "context_blind_spot": blind_spot_detected,
        "context_hits": context_validation["context_hits"],
        "tech_hits": context_validation["tech_hits"],
        "context_explanation": context_validation["explanation"],
    }


def generate_review_recommendations(audit_result: dict) -> list[str]:
    """Genera recomendaciones accionables a partir del resultado de auditoría."""
    recommendations: list[str] = []

    if audit_result.get("context_blind_spot"):
        recommendations.append("Reescribe la reseña para enfocarla en el producto y categoría correctos.")
    elif audit_result.get("context_validation_enabled") and not audit_result.get("context_hits"):
        recommendations.append("Nombra el producto o menciona señales claras de su categoría para dar más contexto.")

    review_len = int(audit_result.get("review_len", 0))
    if review_len < 40:
        recommendations.append("Agrega más detalle sobre uso, sabor, empaque o resultado del producto.")
    elif review_len < 80:
        recommendations.append("Incluye un ejemplo concreto de experiencia para aumentar credibilidad.")

    if audit_result.get("incoherente"):
        recommendations.append("Alinea mejor el tono del texto con la calificación en estrellas.")

    sentiment_score = float(audit_result.get("sentiment_score", 0.0))
    if sentiment_score > 0.6:
        recommendations.append("Complementa la opinión positiva con razones específicas, no solo entusiasmo general.")
    elif sentiment_score < -0.3:
        recommendations.append("Explica con claridad qué falló y cómo afectó tu experiencia con el producto.")

    if float(audit_result.get("probability", 0.0)) >= 0.70:
        recommendations.append("La reseña ya tiene buena base; puedes fortalecerla añadiendo contexto de compra o frecuencia de uso.")

    if not recommendations:
        recommendations.append("La reseña está balanceada; mantén el mismo nivel de especificidad y coherencia.")

    return recommendations
