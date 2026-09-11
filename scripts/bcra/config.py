"""
Capa de mapeo: qué series estandarizadas quiere tener la app y cómo
encontrarlas dentro del catálogo real del BCRA.

Por qué reglas de matching y no una lista de idVariable hardcodeada:
  El pedido original es explícito en no asumir que las variables tienen
  "exactamente esos nombres" en la fuente, y en no inventar identificadores.
  La única fuente de verdad para un idVariable es la respuesta en vivo de
  `GET /estadisticas/v4.0/monetarias`. Este archivo define, por cada
  variable estandarizada que la app necesita, un criterio de búsqueda sobre
  el campo `descripcion` de esa respuesta. El script de sync (download.py)
  aplica estas reglas contra el catálogo real y recién ahí resuelve el
  idVariable correspondiente.

Qué pasa si una regla matchea 0 o más de 1 serie:
  download.py NO adivina. Registra el caso en el reporte de mapeo
  (docs/series-mapping-report.md, generado automáticamente) para que se
  ajuste la regla acá a mano, revisando el catálogo real.

Cómo agregar/ajustar una serie:
  1. Correr `python scripts/bcra/download.py --list-catalog` para ver las
     descripciones reales tal como las publica el BCRA hoy.
  2. Agregar o ajustar un SeriesRule acá.
  3. Volver a correr `download.py --mode full` (es idempotente).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SeriesRule:
    key: str  # nombre estandarizado interno, ej. "base_monetaria"
    category: str  # agrupación usada en la UI
    include: tuple[str, ...] = field(default_factory=tuple)  # substrings (case-insensitive) que TODOS deben aparecer en descripcion
    exclude: tuple[str, ...] = field(default_factory=tuple)  # substrings que NO deben aparecer
    exact: tuple[str, ...] = field(default_factory=tuple)  # si se define, matchea por igualdad exacta (case-insensitive, trim) contra alguna de estas opciones
    notes: str = ""


# Categorías estandarizadas usadas en series_catalog.category / la UI.
CATEGORY_AGREGADOS = "agregados_monetarios"
CATEGORY_RESERVAS = "reservas_internacionales"
CATEGORY_LIQUIDEZ = "liquidez_sistema_financiero"
CATEGORY_TASAS = "tasas_monetarias"

# -----------------------------------------------------------------------------
# Reglas mínimas pedidas: base monetaria, circulante, billetes y monedas en
# poder del público, depósitos en pesos, depósitos privados, M1, M2, M3,
# reservas internacionales, liquidez del sistema financiero, tasas relevantes.
# -----------------------------------------------------------------------------
SERIES_RULES: tuple[SeriesRule, ...] = (
    SeriesRule(
        key="base_monetaria",
        category=CATEGORY_AGREGADOS,
        exact=("Base monetaria - Total (en millones de pesos)", "Base monetaria"),
        include=("base monetaria",),
        notes="Base monetaria total. Si el BCRA publica aperturas (BCRA vs. otros), "
        "esta regla debe ajustarse para apuntar al total.",
    ),
    SeriesRule(
        key="circulante",
        category=CATEGORY_AGREGADOS,
        include=("circula",),
        exclude=("interanual", "variación", "%"),
        notes="'Circulación monetaria'. Puede haber más de un candidato "
        "(circulación monetaria vs. billetes y monedas en poder del público); "
        "si matchea más de uno, desambiguar acá con `exact`.",
    ),
    SeriesRule(
        key="billetes_monedas_publico",
        category=CATEGORY_AGREGADOS,
        include=("billetes y monedas", "público"),
    ),
    SeriesRule(
        key="depositos_pesos",
        category=CATEGORY_AGREGADOS,
        include=("depósito", "peso"),
        exclude=("interanual", "variación", "%", "plazo fijo en usd", "dólares"),
        notes="Ambiguo a propósito: el BCRA puede tener varias aperturas de "
        "depósitos en pesos (vista, plazo fijo, total). Revisar el reporte "
        "de mapeo y afinar con `exact` una vez visto el catálogo real.",
    ),
    SeriesRule(
        key="depositos_sector_privado",
        category=CATEGORY_AGREGADOS,
        include=("depósito", "privado"),
        exclude=("interanual", "variación", "%"),
    ),
    SeriesRule(
        key="m1",
        category=CATEGORY_AGREGADOS,
        exact=("M1",),
        notes="Match exacto para evitar caer en 'M1 privado' u otras aperturas.",
    ),
    SeriesRule(
        key="m2",
        category=CATEGORY_AGREGADOS,
        exact=("M2",),
    ),
    SeriesRule(
        key="m3",
        category=CATEGORY_AGREGADOS,
        exact=("M3",),
    ),
    SeriesRule(
        key="reservas_internacionales",
        category=CATEGORY_RESERVAS,
        include=("reservas internacionales",),
        exclude=("exclu",),  # evita variantes tipo "excluidas asignaciones DEG"
    ),
    SeriesRule(
        key="efectivo_entidades_financieras",
        category=CATEGORY_LIQUIDEZ,
        include=("efectivo en entidades financieras",),
        notes="Proxy de liquidez bancaria en efectivo. Revisar si el BCRA "
        "expone además una serie explícita de 'liquidez' o 'integración de "
        "efectivo mínimo' y agregarla acá.",
    ),
    SeriesRule(
        key="tasa_politica_monetaria",
        category=CATEGORY_TASAS,
        include=("tasa de política monetaria",),
    ),
    SeriesRule(
        key="badlar_privados",
        category=CATEGORY_TASAS,
        include=("badlar", "privados"),
    ),
    SeriesRule(
        key="tamar",
        category=CATEGORY_TASAS,
        include=("tamar",),
    ),
    SeriesRule(
        key="call_interbancario",
        category=CATEGORY_TASAS,
        include=("call",),
    ),
)


def rule_by_key(key: str) -> SeriesRule | None:
    for rule in SERIES_RULES:
        if rule.key == key:
            return rule
    return None
