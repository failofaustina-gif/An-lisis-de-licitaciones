"""
Resuelve las SeriesRule de config.py contra un catálogo real (lista de
CatalogEntry) devuelto por bcra_client.fetch_catalog().

Separado de download.py para poder testearlo con catálogos de prueba sin
pegarle a la red.
"""

from __future__ import annotations

from dataclasses import dataclass

from .bcra_client import CatalogEntry
from .config import SeriesRule


@dataclass(frozen=True)
class MatchResult:
    rule: SeriesRule
    matches: tuple[CatalogEntry, ...]

    @property
    def status(self) -> str:
        if len(self.matches) == 1:
            return "ok"
        if len(self.matches) == 0:
            return "sin_match"
        return "ambiguo"

    @property
    def resolved(self) -> CatalogEntry | None:
        return self.matches[0] if len(self.matches) == 1 else None


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def match_rule(rule: SeriesRule, catalog: list[CatalogEntry]) -> MatchResult:
    if rule.exact:
        exact_norm = {_normalize(e) for e in rule.exact}
        exact_matches = tuple(c for c in catalog if _normalize(c.descripcion) in exact_norm)
        if exact_matches:
            return MatchResult(rule=rule, matches=exact_matches)
        # Sin match exacto: si la regla también define `include`, cae a
        # include/exclude como fallback. Si `exact` era el único criterio,
        # NO hay que adivinar matcheando todo el catálogo: se reporta
        # directamente como sin_match.
        if not rule.include:
            return MatchResult(rule=rule, matches=())

    candidates = []
    for entry in catalog:
        desc = _normalize(entry.descripcion)
        if rule.include and not all(term.lower() in desc for term in rule.include):
            continue
        if rule.exclude and any(term.lower() in desc for term in rule.exclude):
            continue
        if not rule.include:
            # No hay `include` (y si había `exact`, ya falló arriba): no hay
            # criterio positivo para incluir esta entrada.
            continue
        candidates.append(entry)

    return MatchResult(rule=rule, matches=tuple(candidates))


def match_all(rules: tuple[SeriesRule, ...], catalog: list[CatalogEntry]) -> list[MatchResult]:
    return [match_rule(rule, catalog) for rule in rules]
