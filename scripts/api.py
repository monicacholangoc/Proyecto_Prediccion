import os
import pathlib

import joblib
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = FastAPI(title="Amazon Review Helpfulness Predictor API")

# CORS — necesario para que Streamlit Cloud pueda llamar a esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rutas reales del proyecto (igual que config/settings.py) ──────────────────
# scripts/api.py está en scripts/ → ROOT es un nivel arriba
ROOT_DIR  = pathlib.Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT_DIR / os.getenv("MODEL_DIR", "modelos")

# Nombre real definido en config/settings.py: LGB_MODEL_PATH = modelos/modelo_lgb.joblib
MODEL_PATH = MODEL_DIR / "modelo_lgb.joblib"

try:
    model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    model = None

analyzer = SentimentIntensityAnalyzer()


# ── Schemas ────────────────────────────────────────────────────────────────────

class ReviewInput(BaseModel):
    review_text: str
    stars: int


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Health check — muestra qué modelos están cargados."""
    return {
        "status": "ok",
        "api": "Amazon Review Helpfulness Predictor API",
        "caso": "Caso 06 · Seminario EDA 2026",
        "modelos": {
            "lgb_model": "cargado ✓" if model is not None else "no encontrado (usando heurística)",
            "model_path": str(MODEL_PATH),
        },
    }


@app.post("/reviews/predict_helpfulness")
def predict_helpfulness(data: ReviewInput):
    """
    Recibe texto y calificación; devuelve la probabilidad de utilidad.
    Features en el orden exacto de MODEL_FEATURES:
    ['Score', 'sentiment_score', 'review_len', 'incoherente']
    """
    review_len    = len(data.review_text.split())
    sentiment_score = analyzer.polarity_scores(data.review_text)["compound"]
    incoherente   = 1 if (sentiment_score > 0.05 and data.stars <= 2) else 0

    # Orden exacto que espera el modelo entrenado
    features_array = np.array([[data.stars, sentiment_score, review_len, incoherente]])

    if model is not None:
        probability = float(model.predict_proba(features_array)[0][1])
    else:
        # Heurística de respaldo (igual que ml_service.py)
        probability = 0.75 if (review_len > 100 and incoherente == 0) else 0.30

    return {
        "status": "success",
        "probability": probability,
        "etiqueta": "Útil" if probability >= 0.5 else "No útil",
        "features_calculated": {
            "length_words": review_len,
            "sentiment_compound": sentiment_score,
            "is_incoherent": bool(incoherente),
            "stars": data.stars,
        },
    }


@app.get("/reviews/top_words")
def top_words():
    """
    Palabras más asociadas a reseñas útiles vs. no útiles.
    Derivadas del análisis TF-IDF sobre Amazon Fine Food Reviews (≥5 votos).
    """
    return {
        "top_words_utiles": [
            "helpful", "recommend", "quality", "excellent", "detailed",
            "delicious", "flavor", "love", "great", "worth",
        ],
        "top_words_no_utiles": [
            "bad", "waste", "terrible", "disappointed", "never",
            "awful", "horrible", "tasteless", "overpriced", "return",
        ],
        "nota": (
            "Palabras derivadas del análisis TF-IDF sobre el dataset Amazon Fine Food Reviews "
            "(HelpfulnessDenominator ≥ 5, drop_duplicates por UserId-ProductId-Time)."
        ),
    }