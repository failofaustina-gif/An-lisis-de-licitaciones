"""
Capa de escritura a Supabase. Usa exclusivamente la service_role key
(nunca la anon key) porque necesita bypassear RLS para insertar/actualizar
series_catalog y series_observations (ver database/schema.sql: no hay
policies de insert/update para anon/authenticated a propósito).

Requiere las variables de entorno:
  NEXT_PUBLIC_SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timezone
from typing import Any

from supabase import create_client, Client

from .bcra_client import CatalogEntry, Observation
from .transform import is_extreme_change

logger = logging.getLogger("bcra_upload")


class ConfigError(RuntimeError):
    pass


def get_client() -> Client:
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ConfigError(
            "Faltan NEXT_PUBLIC_SUPABASE_URL y/o SUPABASE_SERVICE_ROLE_KEY en el entorno. "
            "Ver .env.example."
        )
    return create_client(url, key)


def upsert_series_catalog(
    client: Client,
    *,
    source: str,
    entry: CatalogEntry,
    display_name: str,
    category: str,
) -> dict[str, Any]:
    """Crea o actualiza la fila de catálogo para una serie. El
    source_series_id sale siempre de `entry` (dato real de la API), nunca
    de un valor fijo en el código.
    """
    row = {
        "source": source,
        "source_series_id": str(entry.id_variable),
        "original_name": entry.descripcion,
        "display_name": display_name,
        "category": category,
        "frequency": entry.periodicidad or "desconocida",
        "unit": entry.unidad_expresion or "sin especificar",
        "description": entry.tipo_serie,
        "active": True,
        "metadata": {
            "categoria_bcra": entry.categoria,
            "moneda": entry.moneda,
            "primer_fecha_informada": entry.primera_fecha_informada,
            "ultima_fecha_informada": entry.ultima_fecha_informada,
        },
    }
    result = (
        client.table("series_catalog")
        .upsert(row, on_conflict="source,source_series_id")
        .execute()
    )
    data = result.data
    if not data:
        raise RuntimeError(f"Upsert de series_catalog no devolvió fila para {display_name}")
    return data[0]


def get_last_observation_date(client: Client, series_id: str) -> str | None:
    result = (
        client.table("series_observations")
        .select("date")
        .eq("series_id", series_id)
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["date"]
    return None


def get_recent_values(client: Client, series_id: str, limit: int = 30) -> list[float]:
    result = (
        client.table("series_observations")
        .select("date,value")
        .eq("series_id", series_id)
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    rows = sorted(result.data, key=lambda r: r["date"])
    return [float(r["value"]) for r in rows]


def upsert_observations(
    client: Client,
    series_id: str,
    observations: list[Observation],
    *,
    batch_size: int = 500,
) -> tuple[int, int]:
    """Inserta/actualiza observaciones. Devuelve (cantidad, cantidad_flaggeadas).

    Duplicados de (series_id, date) se resuelven con upsert sobre la unique
    constraint definida en el schema: no se insertan filas repetidas.
    """
    if not observations:
        return 0, 0

    history = get_recent_values(client, series_id, limit=60)
    flagged_count = 0
    rows: list[dict[str, Any]] = []

    for obs in sorted(observations, key=lambda o: o.fecha):
        value = float(obs.valor)
        is_flagged, reason = is_extreme_change(history, value)
        if is_flagged:
            flagged_count += 1
            logger.warning("Valor sospechoso series_id=%s fecha=%s: %s", series_id, obs.fecha, reason)
        rows.append(
            {
                "series_id": series_id,
                "date": obs.fecha,
                "value": value,
                "is_flagged": is_flagged,
                "flag_reason": reason,
                "source_payload": obs.raw,
            }
        )
        history.append(value)

    total = 0
    for i in range(0, len(rows), batch_size):
        chunk = rows[i : i + batch_size]
        client.table("series_observations").upsert(
            chunk, on_conflict="series_id,date"
        ).execute()
        total += len(chunk)

    return total, flagged_count


def log_ingestion_run(
    client: Client,
    *,
    source: str,
    mode: str,
    series_id: str | None,
    status: str,
    rows_inserted: int = 0,
    rows_flagged: int = 0,
    error_message: str | None = None,
    started_at: datetime | None = None,
) -> None:
    client.table("series_ingestion_runs").insert(
        {
            "source": source,
            "mode": mode,
            "series_id": series_id,
            "status": status,
            "rows_inserted": rows_inserted,
            "rows_updated": 0,
            "rows_flagged": rows_flagged,
            "error_message": error_message,
            "started_at": (started_at or datetime.now(timezone.utc)).isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()
