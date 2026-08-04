# Prueba técnica — Pametana

## Overview

Programa en Python que lee un fichero de menciones en medios (`menciones.csv`), lo limpia, calcula unas métricas, permite filtrar por palabra clave, y genera un informe. Como parte de profundización, además persiste los datos en SQLite pensando en que el proceso se repita periódicamente con nuevos datos.

## Cómo ejecutarlo

Desde la carpeta `src/`:

```bash
pip install -r ../requirements.txt

# Informe general
python main.py

# Filtrando por palabra clave
python main.py --keyword "inteligencia artificial"

# Cargando además en SQLite y viendo la evolución mensual de un cliente
python main.py --cargar-db --cliente-ejemplo "Velfy"
```

El informe se genera en `data/processed/informe.json` (no versionado en git, se regenera al ejecutar). Esa carpeta también aloja `menciones.db` cuando usas `--cargar-db`.

## Parte 1 — Base

### Estructura del código

El proyecto está separado en `extract.py`, `transform.py`, `analyze.py`, `report.py` y `main.py` para mantener un poco la limpieza y la organización.
### Lectura del csv

De librería para el análisis y el preprocessing uso Polars. Hasta ahora en la carrera por defecto usabamos Pandas pero Polars es algo más moderna y orientada al rendimiento. El DataFrame es cómodo de manejar, es  mas escalable, más eficiente en el uso de la memoria y también tiene lazy execution.






En la lectura inicial del csv fuerzo `infer_schema_length=0`, es decir Polars no infiere el tipo de las columnas. Esto es porque además de que se avisaba que el dataset estaba sucio ya con mirarlo manualmente y abrirlo en el excel o en un jupyter se veia que podría dar algun problema. Se lee todo como texto y luego ya decido yo como convertirlo. 
### Los datos "sucios" y cómo los traté

El csv tiene, aposta, varios tipos de inconsistencias. Fui decidiendo el criterio para cada una:

- **`fecha`**: mezclaba formatos. Lo resolví intentando parsear con un formato y si falla pues probando con el otro (`pl.coalesce` de dos intentos de `strptime`).


- **`medio`**: mayúsculas inconsistentes, espacios sueltos y dobles espacios. Los normalicé con `strip` + colapsar espacios + `to_titlecase()`, para que no contaran como medios distintos por un problema de formato.


- **`alcance`**:   Algo más de lío, algunos números separados con comas otros con puntos y sufijos de K o M. La solución que propongo es: si el valor tiene sufijo K/M  el punto o coma actúan como separador decimal, si no el punto es separador de miles. Aquí lo implemento con función de python normal (`map_elements`) porque encadenando expresiones nativas de Polars quedaba menos legible, prioricé la sencillez porque con 500 filas de dataset tampoco supondría mucho coste de rendimiento. 


- **`cliente` y `medio` vacíos**: decidí descartar esas filas directamente. Sin cliente o sin medio no puedo atribuir la mención a nada útil para las métricas por cliente/medio, así que no aportaban.


- **`alcance` no parseable** (`n.d.`, vacío, etc.): aquí sí mantengo la fila (sigue contando para el total de menciones, por cliente, por medio, por día), pero la excluyo del cálculo de "medio con mayor alcance acumulado" — no tiene sentido sumarle 0 o inventar un valor, mejor excluirla de esa métrica concreta y que el resto de conteos no se vean afectados.


- **Duplicados**: los elimino con `unique()` al final del todo, después de normalizar `medio` y parsear `fecha` — no al principio.  Esto es importante hacerlo despues de normalizar bien porque dos filas pueden parecer distintas antes de limpiar ( por un espacio suelto o algo) y ser en realidad duplicadas. Limpiando primero, los detecto todos.


### Filtro por keyword

Busco la palabra clave tanto en `titular` como en `texto` y hago que no sean key sensitive. Al principio solo iba a buscar en `titular`, pero me pareció que se perdía información relevante que solo aparece en el cuerpo del texto.


### Informe


El informe se genera en JSON (está en data --> processed). JSON en mi opinión mejor, legible tanto por una persona como por un programa. Se puede cargar en otra herramienta como Excel. También se imprime en la consola. El CLI usa (`argparse`) en vez de leer `sys.argv` directamente, porque da validación y ayuda automatica (con `--help`)
## Parte 2 — Profundización: B) Datos a escala

### Por qué SQLite y no Parquet



Las profundizaciones que más me llamaron la atención fueron las opciones A  y B. Pensé que sería mejor tirar para lo que conozco algo mejor. En otro proyecto he trabajado Parquet + DuckDB pero en este como el enunciado pedía explicitamente optimizar consultas "por cliente y por fecha" -- acceso puntual , no una lectura analítica en bloque con todo el dataset. SQLite encaja mejor y viene ya integrado en librería estandar de python `sqlite3` y además demuestro el manejo de una herramienta nueva.

### Esquema

```sql
CREATE TABLE menciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    medio TEXT NOT NULL,
    fecha DATE NOT NULL,
    titular TEXT,
    texto TEXT,
    alcance INTEGER,
    UNIQUE(cliente, medio, fecha, titular)
);

CREATE INDEX idx_cliente_fecha ON menciones(cliente, fecha);
```

Como el enunciado dice que los datos se van a ir acumulando con el tiempo (nuevas cargas periódicas, no solo esta foto de ~490 filas), diseñé el esquema pensando en eso, no solo en esta carga puntual:

- La restricción `UNIQUE(cliente, medio, fecha, titular)` evita que una recarga del mismo csv (o una carga solapada) duplique filas. Uso `INSERT OR IGNORE` al cargar, así puedo ejecutar la carga varias veces sin miedo a duplicar datos.
- El índice compuesto en `(cliente, fecha)` acelera justo el patrón de consulta que pide el enunciado.
- `alcance` es `INTEGER` nullable, coherente con el criterio que ya expliqué arriba (nulo cuando no era parseable).

Guardo `alcance` como número puro, sin separador de miles — el formato con comas (`121,153`) solo lo aplico en la capa de presentación del informe (`report.py`), nunca en el almacenamiento. Si lo guardara como texto formateado, perdería la capacidad de sumarlo o filtrarlo directamente en SQL.

### Consulta de ejemplo

Implementé la evolución mensual de un cliente (número de menciones y alcance acumulado por mes):

```sql
SELECT
    strftime('%Y-%m', fecha) AS mes,
    COUNT(*) AS menciones,
    SUM(alcance) AS alcance_total
FROM menciones
WHERE cliente = ?
GROUP BY mes
ORDER BY mes
```

Uso `strftime('%Y-%m', fecha)` para truncar la fecha a granularidad de mes, que es la forma estándar de hacerlo en SQLite sin necesitar una columna adicional.

Se ejecuta con:

```bash
python main.py --cargar-db --cliente-ejemplo "Velfy"
```

## Qué mejoraría con más tiempo

- Es quizás añadir o tirar por alguna de las otras profundizaciones. Me parece una mejora lógica. Algún test automatizado con `pytests` en el parseo de alcance, logging en vez de print si se fuese a ejecutar de manera desatendida. También me parece buena idea implementar una IA con su API y ver el sentimiento de la mención