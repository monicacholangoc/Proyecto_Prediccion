TOPIC_NAMES = {
    0: "Bebidas e infusiones",
    1: "Alimentos y premios para mascotas",
    2: "Snacks, galletas y dulces",
    3: "Ingredientes y condimentos",
    4: "Productos orgánicos y suplementos",
}

DEFAULT_METRICS = {
    "registros_iniciales": 568_454,
    "registros_limpios": 393_522,
    "duplicados_removidos": 174_918,
    "nulos_eliminados": 14,
    "umbral_utilidad": 0.70,
}

MODEL_FEATURES = ["Score", "sentiment_score", "review_len", "incoherente"]
