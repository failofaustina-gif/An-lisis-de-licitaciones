import { NextResponse } from "next/server";
import { getSupabaseServiceClient } from "@/lib/supabase/serverClient";
import { PBI_DISPLAY_NAME } from "@/lib/pbi";

/**
 * Alta manual de un punto de PBI. A diferencia de las series del BCRA
 * (scripts/bcra/*, que nunca inventan un idVariable), esta serie no tiene
 * fuente automática: el BCRA no publica el PBI. Por eso se modela con
 * source='manual' en series_catalog, cargada por esta ruta, y se usa
 * únicamente para expresar otras series como % del PBI (ver lib/pbi.ts).
 *
 * Sin autenticación a propósito (decisión del usuario): cualquiera que
 * conozca esta URL puede cargar/pisar un valor. Si en el futuro hace
 * falta protegerla, agregar acá una verificación simple antes de tocar
 * Supabase.
 */
export async function POST(request: Request) {
  let body: { date?: unknown; value?: unknown };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "JSON inválido." }, { status: 400 });
  }

  const { date, value } = body;
  if (typeof date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    return NextResponse.json(
      { error: "Falta 'date' en formato YYYY-MM-DD." },
      { status: 400 }
    );
  }
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    return NextResponse.json(
      { error: "Falta 'value': tiene que ser un número mayor a 0." },
      { status: 400 }
    );
  }

  const supabase = getSupabaseServiceClient();

  // 1. Asegurar que exista la fila en series_catalog para la serie manual de PBI.
  const { data: existingCatalog, error: catalogSelectError } = await supabase
    .from("series_catalog")
    .select("id")
    .eq("source", "manual")
    .eq("source_series_id", "pbi_nominal")
    .maybeSingle();

  if (catalogSelectError) {
    return NextResponse.json({ error: catalogSelectError.message }, { status: 500 });
  }

  let seriesId = existingCatalog?.id;

  if (!seriesId) {
    const { data: inserted, error: insertError } = await supabase
      .from("series_catalog")
      .insert({
        source: "manual",
        source_series_id: "pbi_nominal",
        original_name: "PBI nominal (a precios corrientes)",
        display_name: PBI_DISPLAY_NAME,
        category: "pbi",
        frequency: "Q",
        unit: "ARS millones",
        description:
          "Cargado a mano (el BCRA no publica el PBI). Se usa para expresar " +
          "otras series como % del PBI: anualizado ×4 sobre el último " +
          "trimestre cargado a cada fecha (ver lib/pbi.ts).",
        active: true,
        metadata: {},
      })
      .select("id")
      .single();

    if (insertError || !inserted) {
      return NextResponse.json(
        { error: insertError?.message ?? "No se pudo crear la serie de PBI." },
        { status: 500 }
      );
    }
    seriesId = inserted.id;
  }

  // 2. Insertar o actualizar (si ya existía) la observación para esa fecha.
  const { error: upsertError } = await supabase
    .from("series_observations")
    .upsert(
      { series_id: seriesId, date, value, is_flagged: false, flag_reason: null },
      { onConflict: "series_id,date" }
    );

  if (upsertError) {
    return NextResponse.json({ error: upsertError.message }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}
