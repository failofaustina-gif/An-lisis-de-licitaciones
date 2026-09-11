import { getSeriesByDisplayName, getObservations } from "./series";
import type { SeriesObservationRow } from "./supabase/types";

/**
 * PBI cargado a mano (el BCRA no lo publica). Vive en series_catalog con
 * source='manual', display_name=PBI_DISPLAY_NAME, mismo esquema que
 * cualquier otra serie — así el resto de la lectura (lib/series.ts) no
 * necesita ningún caso especial.
 */
export const PBI_DISPLAY_NAME = "pbi_nominal";

export async function getPbiObservations(): Promise<SeriesObservationRow[]> {
  const series = await getSeriesByDisplayName(PBI_DISPLAY_NAME);
  if (!series) return [];
  return getObservations(series.id);
}

export interface PbiReference {
  value: number; // valor del trimestre tal como se cargó (sin anualizar)
  quarterDate: string; // fecha de ese trimestre
}

/**
 * Trimestre de PBI más reciente con fecha <= date. Devuelve null si no
 * hay ningún dato de PBI con fecha <= date.
 */
export function pbiReferenceAsOf(
  date: string,
  pbiObservations: SeriesObservationRow[]
): PbiReference | null {
  let best: SeriesObservationRow | null = null;
  for (const obs of pbiObservations) {
    if (obs.date <= date && (!best || obs.date > best.date)) {
      best = obs;
    }
  }
  return best ? { value: best.value, quarterDate: best.date } : null;
}

/**
 * PBI anualizado "as of" una fecha: toma el trimestre de PBI más reciente
 * con fecha <= date (ver pbiReferenceAsOf) y lo multiplica x4.
 *
 * Es una aproximación deliberada: asume que los 4 trimestres del año
 * tienen un nivel similar al último cargado. Se eligió este método (en
 * vez de exigir 4 trimestres reales antes de poder calcular nada) para
 * que la comparación "% del PBI" funcione desde el primer dato de PBI
 * cargado, y mejore sola a medida que se cargan más trimestres reales
 * (en ese caso, el punto de referencia pasa a ser el trimestre real más
 * cercano a cada fecha, no siempre el último).
 *
 * Devuelve null si no hay ningún dato de PBI con fecha <= date.
 */
export function annualizedPbiAsOf(
  date: string,
  pbiObservations: SeriesObservationRow[]
): number | null {
  const ref = pbiReferenceAsOf(date, pbiObservations);
  return ref ? ref.value * 4 : null;
}
