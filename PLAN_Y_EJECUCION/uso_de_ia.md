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

La intención no es “demostrar que se usó IA”, sino dejar trazabilidad de qué se pidió, qué se aceptó y qué fue revisado por una persona.

---

## Registro 1

- Fecha: 2026-05-23
- Integrante: Eduardo
- Herramienta: Codex
- Tarea: análisis global del proyecto Streamlit + ciencia de datos
- Prompt resumido: analizar el proyecto actual, evaluar arquitectura, gráficos, módulos y proponer mejoras visuales, funcionales y de estructura
- Salida que aceptamos: diagnóstico del proyecto, propuesta por fases, separación por capas, sugerencias de diseño ejecutivo y nuevas funcionalidades
- Salida que rechazamos o corregimos: no se aceptó pasar directo a código sin antes definir arquitectura y diseño funcional
- Quién verificó: Eduardo

## Registro 2

- Fecha: 2026-05-24
- Integrante: Eduardo
- Herramienta: Codex
- Tarea: refactorización arquitectónica de la app Streamlit
- Prompt resumido: crear una nueva arquitectura con `main.py`, `pages`, `services`, `plots`, `components`, `utils`, `config` y `styles`
- Salida que aceptamos: estructura nueva del proyecto, CSS externo, páginas multipágina, servicios reutilizables y documentación interna en el código
- Salida que rechazamos o corregimos: se descartó mantener toda la lógica dentro de `scripts/dashboard.py`
- Quién verificó: Eduardo

## Registro 3

- Fecha: 2026-05-24
- Integrante: Eduardo
- Herramienta: Codex
- Tarea: rediseño visual y narrativa del dashboard
- Prompt resumido: mejorar portada, resumen, exploración, modelos, auditoría y ranking con estilo moderno, ejecutivo y consistente
- Salida que aceptamos: nueva identidad visual, mejor jerarquía, páginas más claras, tarjetas de métricas, paneles de insights y vista más profesional
- Salida que rechazamos o corregimos: se evitó copiar de forma literal la interfaz de Amazon; solo se tomó inspiración funcional
- Quién verificó: Eduardo

## Registro 4

- Fecha: 2026-05-24
- Integrante: Eduardo
- Herramienta: Codex
- Tarea: conexión real de modelos y lógica de auditoría
- Prompt resumido: conectar la página de modelos con métricas reales del parquet y mejorar la auditoría con utilidad, benchmark, punto ciego y recomendaciones
- Salida que aceptamos: evaluación real de `Logistic Regression` y `LightGBM`, uso de `LightGBM` guardado, recomendaciones automáticas, benchmark local/global y validación contextual
- Salida que rechazamos o corregimos: se corrigió el uso de un proxy simple de sentimiento y luego se unificó VADER real en auditoría
- Quién verificó: Eduardo

## Registro 5

- Fecha: 2026-05-24
- Integrante: Eduardo
- Herramienta: Codex
- Tarea: persistencia operativa y ranking contextual
- Prompt resumido: implementar guardado de reseñas en archivo separado, filtros por producto/usuario, descarga CSV y ventana tipo “sanduche” para mostrar la reseña dentro del ranking del producto
- Salida que aceptamos: creación de `datos_generados/reseñas_auditadas.csv`, botón `Grabar reseña`, filtros en `ranking`, descarga de reseñas filtradas y vista contextual de la reseña evaluada
- Salida que rechazamos o corregimos: se rechazó modificar el dataset original o sobrescribir el parquet limpio
- Quién verificó: Eduardo

## Registro 6

- Fecha: 2026-05-24
- Integrante: Eduardo
- Herramienta: Codex
- Tarea: documentación de entrega
- Prompt resumido: crear README, .gitignore, resumen del caso, plan de preparación, bitácora de IA y base estructurada de notebooks
- Salida que aceptamos: documentación inicial del proyecto, estructura mínima de entrega y orientación clara para completar los cuadernos académicos
- Salida que rechazamos o corregimos: no se presentó como entrega final completa; quedó explícito que los cuadernos 01 y 02 aún deben completarse con contenido real adicional
- Quién verificó: Eduardo
