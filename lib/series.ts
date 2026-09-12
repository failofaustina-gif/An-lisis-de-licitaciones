import { getSupabaseClient } from "./supabase/client";
import type { SeriesCatalogRow, SeriesObservationRow } from "./supabase/types";

/**
 * Punto único de acceso a datos de series para toda la app. Nada fuera de
 * este archivo (y de scripts/bcra en el lado Python) debería llamar a
 * Supabase directamente para leer series — así, si mañana cambia el
 * esquema, solo hay que tocar acá.
 */

export async function getSeriesCatalog(): Promise<SeriesCatalogRow[]> {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from("series_catalog")
    .select("*")
    .eq("active", true)
    .order("category", { ascending: true })
    .order("display_name", { ascending: true });

  if (error) {
    throw new Error(`Error trayendo series_catalog: ${error.message}`);
  }
  return data ?? [];
}

export async function getSeriesByDisplayName(
  displayName: string
): Promise<SeriesCatalogRow | null> {
  const supabase = getSupabaseClient();
  const { data, error } = await supabase
    .from("series_catalog")
    .select("*")
    .eq("display_name", displayName)
    .eq("active", true)
    .maybeSingle();

  if (error) {
    throw new Error(`Error trayendo la serie '${displayName}': ${error.message}`);
  }
  return data;
}

// PostgREST (y por lo tanto Supabase) devuelve como mucho esta cantidad de
// filas por consulta aunque no se pida un `limit` explícito (es el
// "max-rows" default del proyecto). Series diarias con historia larga
// (ej. Base monetaria, con datos desde 1996 y >7000 filas) superan esto
// largo: sin paginar, `.select("*")` devuelve en silencio solo las
// primeras PAGE_SIZE filas ordenadas por fecha ascendente — es decir, las
// más VIEJAS, no las más recientes — sin ningún error que lo delate. Esto
// se descubrió porque hacía que "% del PBI" diera un gráfico vacío (las
// observaciones devueltas eran todas de 1996-1999, muy anteriores a
// cualquier trimestre de PBI cargado), pero afecta a cualquier lectura de
// una serie larga: "Último valor" mostraba un dato de hace 30 años.
const PAGE_SIZE = 1000;

export async function getObservations(
  seriesId: string,
  opts: { desde?: string; hasta?: string; limit?: number } = {}
): Promise<SeriesObservationRow[]> {
  const supabase = getSupabaseClient();
  const all: SeriesObservationRow[] = [];
  let offset = 0;

  while (true) {
    const remaining = opts.limit != null ? opts.limit - all.length : undefined;
    if (remaining != null && remaining <= 0) break;
    const pageSize = remaining != null ? Math.min(PAGE_SIZE, remaining) : PAGE_SIZE;

    let query = supabase
      .from("series_observations")
      .select("*")
      .eq("series_id", seriesId)
      .order("date", { ascending: true })
      .range(offset, offset + pageSize - 1);

    if (opts.desde) query = query.gte("date", opts.desde);
    if (opts.hasta) query = query.lte("date", opts.hasta);

    const { data, error } = await query;
    if (error) {
      throw new Error(`Error trayendo observaciones de series_id=${seriesId}: ${error.message}`);
    }
    if (!data || data.length === 0) break;

    all.push(...data);
    if (data.length < pageSize) break; // última página: vino incompleta

    offset += pageSize;
  }

  return all;
}
