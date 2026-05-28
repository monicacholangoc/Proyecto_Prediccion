# Plan De Preparación De Datos

## Objetivo

Construir una versión limpia, reproducible y orientada a modelado del dataset Amazon Fine Food Reviews.

## Pasos de limpieza propuestos

1. Cargar el dataset crudo desde `datos_crudos/Reviews.csv`.
2. Validar estructura, tipos de datos y presencia de columnas clave.
3. Filtrar observaciones con `HelpfulnessDenominator >= 5` para reducir ruido estadístico.
4. Eliminar duplicados usando la llave `UserId`, `ProductId`, `Time`.
5. Limpiar el texto removiendo HTML y dejando un contenido apto para análisis.
6. Generar variables derivadas:
   - `review_len`
   - `sentiment_score`
   - `incoherente`
   - `y_util`
7. Validar nulos, distribuciones y consistencia de las columnas nuevas.
8. Exportar resultado a `datos_procesados/reviews_limpias.parquet`.

## Decisiones metodológicas

### Nulos

- Revisar porcentaje de nulos por columna.
- Eliminar o imputar solo si afecta columnas relevantes para el problema.

### Duplicados

- Se eliminan duplicados exactos según criterio del caso:
  - mismo `UserId`
  - mismo `ProductId`
  - misma `Time`

### Outliers

- La longitud textual se revisa descriptivamente.
- No todo valor extremo debe eliminarse: una reseña muy larga puede seguir siendo útil.

### Encodings y texto

- Estandarizar texto a una representación consistente.
- Quitar etiquetas HTML visibles como `<br />` o enlaces incrustados.

### Variable objetivo

- `y_util = 1` si la tasa de utilidad es mayor o igual a `0.70`
- `y_util = 0` en caso contrario

## Variables nuevas

- `review_len`: longitud en palabras de la reseña.
- `sentiment_score`: sentimiento VADER.
- `incoherente`: bandera binaria para inconsistencia básica entre sentimiento y stars.
- `y_util`: objetivo binario del caso.

## Qué se descarta

- Registros con muy pocos votos útiles totales para evitar proporciones poco representativas.
- Duplicados detectados por la llave definida en el caso.

## Validaciones sugeridas

- `assert df.shape[0] > 0`
- `assert df['ProductId'].notna().all()`
- `assert df['Text'].notna().all()`
- `assert df['y_util'].isin([0, 1]).all()`
