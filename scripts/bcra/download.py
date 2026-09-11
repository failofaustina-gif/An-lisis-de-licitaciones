#!/usr/bin/env python3
"""
Script único de sincronización con la API de Estadísticas Monetarias del BCRA.

Uso:
  python -m scripts.bcra.download --mode full
      Trae el historial completo disponible para cada serie mapeada en
      config.py. Pensado para el primer bootstrap de la base.

  python -m scripts.bcra.download --mode incremental
      Para cada serie ya presente en series_catalog, busca la última fecha
      guardada en series_observations y pide a la API solo lo posterior
      (?desde=...). Es el modo pensado para correr a diario.

  python -m scripts.bcra.download --list-catalog
      No escribe nada en la base. Imprime el catálogo completo del BCRA
      (idVariable, descripción, frecuencia, unidad) para poder ajustar las
      reglas de scripts/bcra/config.py a mano. Útil para depurar series
      "sin_match" o "ambiguo".

  python -m scripts.bcra.download --mode full --dry-run
      Corre el matching y muestra qué se resolvería, sin escribir en Supabase.

Variables de entorno requeridas (ver .env.example): NEXT_PUBLIC_SUPABASE_URL,
SUPABASE_SERVICE_ROLE_KEY.

Este script SIEMPRE deja un reporte de mapeo en docs/series-mapping-report.md
con el resultado del matching (ok / sin_match / ambiguo) para cada serie
definida en config.py, para que quede documentado qué se pudo resolver
automáticamente y qué requiere revisión manual.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from . import upload
from .bcra_client import BcraApiError, fetch_catalog, fetch_observations
from .config import SERIES_RULES
from .matcher import MatchResult, match_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("bcra_download")

REPORT_PATH = Path(__file__).resolve().parents[2] / "docs" / "series-mapping-report.md"


def write_mapping_report(results: list[MatchResult]) -> None:
    lines = [
        "# Reporte de mapeo de series BCRA",
        "",
        f"Generado automáticamente por `scripts/bcra/download.py` el "
        f"{datetime.now(timezone.utc).isoformat()} (UTC).",
        "",
        "Este archivo se regenera en cada corrida. No editar a mano: para",
        "corregir un mapeo, ajustar `scripts/bcra/config.py` y volver a correr",
        "el script.",
        "",
        "| clave estandarizada | estado | idVariable | descripción original |",
        "|---|---|---|---|",
    ]
    for r in results:
        if r.status == "ok":
            entry = r.matches[0]
            lines.append(f"| `{r.rule.key}` | ok | {entry.id_variable} | {entry.descripcion} |")
        elif r.status == "sin_match":
            lines.append(f"| `{r.rule.key}` | **sin match** | — | — |")
        else:
            candidatos = "; ".join(f"{m.id_variable}: {m.descripcion}" for m in r.matches)
            lines.append(f"| `{r.rule.key}` | **ambiguo ({len(r.matches)} candidatos)** | — | {candidatos} |")

    pending = [r for r in results if r.status != "ok"]
    if pending:
        lines += [
            "",
            "## Pendientes de revisión manual",
            "",
        ]
        for r in pending:
            lines.append(f"- `{r.rule.key}` ({r.rule.category}): {r.status}. {r.rule.notes}")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Reporte de mapeo escrito en %s", REPORT_PATH)


def cmd_list_catalog() -> None:
    catalog = fetch_catalog()
    for entry in sorted(catalog, key=lambda e: e.id_variable):
        print(
            f"{entry.id_variable:>5}  [{entry.periodicidad or '?':>2}]  "
            f"{entry.unidad_expresion or '':<28}  {entry.descripcion}"
        )
    print(f"\nTotal: {len(catalog)} series", file=sys.stderr)


def run_sync(mode: str, dry_run: bool) -> int:
    try:
        catalog = fetch_catalog()
    except BcraApiError as exc:
        logger.error("No se pudo traer el catálogo del BCRA: %s", exc)
        return 1

    results = match_all(SERIES_RULES, catalog)
    write_mapping_report(results)

    resolved = [r for r in results if r.status == "ok"]
    skipped = [r for r in results if r.status != "ok"]
    for r in skipped:
        logger.warning("Serie '%s' quedó sin resolver (%s). Ver docs/series-mapping-report.md", r.rule.key, r.status)

    if not resolved:
        logger.error("Ninguna serie pudo mapearse contra el catálogo real. Revisar config.py.")
        return 1

    if dry_run:
        logger.info("--dry-run: %d series se resolverían, %d quedarían pendientes. No se escribió nada.", len(resolved), len(skipped))
        return 0

    client = upload.get_client()
    exit_code = 0

    for r in resolved:
        entry = r.resolved
        assert entry is not None
        run_started = datetime.now(timezone.utc)
        try:
            catalog_row = upload.upsert_series_catalog(
                client,
                source="BCRA",
                entry=entry,
                display_name=r.rule.key,
                category=r.rule.category,
            )
            series_id = catalog_row["id"]

            desde = None
            if mode == "incremental":
                last_date = upload.get_last_observation_date(client, series_id)
                desde = last_date  # la API incluye la fecha "desde" en el resultado; puede reprocesar el último día sin problema por el upsert

            observations = list(fetch_observations(entry.id_variable, desde=desde))
            count, flagged = upload.upsert_observations(client, series_id, observations)

            upload.log_ingestion_run(
                client,
                source="BCRA",
                mode=mode,
                series_id=series_id,
                status="success",
                rows_inserted=count,
                rows_flagged=flagged,
                started_at=run_started,
            )
            logger.info(
                "OK %-30s idVariable=%-5s filas=%-5d flaggeadas=%d",
                r.rule.key, entry.id_variable, count, flagged,
            )
        except Exception as exc:  # noqa: BLE001 - queremos loguear y seguir con las demás series
            logger.exception("Error sincronizando '%s'", r.rule.key)
            exit_code = 1
            try:
                upload.log_ingestion_run(
                    client,
                    source="BCRA",
                    mode=mode,
                    series_id=None,
                    status="error",
                    error_message=str(exc),
                    started_at=run_started,
                )
            except Exception:  # noqa: BLE001 - no tapar el error original por un fallo de logging
                logger.exception("Además falló el registro del error en series_ingestion_runs")

    return exit_code


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["full", "incremental"], help="Modo de sincronización")
    parser.add_argument("--list-catalog", action="store_true", help="Solo listar el catálogo del BCRA y salir")
    parser.add_argument("--dry-run", action="store_true", help="Correr el matching sin escribir en Supabase")
    args = parser.parse_args()

    if args.list_catalog:
        cmd_list_catalog()
        return 0

    if not args.mode:
        parser.error("--mode full|incremental es requerido (o usar --list-catalog)")

    return run_sync(args.mode, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
