# Fuentes de datos

## BCRA — API de Estadísticas Monetarias (v4.0)

**Esta es la única fuente de datos monetarios implementada en la Etapa 1.**
Documentación oficial consultada antes de escribir código:

- Catálogo de APIs del BCRA (lista todas las APIs públicas disponibles):
  <https://www.bcra.gob.ar/en/central-bank-api-catalog/>
- Manual técnico de la API de Variables Monetarias v4.0 (PDF oficial, es la
  referencia que se siguió para los endpoints, parámetros y formatos de
  este proyecto):
  <https://www.bcra.gob.ar/archivos/Catalogo/Content/files/pdf/principales-variables-v4.pdf>
- Espejo interactivo (Swagger/OpenAPI) del mismo manual, útil para probar
  requests a mano: <https://principales-variables.bcra.apidocs.ar/>

### Acceso

- **Base URL:** `https://api.bcra.gob.ar/estadisticas/v4.0`
- **Autenticación:** no requiere. El BCRA aplica control de tráfico por IP.
- **Formato:** JSON. Fechas en ISO 8601 (`YYYY-MM-DD`).

### Endpoints usados (y únicamente estos — ver `scripts/bcra/bcra_client.py`)

| Endpoint | Uso en este proyecto |
|---|---|
| `GET /monetarias` | Catálogo completo de series disponibles (paginado, `offset`/`limit`, límite 1000 por página). Es la única fuente de verdad para saber qué `idVariable` existe. |
| `GET /monetarias/{idVariable}` | Historial de una serie puntual. Acepta `desde`/`hasta` (ISO 8601) y pagina hasta 3000 registros por página. |
| `GET /metodologia[/{id}]` | Metodología publicada por el BCRA para una variable. No se usa todavía en la Etapa 1; queda documentado para una futura página de Metodología. |

### Por qué no hay una lista fija de `idVariable` en el código

El pedido original de este proyecto es explícito en no asumir que las
variables (base monetaria, M1, M2, M3, depósitos, etc.) tienen exactamente
esos nombres o esos códigos en la fuente, y en no inventar identificadores.
Por eso:

1. `scripts/bcra/config.py` define **reglas de búsqueda** sobre el campo
   `descripcion` del catálogo real (ej. "debe contener 'base monetaria'"),
   no números de `idVariable` escritos a mano.
2. `scripts/bcra/download.py` trae el catálogo real, aplica esas reglas, y
   recién ahí resuelve qué `idVariable` corresponde a cada variable
   estandarizada.
3. Si una regla no encuentra ningún candidato, o encuentra más de uno, el
   script **no adivina**: lo deja registrado en
   `docs/series-mapping-report.md` (generado automáticamente en cada
   corrida) para revisión manual y ajuste de la regla.

### Variables cubiertas en la Etapa 1

Ver `scripts/bcra/config.py` (`SERIES_RULES`) para el detalle exacto de las
reglas. En líneas generales:

- Base monetaria, circulación monetaria, billetes y monedas en poder del
  público
- Depósitos en pesos, depósitos del sector privado
- M1, M2, M3
- Reservas internacionales
- Efectivo en entidades financieras (proxy de liquidez bancaria)
- Tasa de política monetaria, BADLAR privados, TAMAR, call interbancario

Varias de estas reglas están marcadas como "a revisar" a propósito (ver
`notes` en `config.py`): el BCRA suele publicar múltiples aperturas de una
misma variable (por plazo, por moneda, por tipo de entidad) y decidir cuál
es "la" serie relevante para cada estandarización requiere mirar el
catálogo real, no asumirlo de antemano.

### Nota sobre certificados TLS

Algunas integraciones de terceros con dominios `bcra.gob.ar` reportaron
históricamente errores de verificación de certificado TLS. El cliente de
este proyecto (`scripts/bcra/bcra_client.py`) verifica TLS por default. Si
en tu entorno falla con un `SSLError`, probá primero actualizar el paquete
`certifi` de Python antes de usar la variable de entorno de escape
`BCRA_TLS_INSECURE=1` (no recomendada para CI/producción).

### Limitación de esta etapa: no se pudo probar en vivo desde este entorno

El entorno donde se generó este proyecto tiene el acceso saliente
restringido a una lista blanca de dominios que no incluye `api.bcra.gob.ar`
(ni `registry.npmjs.org` ni `pypi.org`, lo cual también impidió instalar
las dependencias de Node y Python acá — ver README). La lógica de matching
contra el catálogo (`scripts/bcra/matcher.py`) está cubierta por tests
unitarios con datos sintéticos (`scripts/bcra/tests/`), pero el pipeline
completo contra la API real y el build de Next.js **deben verificarse en
un entorno con acceso a internet** (tu máquina o GitHub Actions) antes de
darlos por definitivos.

---

## Tesoro — Licitaciones (Etapa 2, todavía no implementado)

El módulo de licitaciones del Tesoro se documentará acá cuando se
implemente. Por ahora no hay scraping ni carga de datos del Tesoro: la
Etapa 1 se limita a las series del BCRA, tal como se acordó.
