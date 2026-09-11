import { getPbiObservations } from "@/lib/pbi";
import { CargarPbiForm } from "@/components/forms/CargarPbiForm";
import { formatDate, formatNumber } from "@/lib/format";

export const dynamic = "force-dynamic"; // refleja lo recién cargado sin cachear

export default async function CargarPbiPage() {
  const observations = await getPbiObservations();
  const sorted = [...observations].sort((a, b) => b.date.localeCompare(a.date));

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">Cargar PBI</h1>
        <p className="text-sm text-ink-700 leading-relaxed mt-2">
          El BCRA no publica el PBI, así que esta serie se carga a mano,
          trimestre a trimestre. Se usa en "Agregados monetarios" para
          expresar las demás series como % del PBI: se anualiza (×4) el
          último trimestre cargado con fecha anterior o igual a la de cada
          observación.
        </p>
        <p className="text-xs text-ink-500 mt-2">
          Cargá el PBI nominal (a precios corrientes) del trimestre, en ARS
          millones — la misma unidad que usan las demás series monetarias.
          Como fecha, usá el último día del trimestre (ej: 30/06/2026 para
          el segundo trimestre de 2026).
        </p>
      </div>

      <CargarPbiForm />

      <div>
        <h2 className="text-sm font-medium text-ink-900 mb-2">
          Trimestres cargados
        </h2>
        {sorted.length === 0 ? (
          <p className="text-sm text-ink-500">
            Todavía no cargaste ningún valor.
          </p>
        ) : (
          <table className="w-full text-sm border border-ink-100 rounded-lg overflow-hidden">
            <thead className="bg-ink-100 text-ink-500 text-xs">
              <tr>
                <th className="text-left px-3 py-2 font-medium">Fecha</th>
                <th className="text-right px-3 py-2 font-medium">
                  PBI nominal (ARS millones)
                </th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((obs) => (
                <tr key={obs.id} className="border-t border-ink-100">
                  <td className="px-3 py-2">{formatDate(obs.date)}</td>
                  <td className="px-3 py-2 text-right tabular">
                    {formatNumber(obs.value)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
