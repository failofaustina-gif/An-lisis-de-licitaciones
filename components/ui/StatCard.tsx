interface Props {
  label: string;
  value: string;
  sublabel?: string;
  tone?: "neutral" | "positive" | "negative";
}

/**
 * Card genérica de KPI. Principio del spec: "no mostrar una card si
 * todavía no hay datos" — eso se decide en el componente que la usa
 * (no renderiza <StatCard /> si el valor es null), no acá.
 */
export function StatCard({ label, value, sublabel, tone = "neutral" }: Props) {
  const toneClass =
    tone === "positive"
      ? "text-accent"
      : tone === "negative"
        ? "text-danger"
        : "text-ink-900";

  return (
    <div className="rounded-lg border border-ink-100 bg-white px-4 py-3">
      <div className="text-xs text-ink-500 mb-1">{label}</div>
      <div className={`text-xl font-semibold tabular ${toneClass}`}>{value}</div>
      {sublabel ? <div className="text-xs text-ink-500 mt-1">{sublabel}</div> : null}
    </div>
  );
}
