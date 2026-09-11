"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";

interface Props {
  active: boolean;
  disabled?: boolean;
}

/**
 * Toggle "% del PBI". Mismo patrón que SeriesSelect: en vez de estado
 * propio, navega con un query param (?pbi=1) y deja que el Server
 * Component de la página vuelva a resolver los datos.
 */
export function PbiToggle({ active, disabled }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function toggle() {
    const params = new URLSearchParams(searchParams.toString());
    if (active) {
      params.delete("pbi");
    } else {
      params.set("pbi", "1");
    }
    router.push(`${pathname}?${params.toString()}`);
  }

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={disabled}
      title={disabled ? "Cargá el PBI primero en /cargar-pbi" : undefined}
      className={`rounded-md border px-3 py-2 text-sm transition-colors ${
        active
          ? "border-accent bg-accent text-white"
          : "border-ink-100 bg-white text-ink-700 hover:border-accent"
      } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      % del PBI
    </button>
  );
}
