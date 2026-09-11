# Metodología (borrador — se completa por etapas)

Este documento es la base de la futura página `/metodologia` de la app. En
la Etapa 1 solo cubre lo que ya existe.

## Fuentes y frecuencia

Ver `docs/data-sources.md` para el detalle completo de la fuente BCRA, sus
endpoints y las limitaciones conocidas. Todas las series de esta etapa son
de frecuencia diaria según la clasifica el propio BCRA (`periodicidad`),
salvo el PBI (trimestral, cargado a mano — ver más abajo).

## Fecha de última actualización

Cada serie guarda en `series_catalog.metadata.ultima_fecha_informada` la
última fecha que el BCRA tenía informada en el momento del último catálogo
descargado. La página de agregados monetarios la muestra debajo del
gráfico de cada serie.

## Datos originales vs. derivados

- **Originales:** todo lo que vive en `series_observations.value` viene
  directo de la respuesta de la API del BCRA, sin transformar (excepto el
  PBI, que es la única serie cargada a mano — ver más abajo). Ver
  `series_observations.source_payload` para el punto crudo tal como llegó.
- **Derivados:** variaciones diarias, variaciones sobre N observaciones,
  medias móviles y % del PBI se calculan en el momento en `lib/derived.ts`
  (frontend) o en `scripts/bcra/transform.py` (solo para la validación de
  cambios extremos en la ingesta). Ninguna de estas se guarda en la base
  en esta etapa.

### Fórmulas usadas

- Variación diaria (%): `(valor_t - valor_t-1) / |valor_t-1| * 100`
- Variación sobre N observaciones (%): `(valor_último - valor_hace_N) / |valor_hace_N| * 100`,
  donde "hace N" cuenta N observaciones de la serie, no N días de
  calendario (relevante por feriados/fines de semana).
- Media móvil simple de ventana W: promedio de las últimas W observaciones.

### % del PBI

El BCRA no publica el PBI: se carga a mano desde `/cargar-pbi` (ver
`docs/data-sources.md`). Para expresar una serie como % del PBI
(`lib/pbi.ts` + `lib/derived.ts::asPercentOfAnnualizedGdp`):

1. Para cada observación de la serie con fecha `d`, se busca el trimestre
   de PBI cargado más reciente con fecha `<= d`.
2. Ese valor trimestral se anualiza multiplicándolo ×4.
3. `% del PBI = valor_serie / PBI_anualizado * 100`.

Es una aproximación deliberada: anualizar un solo trimestre asume que los
4 trimestres del año tienen un nivel similar al último cargado, en vez de
sumar los 4 trimestres reales. Se eligió así para que el cálculo funcione
desde el primer dato de PBI cargado (no hace falta esperar a tener un año
completo), y mejora sola a medida que se cargan más trimestres: cada
observación usa el trimestre real más cercano a su fecha, no siempre el
último disponible. Los puntos anteriores al primer dato de PBI cargado no
se pueden expresar como % del PBI y se omiten del gráfico.

## Validación de datos

Antes de guardar una observación nueva, `scripts/bcra/transform.py` calcula
un z-score de la variación diaria contra las ~60 observaciones previas de
esa misma serie. Si el z-score supera el umbral (por default 4), la
observación se guarda igual pero se marca `is_flagged = true` con un
`flag_reason`, para revisión manual — nunca se descarta automáticamente.
Esta validación no aplica a la serie de PBI (carga manual, sin pipeline de
ingesta automática).

## Límites conocidos de esta etapa

- El mapeo entre nombres de series del BCRA y las variables estandarizadas
  de la app se resuelve por reglas de texto (ver
  `scripts/bcra/config.py`), y varias reglas están marcadas explícitamente
  como pendientes de revisión (depósitos en pesos, depósitos privados,
  liquidez del sistema financiero). Ver
  `docs/series-mapping-report.md` (se genera al correr el script) para el
  estado real contra el catálogo vivo.
- El % del PBI usa una anualización aproximada (ver arriba) mientras no
  haya varios trimestres reales cargados.
- Todavía no hay página de licitaciones del Tesoro ni sección de
  interacción Tesoro–liquidez: llegan en la Etapa 2.

## Asociación vs. causalidad

Cuando en una etapa futura se cruce el calendario de licitaciones del
Tesoro con la evolución de los agregados monetarios (sección "Tesoro —
Liquidez" del proyecto), la app va a mostrar únicamente asociaciones
temporales (qué pasó con una serie antes/después de una fecha de
licitación), nunca una afirmación de causalidad. Este principio aplica a
todo el proyecto, no solo a esa sección.
