# Caso 06 · Reseñas Amazon — Predicción de Utilidad

## Resumen del caso

Este proyecto estudia el problema de predecir si una reseña de Amazon Fine Food Reviews será considerada útil por otros compradores. La utilidad de una reseña tiene impacto directo en la experiencia de compra, porque en plataformas de e-commerce las opiniones visibles influyen en la confianza, la comparación entre productos y la decisión final de compra.

La propuesta del proyecto no se limita a clasificar reseñas como útiles o no útiles. También busca transformar ese análisis en un producto analítico usable: una API de predicción, un dashboard de exploración y evaluación de modelos, y una auditoría en tiempo real que ayude a revisar reseñas antes de publicarlas.

## Contexto del dominio

En un marketplace digital, las reseñas cumplen una función de prueba social. Los productos con mejores opiniones visibles tienden a convertir mejor, mientras que las reseñas pobres, confusas o fuera de contexto pueden introducir ruido y afectar la experiencia del usuario. En este caso, la plataforma no solo necesita reseñas positivas, sino reseñas que realmente aporten información útil.

La decisión de negocio que inspira este trabajo es clara: si una plataforma puede estimar la utilidad esperada de una reseña antes de publicarla, puede priorizar contenido de mejor calidad, detectar casos problemáticos y sugerir mejoras a quien escribe. Esto beneficia a compradores, vendedores y al ecosistema del producto.

## Pregunta principal de negocio

¿Qué características de una reseña textual permiten predecir si será percibida como útil por otros compradores?

## Preguntas secundarias

1. ¿La longitud del texto influye positivamente en la utilidad percibida?
2. ¿El sentimiento del texto aporta información adicional más allá de la calificación en estrellas?
3. ¿La incoherencia entre sentimiento y estrellas disminuye la probabilidad de utilidad?
4. ¿Es posible detectar reseñas bien escritas pero fuera del contexto del producto, como un “punto ciego” del sistema?

## Métrica de éxito

La métrica de éxito principal del problema de modelado es `ROC-AUC`, complementada por `Precision`, `Recall` y `F1-score`. Desde negocio, el éxito del producto analítico se interpreta como la capacidad de:

- identificar reseñas con alta utilidad esperada
- detectar reseñas incoherentes o fuera de contexto
- ofrecer retroalimentación accionable antes de publicar

## Variables clave del caso

Variables originales relevantes:

- `ProductId`
- `UserId`
- `ProfileName`
- `HelpfulnessNumerator`
- `HelpfulnessDenominator`
- `Score`
- `Time`
- `Summary`
- `Text`

Variables derivadas relevantes:

- `y_util`
- `review_len`
- `sentiment_score`
- `incoherente`

## Hipótesis iniciales

1. Las reseñas más largas tienden a ser percibidas como más útiles.
2. Las reseñas con sentimiento alineado con la calificación en estrellas tienen mayor credibilidad.
3. La calificación en estrellas por sí sola no explica completamente la utilidad.
4. Las reseñas negativas bien argumentadas pueden ser útiles aunque no sean positivas.
5. Una reseña fuera de contexto puede parecer bien escrita, pero debe detectarse como caso problemático para el producto.

## Estado actual del proyecto

Actualmente el proyecto cuenta con:

- dataset crudo local
- dataset limpio en parquet
- feature engineering para modelado
- baseline con Logistic Regression
- modelo principal con LightGBM
- API FastAPI
- dashboard Streamlit multipágina
- evaluación de reseñas en tiempo real
- validación contextual tipo “punto ciego”
- persistencia separada de reseñas nuevas en CSV operativo
