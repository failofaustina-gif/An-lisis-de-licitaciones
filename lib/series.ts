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

export async function getObservations(
  seriesId: string,
  opts: { desde?: string; hasta?: string; limit?: number } = {}
): Promise<SeriesObservationRow[]> {
  const supabase = getSupabaseClient();
  let query = supabase
    .from("series_observations")
    .select("*")
    .eq("series_id", seriesId)
    .order("date", { ascending: true });

  if (opts.desde) query = query.gte("date", opts.desde);
  if (opts.hasta) query = query.lte("date", opts.hasta);
  if (opts.limit) query = query.limit(opts.limit);

  const { data, error } = await query;
  if (error) {
    throw new Error(`Error trayendo observaciones de series_id=${seriesId}: ${error.message}`);
  }
  return data ?? [];
}
