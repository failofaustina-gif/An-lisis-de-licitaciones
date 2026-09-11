import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "./types";

/**
 * Cliente único de Supabase, usado tanto en Server Components como en
 * Route Handlers y Client Components. Usa siempre la clave "anon": el
 * acceso de escritura (usado solo por scripts/bcra/*) requiere la
 * service_role key, que nunca debe llegar al código que corre en el
 * navegador ni a este archivo.
 *
 * La seguridad de lectura pública está garantizada por las políticas RLS
 * definidas en database/schema.sql (select libre, sin insert/update/delete
 * para el rol anon).
 */
let cached: SupabaseClient<Database> | null = null;

export function getSupabaseClient(): SupabaseClient<Database> {
  if (cached) return cached;

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!url || !anonKey) {
    throw new Error(
      "Faltan NEXT_PUBLIC_SUPABASE_URL y/o NEXT_PUBLIC_SUPABASE_ANON_KEY. " +
        "Copiá .env.example a .env.local y completá los valores de tu proyecto Supabase."
    );
  }

  cached = createClient<Database>(url, anonKey, {
    auth: { persistSession: false },
  });
  return cached;
}
