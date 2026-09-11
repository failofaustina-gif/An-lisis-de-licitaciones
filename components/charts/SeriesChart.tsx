"use client";

import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { formatDate, formatNumber } from "@/lib/format";

export interface ChartPoint {
  date: string;
  value: number;
}

interface Props {
  data: ChartPoint[];
  unit: string;
}

/**
 * Gráfico de una sola serie temporal. Deliberadamente simple para esta
 * etapa (item 8 del alcance): sin comparación entre series ni toggles de
 * variación/media móvil todavía — eso corresponde a la sección completa
 * de "Agregados monetarios" de una etapa posterior.
 */
export function SeriesChart({ data, unit }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center rounded-lg border border-dashed border-ink-100 text-sm text-ink-500">
        Todavía no hay observaciones cargadas para esta serie.
      </div>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="#e6e8ec" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            stroke="#9aa1ad"
            fontSize={12}
            tickMargin={8}
            minTickGap={40}
          />
          <YAxis
            stroke="#9aa1ad"
            fontSize={12}
            width={72}
            tickFormatter={(v: number) => formatNumber(v)}
          />
          <Tooltip
            formatter={(value: number) => [`${formatNumber(value)} ${unit}`, "Valor"]}
            labelFormatter={(label: string) => formatDate(label)}
            contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#e6e8ec" }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#1f5f4f"
            strokeWidth={1.75}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
