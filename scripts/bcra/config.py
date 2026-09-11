"""
Capa de mapeo: qué series estandarizadas quiere tener la app y cómo
encontrarlas dentro del catálogo real del BCRA.

Por qué reglas de matching y no una lista de idVariable hardcodeada:
  El pedido original es explícito en no asumir que las variables tienen
  "exactamente esos nombres" en la fuente, y en no inventar identificadores.
  La única fuente de verdad para un idVariable es la respuesta en vivo de
  `GET /estadisticas/v4.0/monetarias`. Este archivo define, por cada
  variable estandarizada que la app necesita, un criterio de búsqueda sobre
  el campo `descripcion` (y, cuando hace falta desambiguar duplicados con la
  misma descripción, el campo `categoria`) de esa respuesta. El script de
  sync (download.py) aplica estas reglas contra el catálogo real y recién
  ahí resuelve el idVariable correspondiente.

Qué pasa si una regla matchea 0 o más de 1 serie:
  download.py NO adivina. Registra el caso en el reporte de mapeo
  (docs/series-mapping-report.md, generado automáticamente) para que se
  ajuste la regla acá a mano, revisando el catálogo real.

Nota sobre `categoria_bcra`:
  El catálogo del BCRA a veces republica la MISMA serie (idéntica
  `descripcion`) bajo varios `idVariable` distintos, agrupados en distintas
  `categoria` (ej. "Principales Variables" vs "Series.xlsm" vs "Activos y
  pasivos del BCRA" vs una versión mensual en "Agregados monetarios y sus
  componentes"). Verificado a mano contra el catálogo real (2026-09-11):
  quedarse con la que está en categoría "Principales Variables" da, en cada
  caso verificado, la serie diaria vigente (mismo valor que sus duplicados,
  actualizada al día). `categoria_bcra`, si se define, filtra los
  candidatos por ese campo antes de decidir si hay 0, 1 o más de 1 match.
  Nunca se usa para elegir "a ciegas" entre candidatos con VALORES
  distintos (ver badlar_privados y tamar más abajo): ahí se usa solo para
  acotar la lista de candidatos, no para resolver la ambigüedad.

Cómo agregar/ajustar una serie:
  1. Correr `python -m scripts.bcra.download --list-catalog` para ver las
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
    categoria_bcra: tuple[str, ...] = field(default_factory=tuple)  # filtra candidatos por el campo `categoria` del catálogo BCRA (ver nota arriba). No confundir con `category` (la categoría estandarizada de la app).
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
        include=("base monetaria",),
        categoria_bcra=("Principales Variables",),
        notes="Verificado 2026-09-11: idVariable 15. El catálogo repite "
        "'Base monetaria' bajo otros 4 idVariable (64, 71, 1248, 1606) en "
        "otras categorías del BCRA (variación diaria, re-listado en "
        "'Activos y pasivos del BCRA', o versión mensual); 'Principales "
        "Variables' es la serie diaria vigente que usa la app.",
    ),
    SeriesRule(
        key="circulante",
        category=CATEGORY_AGREGADOS,
        include=("circula",),
        exclude=("interanual", "variación", "%"),
        categoria_bcra=("Principales Variables",),
        notes="Verificado 2026-09-11: idVariable 16. Mismo patrón de "
        "duplicados que base_monetaria (ver esa nota).",
    ),
    SeriesRule(
        key="billetes_monedas_publico",
        category=CATEGORY_AGREGADOS,
        include=("billetes y monedas", "público"),
        categoria_bcra=("Principales Variables",),
        notes="Verificado 2026-09-11: idVariable 17. Mismo patrón de "
        "duplicados que base_monetaria (ver esa nota).",
    ),
    SeriesRule(
        key="depositos_pesos",
        category=CATEGORY_AGREGADOS,
        exact=("Depósitos en pesos de los sectores público y privados no financieros (incluye cedros)",),
        notes="Verificado 2026-09-11: idVariable 91. El include genérico "
        "anterior ('depósito' + 'peso') matcheaba también series de tasas "
        "de interés de depósitos a plazo fijo y otras que no son el saldo "
        "de depósitos en sí. Se deja como match exacto sobre la única "
        "serie del catálogo que es literalmente 'depósitos en pesos' "
        "(sectores público y privado no financieros, incluye cedros).",
    ),
    SeriesRule(
        key="depositos_sector_privado",
        category=CATEGORY_AGREGADOS,
        exact=("Depósitos totales del sector privado",),
        categoria_bcra=("Depósitos por cuenta",),
        notes="Verificado 2026-09-11: idVariable 1526, diaria y vigente. "
        "El catálogo tiene 51 candidatos para 'depósito' + 'privado' "
        "(aperturas por plazo, por moneda, por tipo de cuenta, mensuales "
        "vs. diarias). Se eligió la serie diaria de total agregado; las "
        "aperturas específicas quedan fuera del alcance de esta variable "
        "estandarizada.",
    ),
    SeriesRule(
        key="m1",
        category=CATEGORY_AGREGADOS,
        exact=("M1 en moneda local",),
        categoria_bcra=("Agregados monetarios y sus componentes",),
        notes="Verificado 2026-09-11: idVariable 1612, mensual. A "
        "diferencia de M2 (que tiene una serie diaria con descripción "
        "exacta 'M2'), el catálogo no tiene ninguna serie M1 con "
        "descripción corta. La única M1 diaria ('Informe Monetario "
        "Diario', idVariable 1232) dejó de actualizarse en mayo 2026 (BCRA "
        "parece haber discontinuado ese informe); se usa en su lugar la "
        "versión mensual vigente, en moneda local (excluye la variante "
        "'M1 en moneda local y extranjera').",
    ),
    SeriesRule(
        key="m2",
        category=CATEGORY_AGREGADOS,
        exact=("M2",),
    ),
    SeriesRule(
        key="m3",
        category=CATEGORY_AGREGADOS,
        exact=("M3 en moneda local",),
        categoria_bcra=("Agregados monetarios y sus componentes",),
        notes="Verificado 2026-09-11: idVariable 1624, mensual. Mismo "
        "motivo que m1: la serie diaria de 'Informe Monetario Diario' "
        "(idVariable 1234) dejó de actualizarse en mayo 2026.",
    ),
    SeriesRule(
        key="reservas_internacionales",
        category=CATEGORY_RESERVAS,
        include=("reservas internacionales",),
        exclude=("exclu",),  # evita variantes tipo "excluidas asignaciones DEG"
        categoria_bcra=("Principales Variables",),
        notes="Verificado 2026-09-11: idVariable 1. Mismo patrón de "
        "duplicados que base_monetaria (ver esa nota).",
    ),
    SeriesRule(
        key="efectivo_entidades_financieras",
        category=CATEGORY_LIQUIDEZ,
        include=("efectivo en entidades financieras",),
        categoria_bcra=("Principales Variables",),
        notes="Verificado 2026-09-11: idVariable 18. Proxy de liquidez "
        "bancaria en efectivo. Revisar si el BCRA expone además una serie "
        "explícita de 'liquidez' o 'integración de efectivo mínimo' y "
        "agregarla acá.",
    ),
    SeriesRule(
        key="tasa_politica_monetaria",
        category=CATEGORY_TASAS,
        include=("tasa de política monetaria",),
        notes="Verificado 2026-09-11: sin serie vigente. Los únicos "
        "candidatos parecidos en el catálogo (idVariable 160 y 161, "
        "'Tasas de interés de política monetaria') dejaron de actualizarse "
        "en julio 2025 — el BCRA aparenta haber discontinuado esta serie "
        "al cambiar de esquema de política monetaria. Pendiente: decidir "
        "si se deja sin dato, o se reemplaza el concepto por la tasa que "
        "el BCRA use actualmente como referencia de política (a "
        "confirmar).",
    ),
    SeriesRule(
        key="badlar_privados",
        category=CATEGORY_TASAS,
        include=("badlar", "privados"),
        categoria_bcra=("Principales Variables",),
        notes="PENDIENTE DE CONFIRMAR A MANO (no resuelto automáticamente "
        "a propósito). El catálogo tiene 2 series activas en 'Principales "
        "Variables' con la MISMA descripción ('Tasa de interés BADLAR de "
        "bancos privados') pero valores distintos el 2026-09-09: "
        "idVariable 7 = 22.4375%, idVariable 35 = 24.88%. No hay forma de "
        "distinguir cuál es 'la' oficial solo con los metadatos del "
        "catálogo. Una vez confirmado cuál corresponde, agregar acá "
        "`exact=(\"Tasa de interés BADLAR de bancos privados\",)` no "
        "alcanza para desambiguar (las dos tienen el mismo texto): hay que "
        "fijar el idVariable a mano editando `bcra_client.py` o agregando "
        "un filtro adicional por idVariable en el matcher.",
    ),
    SeriesRule(
        key="tamar",
        category=CATEGORY_TASAS,
        include=("tamar", "bancos"),
        categoria_bcra=("Principales Variables",),
        notes="PENDIENTE DE CONFIRMAR A MANO (mismo caso que "
        "badlar_privados). Bug corregido 2026-09-11: el include anterior "
        "(solo 'tamar') matcheaba también series de la provincia de "
        "'CaTAMARca'; se agregó 'bancos' como segundo término requerido. "
        "El catálogo tiene 2 series activas en 'Principales Variables' con "
        "valores distintos el 2026-09-09: idVariable 44 ('Tasa de interes "
        "TAMAR...', sin tilde) = 23.5625%, idVariable 45 ('Tasa de interés "
        "TAMAR...', con tilde) = 26.27%.",
    ),
    SeriesRule(
        key="call_interbancario",
        category=CATEGORY_TASAS,
        include=("call",),
        notes="Verificado 2026-09-11: sin ningún candidato en el catálogo "
        "actual (cero series con 'call' en la descripción). El BCRA no "
        "parece publicar hoy una serie con este nombre; pendiente "
        "investigar bajo qué otro nombre podría estar publicada la tasa "
        "call interbancaria, si es que sigue existiendo.",
    ),
)


def rule_by_key(key: str) -> SeriesRule | None:
    for rule in SERIES_RULES:
        if rule.key == key:
            return rule
    return None
