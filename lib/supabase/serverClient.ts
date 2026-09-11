import { createClient, type SupabaseClient } from "@supabase/supabase-js";

/**
 * Cliente con la service_role key. SOLO se importa desde Route Handlers
 * (app/api/.../route.ts) que corren en el servidor. A diferencia de
 * client.ts (clave "anon", de solo lectura por RLS), este cliente
 * bypassea RLS: nunca hay que importarlo desde un Client Component ni
 * desde código que pueda terminar en el bundle del browser.
 *
 * Sin el genérico Database (a diferencia de client.ts): el tipo
 * Database de este proyecto se escribe a mano solo con Row/Insert/Update
 * (sin Relationships/Views/Functions), que alcanza para tipar
 * `.select()` pero no para que supabase-js infiera bien `.insert()` /
 * `.upsert()` en esta versión de @supabase/supabase-js. Para las pocas
 * escrituras de este proyecto (ver app/api/pbi/route.ts) no vale la
 * pena mantener ese tipo completo; los payloads ya se validan a mano
 * antes de llegar acá.
 */
export function getSupabaseServiceClient(): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !serviceKey) {
    throw new Error(
      "Faltan NEXT_PUBLIC_SUPABASE_URL y/o SUPABASE_SERVICE_ROLE_KEY en el " +
        "entorno del servidor (Vercel: Project Settings > Environment " +
        "Variables). SUPABASE_SERVICE_ROLE_KEY nunca debe llevar el prefijo " +
        "NEXT_PUBLIC_."
    );
  }

  return createClient(url, serviceKey, {
    auth: { persistSession: false },
  });
}
