"""
Transformaciones sobre observaciones YA descargadas.

Importante: estas funciones se usan hoy solo para VALIDACIÓN (detectar
cambios extremos antes de guardar, ver upload.py). No se usan para escribir
variables derivadas en la base — esas se calculan en el frontend
(lib/derived.ts) a partir de series_observations, para no duplicar
información que se puede recalcular fácilmente.

Si en una etapa futura el volumen de datos justifica materializar
derivados (por performance), este es el módulo donde debería vivir esa
lógica, reutilizando estas mismas funciones.
"""

from __future__ import annotations

import statistics


def pct_change(previous: float, current: float) -> float | None:
    """Variación porcentual entre dos observaciones consecutivas."""
    if previous == 0:
        return None
    return (current - previous) / abs(previous) * 100.0


def is_extreme_change(
    history: list[float],
    new_value: float,
    z_threshold: float = 4.0,
    min_history: int = 10,
) -> tuple[bool, str | None]:
    """Marca un valor como sospechoso si se aleja demasiado de la
    distribución de variaciones diarias recientes (z-score sobre las
    diferencias día a día), no del nivel de la serie.

    Devuelve (es_extremo, motivo). No decide "correcto/incorrecto": solo
    señala para revisión manual, tal como pide el spec.
    """
    if len(history) < min_history:
        return False, None

    diffs = [b - a for a, b in zip(history, history[1:])]
    if len(diffs) < 2:
        return False, None

    mean = statistics.fmean(diffs)
    try:
        stdev = statistics.stdev(diffs)
    except statistics.StatisticsError:
        return False, None

    new_diff = new_value - history[-1]

    if stdev == 0:
        # Historial con variación diaria perfectamente constante: cualquier
        # apartamiento de ese patrón ya es, por definición, una anomalía
        # (no hay forma de calcular un z-score con desvío 0).
        if new_diff != mean:
            return True, f"variación diaria {new_diff:g} rompe un patrón constante de {mean:g}"
        return False, None

    z = (new_diff - mean) / stdev
    if abs(z) >= z_threshold:
        return True, f"variación diaria con z-score={z:.2f} (umbral={z_threshold})"
    return False, None
