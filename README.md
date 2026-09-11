# Monitor Monetario Argentina

Base histórica y visualización de la política monetaria y la liquidez en
Argentina, con foco en la interacción entre el BCRA y las licitaciones del
Tesoro.

**Estado actual: Etapa 1.** Solo están implementadas las series del BCRA
(agregados monetarios, reservas, liquidez, tasas). El módulo de
licitaciones del Tesoro es la Etapa 2 y todavía no existe.

## Stack

Next.js (App Router) + React + TypeScript + Tailwind CSS · Supabase
(Postgres) · Recharts · Python (ingesta) · GitHub Actions (Etapa 2).

## Estructura del repositorio

```
app/
  agregados/          página de agregados monetarios (selector + gráfico)
  layout.tsx, page.tsx
components/
  charts/SeriesChart.tsx   gráfico de una serie (Recharts)
  ui/SeriesSelect.tsx      selector de serie (navega por query param)
  ui/StatCard.tsx          card de KPI
lib/
  series.ts           único punto de acceso a datos de series (Supabase)
  derived.ts           variaciones y medias móviles, calculadas al vuelo
  format.ts            formato de números/fechas es-AR
  supabase/            cliente Supabase (anon key) y tipos de las tablas
scripts/bcra/
  config.py            capa de mapeo: reglas para encontrar cada serie en el catálogo real del BCRA
  bcra_client.py        cliente de la API de Estadísticas Monetarias v4.0
  matcher.py            resuelve las reglas de config.py contra el catálogo
  download.py           CLI de sincronización (--mode full | incremental | --list-catalog)
  upload.py             escritura a Supabase + validación de cambios extremos
  transform.py           funciones de variación/detección de outliers
  tests/                 tests unitarios del matcher y de transform (sin red)
database/
  schema.sql            series_catalog, series_observations, series_ingestion_runs
  seed.sql               intencionalmente vacío (ver el archivo)
docs/
  data-sources.md        fuente del BCRA documentada en detalle
  methodology.md         fórmulas y límites conocidos
  series-mapping-report.md  se genera al correr download.py (no versionar a mano)
```

## Cómo correrlo

### 1. Crear el proyecto en Supabase

1. Crear un proyecto nuevo en [supabase.com](https://supabase.com).
2. En el **SQL Editor**, correr el contenido de `database/schema.sql`.
   (`database/seed.sql` no inserta datos a propósito — ver el archivo.)
3. Copiar `.env.example` a `.env.local` y completar:
   - `NEXT_PUBLIC_SUPABASE_URL` y `NEXT_PUBLIC_SUPABASE_ANON_KEY`: en
     *Project Settings → API*.
   - `SUPABASE_SERVICE_ROLE_KEY`: en la misma pantalla ("service_role",
     secreta). **Nunca** commitear este valor ni usarlo en código de
     frontend.

### 2. Traer los datos del BCRA

Requiere Python 3.11+.

```bash
cd scripts/bcra
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ../..

# Variables de entorno para los scripts (además de las de Supabase):
export NEXT_PUBLIC_SUPABASE_URL=...
export SUPABASE_SERVICE_ROLE_KEY=...

# Ver qué series existen hoy en el BCRA (no escribe nada):
python -m scripts.bcra.download --list-catalog

# Carga inicial completa:
python -m scripts.bcra.download --mode full

# Actualización incremental (pensada para correr a diario):
python -m scripts.bcra.download --mode incremental
```

Cada corrida regenera `docs/series-mapping-report.md` con qué series se
resolvieron automáticamente y cuáles quedaron pendientes de revisión (ver
`scripts/bcra/config.py` para ajustar las reglas de mapeo).

Correr los tests (no requieren red ni credenciales):

```bash
python3 -m unittest discover -s scripts/bcra/tests
```

### 3. Levantar la app

Requiere Node.js 18.18+.

```bash
npm install
npm run dev
```

Abrir `http://localhost:3000/agregados`.

## Variables de entorno

| Variable | Dónde se usa | Secreta |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Frontend y scripts | No |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Frontend (lectura pública, protegida por RLS) | No |
| `SUPABASE_SERVICE_ROLE_KEY` | Solo `scripts/bcra/*` (bypassea RLS para escribir) | **Sí** |
| `BCRA_HTTP_TIMEOUT` | Opcional, timeout en segundos para la API del BCRA (default 30) | No |
| `BCRA_TLS_INSECURE` | Opcional, escape hatch si hay error de certificado TLS (default apagado) | No |

## Fuente de datos exacta

BCRA — API de Estadísticas Monetarias v4.0, `https://api.bcra.gob.ar/estadisticas/v4.0`,
sin autenticación. Detalle completo, incluyendo por qué no hay ningún
`idVariable` hardcodeado, en [`docs/data-sources.md`](docs/data-sources.md).

## Limitación conocida de este build

Este proyecto se generó en un entorno sandboxeado cuyo acceso saliente
está restringido a una lista blanca de dominios que **no incluye**
`registry.npmjs.org`, `pypi.org` ni `api.bcra.gob.ar`. Como consecuencia:

- No se pudo correr `npm install` ni `npm run build` para verificar que la
  app compila.
- No se pudo instalar el paquete `supabase` de Python ni correr
  `download.py` contra la API real.
- Sí se pudieron correr los tests unitarios de `scripts/bcra/tests`
  (usan un catálogo sintético, sin red) y se revisó a mano cada archivo.

**Antes de dar la Etapa 1 por cerrada, correr localmente:**
`npm install && npm run build` y
`python -m scripts.bcra.download --mode full` (con credenciales reales de
Supabase) para confirmar que no quedó ningún error de compilación o de
integración que este entorno no pudo detectar.

## Pendiente para la Etapa 2

- Módulo de licitaciones del Tesoro: tablas `treasury_auctions` /
  `treasury_auction_instruments`, pantalla de carga manual, página de
  listado y detalle.
- Sección "Tesoro — Liquidez" (cruce de fechas de licitación con la
  evolución de un agregado monetario).
- Dashboard principal con las cards resumen.
- Página de Metodología completa.
- GitHub Action diaria (`update-bcra.yml`) para correr
  `download.py --mode incremental` sin intervención manual.
- Revisar y cerrar las reglas de mapeo marcadas como pendientes en
  `scripts/bcra/config.py` (depósitos en pesos, depósitos privados,
  liquidez del sistema financiero) mirando el catálogo real del BCRA.
