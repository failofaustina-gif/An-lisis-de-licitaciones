import { getSeriesCatalog, getSeriesByDisplayName, getObservations } from "@/lib/series";
import { SeriesSelect } from "@/components/ui/SeriesSelect";
import { StatCard } from "@/components/ui/StatCard";
import { SeriesChart } from "@/components/charts/SeriesChart";
import { changeOverLastN, withDailyChange } from "@/lib/derived";
import { formatDate, formatNumber, formatPercent } from "@/lib/format";

export const dynamic = "force-dynamic"; // los datos cambian a diario; no cachear la página estáticamente

interface PageProps {
  searchParams: { serie?: string };
}

export default async function AgregadosPage({ searchParams }: PageProps) {
  const catalog = await getSeriesCatalog();

  if (catalog.length === 0) {
    return <EmptyState />;
  }

  const firstSeries = catalog[0]!; // catalog.length === 0 ya retornó arriba
  const selectedName = searchParams.serie ?? firstSeries.display_name;
  const selectedSeries =
    (await getSeriesByDisplayName(selectedName)) ?? firstSeries;

  const observations = await getObservations(selectedSeries.id);
  const withChange = withDailyChange(observations);
  const last = observations.at(-1);
  const dailyChange = withChange.at(-1);

  const change5 = changeOverLastN(observations, 5);
  const change20 = changeOverLastN(observations, 20);
  const change60 = changeOverLastN(observations, 60);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">
            {selectedSeries.original_name}
          </h1>
          <p className="text-sm text-ink-500 mt-1">
            {selectedSeries.unit} · frecuencia {readableFrequency(selectedSeries.frequency)} ·
            {" "}
            fuente {selectedSeries.source}
          </p>
        </div>
        <SeriesSelect catalog={catalog} selected={selectedSeries.display_name} />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {last ? (
          <StatCard
            label="Último valor"
            value={formatNumber(last.value)}
            sublabel={formatDate(last.date)}
          />
        ) : null}
        {dailyChange?.diffPct != null ? (
          <StatCard
            label="Variación diaria"
            value={formatPercent(dailyChange.diffPct)}
            tone={dailyChange.diffPct >= 0 ? "positive" : "negative"}
          />
        ) : null}
        {change5 ? (
          <StatCard
            label="Variación 5 obs."
            value={change5.diffPct != null ? formatPercent(change5.diffPct) : "—"}
            tone={change5.diffAbs >= 0 ? "positive" : "negative"}
          />
        ) : null}
        {change20 ? (
          <StatCard
            label="Variación 20 obs."
            value={change20.diffPct != null ? formatPercent(change20.diffPct) : "—"}
            tone={change20.diffAbs >= 0 ? "positive" : "negative"}
          />
        ) : null}
        {change60 ? (
          <StatCard
            label="Variación 60 obs."
            value={change60.diffPct != null ? formatPercent(change60.diffPct) : "—"}
            tone={change60.diffAbs >= 0 ? "positive" : "negative"}
          />
        ) : null}
      </div>

      <div className="rounded-lg border border-ink-100 bg-white p-4">
        <SeriesChart
          data={observations.map((o) => ({ date: o.date, value: o.value }))}
          unit={selectedSeries.unit}
        />
      </div>

      {selectedSeries.metadata?.ultima_fecha_informada ? (
        <p className="text-xs text-ink-500">
          Última fecha informada por la fuente:{" "}
          {String(selectedSeries.metadata.ultima_fecha_informada)}. Nombre original
          en el BCRA: "{selectedSeries.original_name}" (idVariable{" "}
          {selectedSeries.source_series_id}).
        </p>
      ) : null}
    </div>
  );
}

function readableFrequency(freq: string): string {
  const map: Record<string, string> = {
    D: "diaria",
    M: "mensual",
    T: "trimestral",
    Q: "trimestral",
  };
  return map[freq] ?? freq;
}

function EmptyState() {
  return (
    <div className="max-w-xl rounded-lg border border-dashed border-ink-100 p-6">
      <h1 className="text-lg font-semibold text-ink-900 mb-2">
        Todavía no hay series cargadas
      </h1>
      <p className="text-sm text-ink-700 leading-relaxed mb-3">
        Esta página lee directamente de <code>series_catalog</code> en
        Supabase. Para poblarla, corré el script de sincronización con el
        BCRA:
      </p>
      <pre className="rounded-md bg-ink-900 text-paper text-xs p-3 overflow-x-auto">
        python -m scripts.bcra.download --mode full
      </pre>
      <p className="text-sm text-ink-700 mt-3">
        Ver <code>README.md</code> en la raíz del repositorio para las
        variables de entorno necesarias.
      </p>
    </div>
  );
}
