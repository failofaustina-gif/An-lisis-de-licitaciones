"""
Tests del matcher usando un catálogo SINTÉTICO (no son datos reales del
BCRA, salvo la fila idVariable=1 que reproduce el ejemplo textual del
manual oficial v4.0 para 'Reservas internacionales'). Sirve para validar
la lógica de matching sin depender de la red.
"""

from __future__ import annotations

import unittest

from ..bcra_client import CatalogEntry
from ..config import SeriesRule
from ..matcher import match_all, match_rule


def _entry(id_variable: int, descripcion: str, **kwargs) -> CatalogEntry:
    return CatalogEntry(
        id_variable=id_variable,
        descripcion=descripcion,
        categoria=kwargs.get("categoria", "Principales Variables"),
        tipo_serie=kwargs.get("tipo_serie", "Saldos"),
        periodicidad=kwargs.get("periodicidad", "D"),
        unidad_expresion=kwargs.get("unidad_expresion", "En millones de pesos"),
        moneda=kwargs.get("moneda", "ML"),
        primera_fecha_informada=kwargs.get("primera_fecha_informada"),
        ultima_fecha_informada=kwargs.get("ultima_fecha_informada"),
        ultimo_valor_informado=kwargs.get("ultimo_valor_informado"),
        raw={},
    )


FAKE_CATALOG = [
    _entry(1, "Reservas internacionales", unidad_expresion="En millones de USD", moneda="ME"),
    _entry(74, "Reservas internacionales (excluidas asignaciones DEG 2009)", unidad_expresion="En millones de USD", moneda="ME"),
    _entry(15, "Base monetaria - Total (en millones de pesos)"),
    _entry(16, "Circulación monetaria"),
    _entry(17, "Billetes y monedas en poder del público"),
    _entry(109, "M2"),
    _entry(200, "M2 privado"),
    # Deliberadamente NO incluye M1 ni M3 para probar el caso "sin_match".
]


class MatchRuleTests(unittest.TestCase):
    def test_exact_match_single_candidate(self):
        rule = SeriesRule(key="reservas_internacionales", category="x", include=("reservas internacionales",), exclude=("exclu",))
        result = match_rule(rule, FAKE_CATALOG)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.resolved.id_variable, 1)

    def test_exact_rule_prefers_exact_over_substring(self):
        rule = SeriesRule(key="m2", category="x", exact=("M2",))
        result = match_rule(rule, FAKE_CATALOG)
        # Sin la regla `exact`, "M2" e "M2 privado" matchearían ambas por
        # substring. Con `exact`, debe resolver únicamente a idVariable=109.
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.resolved.id_variable, 109)

    def test_no_match_reported_not_guessed(self):
        rule = SeriesRule(key="m1", category="x", exact=("M1",))
        result = match_rule(rule, FAKE_CATALOG)
        self.assertEqual(result.status, "sin_match")
        self.assertIsNone(result.resolved)

    def test_ambiguous_without_exact_rule(self):
        rule = SeriesRule(key="circulante_amplio", category="x", include=("circula",))
        # "Circulación monetaria" es el único que matchea "circula" en este
        # catálogo de prueba -> debería ser 'ok', no ambiguo.
        result = match_rule(rule, FAKE_CATALOG)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.resolved.id_variable, 16)

    def test_match_all_runs_every_rule(self):
        rules = (
            SeriesRule(key="base_monetaria", category="x", exact=("Base monetaria",), include=("base monetaria",)),
            SeriesRule(key="m3", category="x", exact=("M3",)),
        )
        results = match_all(rules, FAKE_CATALOG)
        self.assertEqual(len(results), 2)
        statuses = {r.rule.key: r.status for r in results}
        self.assertEqual(statuses["base_monetaria"], "ok")
        self.assertEqual(statuses["m3"], "sin_match")


if __name__ == "__main__":
    unittest.main()
