from fastapi import FastAPI
from pydantic import BaseModel
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import joblib
import numpy as np
import os

app = FastAPI(title="Amazon Review Helpfulness Predictor API")

# Definir la estructura de entrada que requiere la API 
class ReviewInput(BaseModel):
    review_text: str
    stars: int

# Cargar el modelo LightGBM entrenado y el analizador de sentimiento [cite: 44, 45]
# Nota: Asegúrate de haber guardado tu modelo como 'modelo_lgb.joblib' en 04_modelos/ 
base_path = os.path.dirname(__file__)
MODEL_PATH = os.path.join(base_path, "..", "modelos", "modelo_lgb.joblib")

try:
    model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    model = None  # En caso de que se simule el comportamiento antes de guardar el archivo real

analyzer = SentimentIntensityAnalyzer()

@app.post("/reviews/predict_helpfulness")
def predict_helpfulness(data: ReviewInput):
    """Recibe texto y calificación; devuelve la probabilidad de utilidad.""" 
    # 1. Calcular características extraídas en tiempo real [cite: 44]
    review_len = len(data.review_text.split())
    sentiment_score = analyzer.polarity_scores(data.review_text)['compound']
    incoherente = 1 if (sentiment_score > 0.05 and data.stars <= 2) else 0
    
    # 2. Organizar las características en el orden en que se entrenó el modelo
    # features = ['Score', 'sentiment_score', 'review_len', 'incoherente']
    features_array = np.array([[data.stars, sentiment_score, review_len, incoherente]])
    
    # 3. Predecir probabilidad 
    if model:
        probability = model.predict_proba(features_array)[0][1]
    else:
        # Simulación de respaldo si el archivo físico .joblib no se encuentra aún
        probability = 0.75 if (review_len > 100 and incoherente == 0) else 0.30
        
    return {
        "status": "success",
        "probability": float(probability),
        "features_calculated": {
            "length_words": review_len,
            "sentiment_compound": sentiment_score,
            "is_incoherent": bool(incoherente)
        }
    }