-- =============================================================================
-- seed.sql — Etapa 1
-- =============================================================================
-- A propósito, este archivo NO inserta filas en series_catalog con datos
-- inventados. El catálogo se puebla exclusivamente corriendo:
--
--   python scripts/bcra/download.py --mode full
--
-- que trae el catálogo real desde la API del BCRA (GET /estadisticas/v4.0/monetarias)
-- y lo matchea contra las reglas de scripts/bcra/config.py. Precargar acá IDs
-- de series "a mano" violaría el principio de no inventar/asumir códigos de
-- la fuente.
--
-- Este archivo queda como punto de extensión si más adelante se necesita
-- sembrar datos de prueba (fixtures) para tests automatizados.
-- =============================================================================

select 1; -- no-op intencional
