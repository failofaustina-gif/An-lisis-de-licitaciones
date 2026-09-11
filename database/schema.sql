-- =============================================================================
-- Monitor Monetario Argentina — schema inicial (Etapa 1)
-- =============================================================================
-- Alcance de esta etapa: únicamente las series del BCRA (agregados monetarios,
-- reservas, liquidez, tasas). El módulo de licitaciones del Tesoro se agrega
-- en una migración separada durante la Etapa 2, una vez validada la descarga
-- y el almacenamiento de las series del BCRA.
--
-- Principios que este schema refleja:
--   - Los datos originales de cada serie nunca se modifican in-place.
--   - Las variables derivadas (variaciones, medias móviles, etc.) NO se
--     guardan acá: se calculan al vuelo en la capa de presentación
--     (lib/derived.ts) a partir de series_observations. Si en el futuro el
--     volumen de datos lo justifica, se puede agregar una tabla de
--     derivados materializados sin tocar esta estructura.
--   - Ninguna serie, código o id de la fuente se hardcodea en el frontend:
--     todo pasa por series_catalog.
-- =============================================================================

create extension if not exists "pgcrypto"; -- para gen_random_uuid()

-- -----------------------------------------------------------------------------
-- series_catalog: capa de mapeo entre la fuente original y la app
-- -----------------------------------------------------------------------------
-- Cada fila representa una serie temporal individual tal como la publica la
-- fuente (hoy: BCRA), más su traducción a un nombre estandarizado que usa
-- el resto de la aplicación. El source_series_id (ej. idVariable del BCRA)
-- se completa siempre con el valor devuelto por la API real, nunca a mano.
create table if not exists series_catalog (
  id uuid primary key default gen_random_uuid(),

  -- Identificación en la fuente original
  source text not null,                 -- ej: 'BCRA'
  source_series_id text not null,       -- ej: idVariable devuelto por la API del BCRA (como texto)
  original_name text not null,          -- 'descripcion' tal cual la devuelve la fuente

  -- Estandarización interna
  display_name text not null,           -- nombre estandarizado usado en la UI (ej: 'base_monetaria')
  category text not null,               -- ej: 'agregados_monetarios', 'reservas', 'liquidez', 'tasas'
  frequency text not null,              -- 'D' diaria, 'M' mensual, 'Q' trimestral, etc. (tal como la fuente)
  unit text not null,                   -- ej: 'ARS millones', 'USD millones', '% n.a.'
  description text,                     -- notas adicionales / metodología resumida

  active boolean not null default true, -- permite desactivar una serie sin borrar histórico
  metadata jsonb not null default '{}'::jsonb, -- campos crudos adicionales de la fuente (categoria, moneda, tipoSerie, etc.)

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  constraint series_catalog_source_unique unique (source, source_series_id)
);

comment on table series_catalog is
  'Capa de mapeo: nombre/código original de la fuente <-> nombre estandarizado interno.';
comment on column series_catalog.source_series_id is
  'Id de la serie tal como lo asigna la fuente (ej. idVariable del BCRA). Nunca inventado a mano.';
comment on column series_catalog.display_name is
  'Nombre estandarizado interno, estable, usado por la app y por lib/config/series-catalog.ts.';

-- -----------------------------------------------------------------------------
-- series_observations: datos originales, sin transformar
-- -----------------------------------------------------------------------------
create table if not exists series_observations (
  id uuid primary key default gen_random_uuid(),
  series_id uuid not null references series_catalog(id) on delete cascade,
  date date not null,
  value numeric not null,

  -- Validación / auditoría (ver sección VALIDACIONES del spec):
  -- los valores sospechosos se marcan para revisión, nunca se eliminan solos.
  is_flagged boolean not null default false,
  flag_reason text,

  source_payload jsonb, -- respuesta cruda de la fuente para ese punto, útil para auditoría

  created_at timestamptz not null default now(),

  constraint series_observations_unique unique (series_id, date)
);

comment on table series_observations is
  'Observaciones diarias/periódicas tal como las publica la fuente. No se sobreescriben con datos "corregidos": si la fuente revisa un valor, se actualiza el valor pero se conserva source_payload con la última respuesta.';
comment on column series_observations.is_flagged is
  'true si la observación mostró un cambio extremo respecto del historial reciente. Se marca para revisión manual, no se descarta.';

create index if not exists idx_series_observations_series_date
  on series_observations (series_id, date desc);

-- -----------------------------------------------------------------------------
-- series_ingestion_runs: log de corridas de sincronización
-- -----------------------------------------------------------------------------
-- Necesario para poder mostrar "última actualización" por serie y para
-- diagnosticar errores de descarga sin depender solo de logs de CI.
create table if not exists series_ingestion_runs (
  id uuid primary key default gen_random_uuid(),
  source text not null,                     -- ej: 'BCRA'
  mode text not null,                       -- 'full' | 'incremental'
  series_id uuid references series_catalog(id) on delete set null, -- null = corrida completa
  status text not null,                     -- 'success' | 'error' | 'partial'
  rows_inserted integer not null default 0,
  rows_updated integer not null default 0,
  rows_flagged integer not null default 0,
  error_message text,
  started_at timestamptz not null default now(),
  finished_at timestamptz
);

comment on table series_ingestion_runs is
  'Historial de corridas del sync (scripts/bcra/download.py). Una fila por serie procesada, más registro a nivel corrida cuando series_id es null.';

create index if not exists idx_series_ingestion_runs_series
  on series_ingestion_runs (series_id, started_at desc);

-- -----------------------------------------------------------------------------
-- Trigger genérico para updated_at
-- -----------------------------------------------------------------------------
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_series_catalog_updated_at on series_catalog;
create trigger trg_series_catalog_updated_at
  before update on series_catalog
  for each row execute function set_updated_at();

-- -----------------------------------------------------------------------------
-- Row Level Security
-- -----------------------------------------------------------------------------
-- Lectura pública (la app es un tablero de datos públicos del BCRA), escritura
-- solo con la service_role key (usada exclusivamente por scripts/bcra/*).
alter table series_catalog enable row level security;
alter table series_observations enable row level security;
alter table series_ingestion_runs enable row level security;

drop policy if exists series_catalog_read on series_catalog;
create policy series_catalog_read on series_catalog
  for select using (true);

drop policy if exists series_observations_read on series_observations;
create policy series_observations_read on series_observations
  for select using (true);

drop policy if exists series_ingestion_runs_read on series_ingestion_runs;
create policy series_ingestion_runs_read on series_ingestion_runs
  for select using (true);

-- No se crean políticas de insert/update/delete: sin una policy que lo permita,
-- RLS deniega esas operaciones para roles anon/authenticated. El service_role
-- key usado por los scripts de Python bypassea RLS por diseño de Supabase.
