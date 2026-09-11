"""
Cliente para la API pública de Estadísticas Monetarias del BCRA (v4.0).

Fuente oficial documentada:
  - Catálogo de APIs del BCRA: https://www.bcra.gob.ar/en/central-bank-api-catalog/
  - Manual técnico "Variables Monetarias v4.0":
    https://www.bcra.gob.ar/archivos/Catalogo/Content/files/pdf/principales-variables-v4.pdf
  - Espejo interactivo (Swagger) del mismo manual:
    https://principales-variables.bcra.apidocs.ar/

Base URL: https://api.bcra.gob.ar/estadisticas/v4.0
No requiere autenticación. El BCRA aplica control de tráfico por IP
(rate limiting), sin límites publicados en el manual al momento de escribir
esto — por eso este cliente pagina con cuidado y no dispara requests en
paralelo.

IMPORTANTE — no inventar endpoints:
  Este módulo solo usa los tres endpoints documentados en el manual v4.0:
    GET /monetarias
    GET /monetarias/{idVariable}
    GET /metodologia[/{id}]
  Cualquier extensión debe volver a chequear el manual oficial, no asumir.

Nota sobre certificados TLS:
  Distintas integraciones de terceros con APIs de bcra.gob.ar reportaron
  históricamente problemas de verificación de certificado (cadena de
  confianza gubernamental no incluida en algunos bundles de CAs). Por
  default este cliente verifica TLS normalmente (verify=True). Si en tu
  entorno falla con un SSLError, primero actualizá el paquete `certifi`
  antes de desactivar la verificación. Como último recurso, se puede
  setear la variable de entorno BCRA_TLS_INSECURE=1, pero no se recomienda
  para uso en CI/producción.
"""

from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass
from typing import Any, Iterator

import requests

logger = logging.getLogger("bcra_client")

BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0"

DEFAULT_TIMEOUT = float(os.environ.get("BCRA_HTTP_TIMEOUT", "30"))
_TLS_INSECURE = os.environ.get("BCRA_TLS_INSECURE", "0") == "1"

# Límite máximo de registros por página según el manual v4.0.
MAX_LIMIT_MONETARIAS_DETALLE = 3000
DEFAULT_LIMIT_CATALOGO = 1000


class BcraApiError(RuntimeError):
    """Error de negocio devuelto por la API (status != 200) o de transporte."""


@dataclass(frozen=True)
class CatalogEntry:
    """Una fila cruda del catálogo de /monetarias, sin transformar."""

    id_variable: int
    descripcion: str
    categoria: str | None
    tipo_serie: str | None
    periodicidad: str | None
    unidad_expresion: str | None
    moneda: str | None
    primera_fecha_informada: str | None
    ultima_fecha_informada: str | None
    ultimo_valor_informado: float | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class Observation:
    """Un punto (fecha, valor) tal como lo devuelve la fuente."""

    fecha: str
    valor: float
    raw: dict[str, Any]


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "Accept": "application/json",
            "Accept-Language": "es-AR",
            "Accept-Encoding": "gzip",
            "User-Agent": "monitor-monetario-argentina/0.1 (+scripts/bcra)",
        }
    )
    return s


def _get(session: requests.Session, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    verify = not _TLS_INSECURE
    if _TLS_INSECURE:
        logger.warning("BCRA_TLS_INSECURE=1: verificación TLS deshabilitada para %s", url)

    last_exc: Exception | None = None
    for attempt in range(1, 4):
        try:
            resp = session.get(url, params=params, timeout=DEFAULT_TIMEOUT, verify=verify)
        except requests.RequestException as exc:  # errores de red/timeout
            last_exc = exc
            logger.warning("Intento %s/3 falló para %s: %s", attempt, url, exc)
            time.sleep(1.5 * attempt)
            continue

        if resp.status_code == 200:
            return resp.json()

        # 4xx no tiene sentido reintentarlo (parámetro mal formado, id inválido, etc.)
        if 400 <= resp.status_code < 500:
            body = _safe_json(resp)
            raise BcraApiError(
                f"BCRA API {resp.status_code} en {url} params={params}: {body}"
            )

        # 5xx: reintentar con backoff
        logger.warning("BCRA API %s en %s (intento %s/3)", resp.status_code, url, attempt)
        time.sleep(1.5 * attempt)

    raise BcraApiError(f"No se pudo obtener {url} tras 3 intentos: {last_exc}")


def _safe_json(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except ValueError:
        return resp.text[:500]


def fetch_catalog(session: requests.Session | None = None) -> list[CatalogEntry]:
    """Trae el catálogo COMPLETO de variables monetarias (paginado).

    Este es el único lugar donde la app "descubre" qué series existen y con
    qué idVariable. No hay ningún idVariable hardcodeado en el resto del
    proyecto: todo pasa por acá.
    """
    session = session or _session()
    entries: list[CatalogEntry] = []
    offset = 0
    while True:
        payload = _get(
            session,
            "/monetarias",
            params={"offset": offset, "limit": DEFAULT_LIMIT_CATALOGO},
        )
        results = payload.get("results", [])
        for row in results:
            entries.append(
                CatalogEntry(
                    id_variable=row["idVariable"],
                    descripcion=row.get("descripcion", "").strip(),
                    categoria=row.get("categoria"),
                    tipo_serie=row.get("tipoSerie"),
                    periodicidad=row.get("periodicidad"),
                    unidad_expresion=row.get("unidadExpresion"),
                    moneda=row.get("moneda"),
                    primera_fecha_informada=row.get("primerFechaInformada"),
                    ultima_fecha_informada=row.get("ultFechaInformada"),
                    ultimo_valor_informado=row.get("ultValorInformado"),
                    raw=row,
                )
            )
        resultset = payload.get("metadata", {}).get("resultset", {})
        count = resultset.get("count", len(entries))
        offset += DEFAULT_LIMIT_CATALOGO
        if offset >= count or not results:
            break
    logger.info("Catálogo BCRA: %d series encontradas", len(entries))
    return entries


def fetch_observations(
    id_variable: int,
    desde: str | None = None,
    hasta: str | None = None,
    session: requests.Session | None = None,
) -> Iterator[Observation]:
    """Trae observaciones históricas de una serie, paginando de a
    MAX_LIMIT_MONETARIAS_DETALLE registros.

    desde/hasta: strings 'YYYY-MM-DD' (ISO 8601), o None para traer todo el
    historial disponible (usado en la carga 'full').
    """
    session = session or _session()
    offset = 0
    while True:
        params: dict[str, Any] = {
            "offset": offset,
            "limit": MAX_LIMIT_MONETARIAS_DETALLE,
        }
        if desde:
            params["desde"] = desde
        if hasta:
            params["hasta"] = hasta

        payload = _get(session, f"/monetarias/{id_variable}", params=params)
        results = payload.get("results", [])
        if not results:
            break

        # La API devuelve una lista de resultados con un único elemento por
        # idVariable, cada uno con su lista `detalle` de {fecha, valor}.
        detalle: list[dict[str, Any]] = []
        for row in results:
            detalle.extend(row.get("detalle", []))

        if not detalle:
            break

        for point in detalle:
            yield Observation(fecha=point["fecha"], valor=point["valor"], raw=point)

        resultset = payload.get("metadata", {}).get("resultset", {})
        count = resultset.get("count", len(detalle))
        offset += MAX_LIMIT_MONETARIAS_DETALLE
        if offset >= count:
            break
