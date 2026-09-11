/**
 * Formateo de números al estilo argentino (punto de miles, coma decimal),
 * centralizado acá para no repetir Intl.NumberFormat por todos lados.
 */

const numberFormatterCache = new Map<string, Intl.NumberFormat>();

function getFormatter(maximumFractionDigits: number): Intl.NumberFormat {
  const key = String(maximumFractionDigits);
  let formatter = numberFormatterCache.get(key);
  if (!formatter) {
    formatter = new Intl.NumberFormat("es-AR", {
      maximumFractionDigits,
      minimumFractionDigits: 0,
    });
    numberFormatterCache.set(key, formatter);
  }
  return formatter;
}

/** Formatea un valor monetario/numérico grande, ej: 45.123.456 */
export function formatNumber(value: number, maximumFractionDigits = 0): string {
  return getFormatter(maximumFractionDigits).format(value);
}

/** Formatea una variación porcentual con signo, ej: +2,3% / -1,1% */
export function formatPercent(value: number, maximumFractionDigits = 1): string {
  const formatted = getFormatter(maximumFractionDigits).format(Math.abs(value));
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return `${sign}${formatted}%`;
}

/** Formatea una fecha ISO ('YYYY-MM-DD') como 'DD/MM/AAAA'. */
export function formatDate(isoDate: string): string {
  const [y, m, d] = isoDate.split("-");
  return `${d}/${m}/${y}`;
}

/** Etiqueta legible para la unidad guardada en series_catalog.unit. */
export function formatUnit(unit: string): string {
  return unit;
}
