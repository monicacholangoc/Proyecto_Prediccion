# Bitácora De Uso De IA

## Cómo se llena una bitácora profesional

Cada uso significativo de IA debe registrar:

- Fecha
- Integrante
- Herramienta
- Tarea
- Prompt resumido
- Salida que aceptamos
- Salida que rechazamos o corregimos
- Quién verificó

La intención no es "demostrar que se usó IA", sino dejar trazabilidad de qué se pidió, qué se aceptó y qué fue revisado por una persona.

---

## Registros — Arévalo José · EDA & Pipeline

## Registro 1

- Fecha: 2026-05-23
- Integrante: Arévalo José
- Herramienta: Claude (Anthropic)
- Tarea: definición de la pregunta de negocio y variables clave del caso
- Prompt resumido: dado el dataset Amazon Fine Food Reviews, ayudar a formular la pregunta de negocio principal, identificar variables relevantes y proponer hipótesis iniciales concretas
- Salida que aceptamos: pregunta principal sobre predicción de utilidad, cinco hipótesis iniciales con dirección esperada, identificación de `HelpfulnessDenominator` como criterio de filtro estadístico
- Salida que rechazamos o corregimos: se descartó una hipótesis sobre estacionalidad temporal por no ser relevante para el caso de clasificación planteado
- Quién verificó: Arévalo José

## Registro 2

- Fecha: 2026-05-23
- Integrante: Arévalo José
- Herramienta: Codex
- Tarea: pipeline de limpieza y preparación del dataset
- Prompt resumido: construir el script de preparación aplicando filtro `HelpfulnessDenominator >= 5`, deduplicación por `UserId-ProductId-Time`, limpieza de HTML en texto, y generación de variables derivadas `review_len`, `sentiment_score`, `incoherente` y `y_util`
- Salida que aceptamos: script reproducible con validaciones `assert`, exportación a parquet y documentación interna de cada paso
- Salida que rechazamos o corregimos: se corrigió el criterio de deduplicación; la propuesta inicial usaba solo `UserId` y `ProductId`, sin incluir `Time`, lo que eliminaba reseñas legítimas del mismo usuario sobre el mismo producto en fechas distintas
- Quién verificó: Arévalo José

## Registro 3

- Fecha: 2026-05-24
- Integrante: Arévalo José
- Herramienta: Claude (Anthropic)
- Tarea: análisis exploratorio univariado y bivariado para el cuaderno 02_eda
- Prompt resumido: proponer estructura del EDA con mínimo 8 visualizaciones, incluyendo distribución de estrellas, longitud, sentimiento, incoherencia, correlaciones y balance de la variable objetivo
- Salida que aceptamos: estructura del cuaderno con secciones univariado, bivariado e insights finales; sugerencia de usar `px.box` para sentimiento por estrellas y heatmap de correlación para las 6 variables clave
- Salida que rechazamos o corregimos: se descartó una visualización de wordcloud propuesta porque requería dependencias adicionales no incluidas en `requirements.txt` y no aportaba al modelado
- Quién verificó: Arévalo José

---

## Registros — Cholango Mónica · Modelado & API

## Registro 4

- Fecha: 2026-05-24
- Integrante: Cholango Mónica
- Herramienta: Codex
- Tarea: entrenamiento y comparación de clasificadores
- Prompt resumido: implementar `model_eval_service.py` comparando Logistic Regression, LightGBM, XGBoost y CatBoost con métricas `precision`, `recall`, `f1` y `roc_auc`; usar `class_weight='balanced'` para manejar el desbalance de clases
- Salida que aceptamos: servicio con `train_test_split` estratificado, escalado para regresión logística, curvas ROC reales y matrices de confusión por modelo
- Salida que rechazamos o corregimos: la propuesta inicial calculaba `accuracy` como métrica principal; se reemplazó por `roc_auc` y `f1` con justificación explícita del desbalance (70% clase negativa)
- Quién verificó: Cholango Mónica

## Registro 5

- Fecha: 2026-05-24
- Integrante: Cholango Mónica
- Herramienta: Claude (Anthropic)
- Tarea: diseño y documentación de la API FastAPI
- Prompt resumido: estructurar `api.py` con endpoints `POST /reviews/predict_helpfulness` y `GET /reviews/top_words`, CORS abierto para Streamlit Cloud, carga correcta del modelo desde `modelos/modelo_lgb.joblib` y heurística de respaldo si el archivo no existe
- Salida que aceptamos: API con esquema Pydantic, orden de features alineado con el modelo entrenado (`Score`, `sentiment_score`, `review_len`, `incoherente`), health check en `GET /` y respuesta estructurada con desglose de features calculados
- Salida que rechazamos o corregimos: se corrigió la ruta del modelo; la propuesta inicial usaba una ruta relativa que fallaba al lanzar desde `scripts/` con `uvicorn`
- Quién verificó: Cholango Mónica

## Registro 6

- Fecha: 2026-05-25
- Integrante: Cholango Mónica
- Herramienta: Claude (Anthropic)
- Tarea: verificación de estructura del repositorio y limpieza antes de entrega
- Prompt resumido: analizar todos los módulos del proyecto, identificar archivos duplicados o sin conexión con la arquitectura nueva, y verificar si `scripts/dashboard.py` podía eliminarse sin romper dependencias
- Salida que aceptamos: diagnóstico completo de carpetas, confirmación mediante `grep` de que `dashboard.py` no era importado por ningún módulo, y comandos concretos para eliminarlo con trazabilidad en Git
- Salida que rechazamos o corregimos: no se aceptó la sugerencia de vaciar el archivo; se optó por eliminarlo directamente con `git rm` para mantener el historial limpio
- Quién verificó: Cholango Mónica

---

## Registros — Torres Byron · Dashboard & UI

## Registro 7

- Fecha: 2026-05-23
- Integrante: Torres Byron
- Herramienta: Codex
- Tarea: análisis global del proyecto Streamlit y propuesta de refactorización
- Prompt resumido: analizar el proyecto monolítico en `scripts/dashboard.py`, evaluar arquitectura y proponer separación en capas con `main.py`, `pages/`, `services/`, `plots/`, `components/`, `utils/`, `config/` y `styles/`
- Salida que aceptamos: diagnóstico del proyecto, propuesta por fases, separación por capas, sugerencias de diseño ejecutivo y nuevas funcionalidades
- Salida que rechazamos o corregimos: no se aceptó pasar directo a código sin antes validar la arquitectura propuesta con el equipo
- Quién verificó: Torres Byron

## Registro 8

- Fecha: 2026-05-24
- Integrante: Torres Byron
- Herramienta: Codex
- Tarea: rediseño visual del dashboard con identidad ejecutiva
- Prompt resumido: mejorar portada, resumen, exploración, modelos, auditoría y ranking con estilo moderno y consistente; implementar CSS externo con variables de tema para soporte de modo claro y oscuro
- Salida que aceptamos: nueva identidad visual con `styles.css`, jerarquía tipográfica clara, tarjetas de métricas reutilizables, sidebar oscuro persistente y paneles de insight en lenguaje natural
- Salida que rechazamos o corregimos: se evitó copiar literalmente la interfaz de Amazon; solo se tomó inspiración funcional en la estructura de ranking y reseñas
- Quién verificó: Torres Byron

## Registro 9

- Fecha: 2026-05-24
- Integrante: Torres Byron
- Herramienta: Claude (Anthropic)
- Tarea: implementación de persistencia operativa y ranking contextual
- Prompt resumido: implementar guardado de reseñas auditadas en CSV separado sin modificar el dataset original, filtros por producto y usuario, descarga CSV y ventana tipo sándwich para mostrar la reseña dentro del ranking local del producto
- Salida que aceptamos: `preprocessing_service.py` con funciones `append_audited_review`, `get_local_product_ranking`, `get_review_context_window` y `save_latest_review_to_file`; integración con Supabase para persistencia en la nube
- Salida que rechazamos o corregimos: se rechazó la propuesta de sobrescribir `reviews_limpias.parquet` con cada nueva reseña; se mantuvo el dataset original inmutable y las reseñas nuevas se guardan en `datos_generados/reseñas_auditadas.csv`
- Quién verificó: Torres Byron

## Registro 10

- Fecha: 2026-05-24
- Integrante: Torres Byron
- Herramienta: Codex
- Tarea: documentación final del repositorio
- Prompt resumido: crear README con estructura del repo, instrucciones de instalación, descripción del flujo funcional y estado actual del proyecto; generar también el documento de funcionalidades y la propuesta de limpieza del repositorio
- Salida que aceptamos: README completo, `Documento_funcionalidades_proyecto.docx`, `LIMPIEZA_REPO_PROPUESTA.md` con criterios claros de qué eliminar y qué conservar
- Salida que rechazamos o corregimos: no se presentó como entrega final completa; quedó explícito que los cuadernos `01_preparacion_datos.ipynb` y `02_eda.ipynb` aún requieren contenido académico adicional
- Quién verificó: Torres Byron