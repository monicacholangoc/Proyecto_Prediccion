# Predicción de Utilidad de Reseñas Amazon Fine Food

Proyecto de seminario de ciencia de datos enfocado en predecir la utilidad percibida de reseñas de productos alimenticios en Amazon. El sistema combina preparación de datos, EDA, modelado supervisado, una API con FastAPI y un dashboard en Streamlit para auditoría de reseñas en tiempo real.

## Integrantes

- Arevalo Jose
- Cholango Monica 
- Torres Byron

## Objetivo del caso

Construir un sistema que:

- prediga si una reseña será considerada útil por otros usuarios
- compare un modelo interpretable contra uno de mayor capacidad predictiva
- ayude a revisar reseñas en tiempo real antes de publicarlas
- detecte casos de "punto ciego", cuando la reseña no corresponde al producto o categoría seleccionados

## Estructura del repositorio

```text
Predictivo/
├── .streamlit/
├── components/
├── config/
├── cuadernos/
├── datos_crudos/
├── datos_generados/
├── datos_procesados/
├── modelos/
├── pages/
├── plots/
├── scripts/
├── services/
├── styles/
├── utils/
├── main.py
└── requirements.txt
```

## Dataset

- Fuente: Amazon Fine Food Reviews
- Archivo crudo local: `datos_crudos/Reviews.csv`
- Archivo procesado principal: `datos_procesados/reviews_limpias.parquet`
- Contexto de productos: `datos_procesados/productos_contexto.parquet`

## Modelos implementados

- Baseline: `Logistic Regression`
- Modelo principal: `LightGBM`
- Técnicas auxiliares: `VADER`, `TF-IDF`, `KMeans`, reglas por keywords para validación contextual

## Instalación

1. Crear y activar entorno virtual.
2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

## Ejecución

### Dashboard Streamlit

```powershell
streamlit run main.py
```

### API FastAPI

```powershell
uvicorn scripts.api:app --reload
```

## Flujo funcional del dashboard

- `main`: portada y navegación general
- `resumen`: visión ejecutiva del caso
- `exploracion`: EDA con filtros y visualizaciones
- `modelos`: comparación real entre clasificadores
- `auditoria`: evaluación de reseña, utilidad, punto ciego y guardado operativo
- `ranking`: benchmark por producto, ranking local/global e histórico por fecha

## Datos generados por la app

Las reseñas nuevas evaluadas y guardadas desde la app no modifican el dataset original. Se almacenan aparte en:

- `datos_generados/reseñas_auditadas.csv`

Esto mantiene inmutable la fuente histórica y mejora la trazabilidad.

## Estado actual

- App multipágina en Streamlit operativa
- API FastAPI operativa
- Evaluación real de modelos conectada a la app
- Validación contextual / punto ciego implementada
- Persistencia separada de nuevas reseñas implementada

## Pendientes recomendados

- completar los notebooks `01_preparacion_datos.ipynb` y `02_eda.ipynb`
- generar documentación final de decisiones metodológicas
- considerar una exportación PDF ejecutiva para reportes
