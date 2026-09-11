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
 *
 * `global.fetch` con `cache: "no-store"` explícito: sin esto, el fetch
 * interno de supabase-js queda sujeto al Data Cache de Next.js, que puede
 * cachear indefinidamente la respuesta de una consulta aunque la página
 * tenga `dynamic = "force-dynamic"` (ese flag controla el render de la
 * página, no el cacheo de cada fetch individual). Así fue como, al cargar
 * PBI por primera vez, la consulta a series_catalog había quedado
 * cacheada como "no existe" desde antes de crear la fila manual, y esa
 * respuesta vacía se siguió sirviendo para siempre aunque el dato ya
 * estuviera en la base (confirmado leyendo la misma fila directo por la
 * REST API de Supabase, sin pasar por Next.js). Con `cache: "no-store"`
 * cada lectura pega siempre a Supabase.
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
    global: {
      fetch: (input, init) => fetch(input, { ...init, cache: "no-store" }),
    },
  });
  return cached;
}
