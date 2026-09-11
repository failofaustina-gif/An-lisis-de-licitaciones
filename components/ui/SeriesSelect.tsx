"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import type { SeriesCatalogRow } from "@/lib/supabase/types";

interface Props {
  catalog: SeriesCatalogRow[];
  selected: string;
}

/**
 * Selector de serie. En vez de manejar estado propio + fetch client-side,
 * navega con un query param (?serie=...) y deja que el Server Component de
 * la página vuelva a resolver los datos. Menos estado, menos JS en el
 * cliente, y la URL queda compartible.
 */
export function SeriesSelect({ catalog, selected }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function onChange(displayName: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("serie", displayName);
    router.push(`${pathname}?${params.toString()}`);
  }

  const grouped = groupByCategory(catalog);

  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-ink-500">Serie</span>
      <select
        className="rounded-md border border-ink-100 bg-white px-3 py-2 text-ink-900 text-sm min-w-[280px]"
        value={selected}
        onChange={(e) => onChange(e.target.value)}
      >
        {Object.entries(grouped).map(([category, rows]) => (
          <optgroup key={category} label={category}>
            {rows.map((row) => (
              <option key={row.display_name} value={row.display_name}>
                {row.original_name}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
    </label>
  );
}

function groupByCategory(
  catalog: SeriesCatalogRow[]
): Record<string, SeriesCatalogRow[]> {
  return catalog.reduce<Record<string, SeriesCatalogRow[]>>((acc, row) => {
    (acc[row.category] ??= []).push(row);
    return acc;
  }, {});
}
