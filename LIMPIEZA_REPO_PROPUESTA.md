# Propuesta De Limpieza Final Del Repo

Este documento no ejecuta borrados. Solo deja constancia de qué conviene revisar o eliminar antes de una entrega final.

## Borrado o exclusión recomendada

1. `__pycache__/` en la raíz y en subcarpetas
   - Motivo: archivos compilados automáticos, no forman parte del código fuente.

2. `venv/`
   - Motivo: entorno virtual local, no debe versionarse en Git.

3. `Microsoft/`
   - Motivo: carpeta ajena a la lógica del proyecto; parece haberse creado por error dentro del workspace.

4. `services/preprocesing_service.py`
   - Motivo: archivo vacío y además con nombre mal escrito; el archivo correcto es `preprocessing_service.py`.

5. `scripts/dashboard.py`
   - Motivo: hoy funciona como versión legacy del dashboard. No necesariamente hay que borrarlo ya, pero sí decidir si se conserva como respaldo o si se elimina para evitar duplicidad.

## Mantener

1. `datos_crudos/Reviews.csv`
   - Motivo: fuente local del proyecto. No debe subirse si el repo será público y supera el límite de tamaño, pero sí debe conservarse localmente.

2. `datos_procesados/reviews_limpias.parquet`
   - Motivo: dataset limpio central del flujo analítico.

3. `datos_procesados/productos_contexto.parquet`
   - Motivo: contexto semántico para productos.

4. `datos_generados/reseñas_auditadas.csv`
   - Motivo: persistencia operativa separada de nuevas reseñas.

## Revisión adicional antes de entrega

- confirmar codificación UTF-8 en archivos de texto
- revisar consistencia de nombres de carpetas con la guía del curso
- decidir si se agregan `07_CONTEXTO` y `08_PLAN_Y_EJECUCION` al README raíz
- verificar que `requirements.txt` incluya todas las dependencias realmente usadas
