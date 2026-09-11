/**
 * Tipos manuales de las tablas de Supabase relevantes para el frontend en
 * esta etapa. Se escriben a mano (en vez de generar con `supabase gen
 * types`) para no agregar el CLI de Supabase como dependencia todavía;
 * deben mantenerse en sincro con database/schema.sql.
 */

export interface SeriesCatalogRow {
  id: string;
  source: string;
  source_series_id: string;
  original_name: string;
  display_name: string;
  category: string;
  frequency: string;
  unit: string;
  description: string | null;
  active: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface SeriesObservationRow {
  id: string;
  series_id: string;
  date: string; // YYYY-MM-DD
  value: number;
  is_flagged: boolean;
  flag_reason: string | null;
  created_at: string;
}

export interface Database {
  public: {
    Tables: {
      series_catalog: {
        Row: SeriesCatalogRow;
        Insert: Partial<SeriesCatalogRow>;
        Update: Partial<SeriesCatalogRow>;
      };
      series_observations: {
        Row: SeriesObservationRow;
        Insert: Partial<SeriesObservationRow>;
        Update: Partial<SeriesObservationRow>;
      };
    };
  };
}
