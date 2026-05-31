"""Rutas centralizadas del proyecto.

Este modulo evita repetir paths manuales en diferentes archivos.
Si cambia la ubicacion de datos o modelos, el ajuste se hace aqui.
"""

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = ROOT_DIR / "datos_crudos"
DATA_PROCESSED_DIR = ROOT_DIR / "datos_procesados"
DATA_GENERATED_DIR = ROOT_DIR / "datos_generados"
REPORTS_DIR = DATA_GENERATED_DIR / "reportes"
MODELS_DIR = ROOT_DIR / "modelos"
STYLES_DIR = ROOT_DIR / "styles"
REVIEWS_WITH_CATEGORY_PATH = DATA_DIR / "reviews_con_categoria.parquet"
REVIEWS_RAW_PATH = DATA_RAW_DIR / "Reviews.csv"
REVIEWS_PROCESSED_PATH = DATA_PROCESSED_DIR / "reviews_limpias.parquet"
PRODUCT_CONTEXT_PATH = DATA_PROCESSED_DIR / "productos_contexto.parquet"
AUDITED_REVIEWS_PATH = DATA_GENERATED_DIR / "reseñas_auditadas.csv"
LGB_MODEL_PATH = MODELS_DIR / "modelo_lgb.joblib"
