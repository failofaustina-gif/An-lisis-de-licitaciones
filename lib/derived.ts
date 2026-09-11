import type { SeriesObservationRow } from "./supabase/types";

/**
 * Cálculos derivados sobre observaciones YA cargadas en memoria. A
 * propósito, nada de esto se guarda en la base (ver database/schema.sql):
 * se recalcula acá cada vez que se necesita, para no duplicar datos que
 * son triviales de derivar del dato crudo.
 *
 * La lógica de "cambio extremo" para validación vive en Python
 * (scripts/bcra/transform.py) porque corre en el pipeline de ingesta, no
 * en el frontend; si en algún momento hace falta el mismo criterio acá,
 * portar esa función en vez de reimplementarla distinto.
 */

export interface DerivedPoint {
  date: string;
  value: number;
  diffAbs: number | null;
  diffPct: number | null;
}

/** Variación absoluta y porcentual respecto de la observación anterior. */
export function withDailyChange(observations: SeriesObservationRow[]): DerivedPoint[] {
  const sorted = [...observations].sort((a, b) => a.date.localeCompare(b.date));
  return sorted.map((obs, i) => {
    const prev = i > 0 ? sorted[i - 1] : undefined;
    if (!prev) {
      return { date: obs.date, value: obs.value, diffAbs: null, diffPct: null };
    }
    const diffAbs = obs.value - prev.value;
    const diffPct = prev.value !== 0 ? (diffAbs / Math.abs(prev.value)) * 100 : null;
    return { date: obs.date, value: obs.value, diffAbs, diffPct };
  });
}

/**
 * Variación porcentual entre el último valor disponible y el valor de N
 * observaciones hacia atrás (no N días de calendario: N puntos de la
 * serie, que es lo que corresponde para series diarias con feriados).
 * Devuelve null si no hay suficiente historial.
 */
export function changeOverLastN(
  observations: SeriesObservationRow[],
  n: number
): { diffAbs: number; diffPct: number | null } | null {
  const sorted = [...observations].sort((a, b) => a.date.localeCompare(b.date));
  if (sorted.length <= n) return null;

  const last = sorted[sorted.length - 1]!; // length > n >= 0 fue chequeado arriba
  const reference = sorted[sorted.length - 1 - n]!;
  const diffAbs = last.value - reference.value;
  const diffPct = reference.value !== 0 ? (diffAbs / Math.abs(reference.value)) * 100 : null;
  return { diffAbs, diffPct };
}

/** Media móvil simple de `window` observaciones. */
export function simpleMovingAverage(
  observations: SeriesObservationRow[],
  window: number
): { date: string; value: number }[] {
  const sorted = [...observations].sort((a, b) => a.date.localeCompare(b.date));
  const result: { date: string; value: number }[] = [];

  for (let i = window - 1; i < sorted.length; i++) {
    const slice = sorted.slice(i - window + 1, i + 1);
    const avg = slice.reduce((sum, o) => sum + o.value, 0) / slice.length;
    result.push({ date: sorted[i]!.date, value: avg });
  }
  return result;
}
