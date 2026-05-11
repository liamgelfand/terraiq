import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SweepPoint } from "../../api/client";

interface SweepChartProps {
  curve: SweepPoint[];
  baselineFuelL: number;
  distanceKm: number;
}

export function SweepChart({ curve, baselineFuelL, distanceKm }: SweepChartProps) {
  const data = curve.map((p) => ({
    extra_min: p.extra_time_min,
    cost_saved: p.cost_saved_usd,
    fuel_pct: p.fuel_saved_pct,
    tbf: p.time_budget_fraction,
  }));

  // Find the "knee" point — max marginal return before it flattens
  const kneeIdx = data.reduce((best, pt, i) => {
    if (i === 0) return best;
    const marginal =
      (pt.cost_saved - data[i - 1].cost_saved) /
      Math.max(pt.extra_min - data[i - 1].extra_min, 0.1);
    return marginal > (best.marginal ?? 0) ? { i, marginal } : best;
  }, {} as { i?: number; marginal?: number });

  const knee = kneeIdx.i !== undefined ? data[kneeIdx.i] : null;

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-stone-500">
            {distanceKm.toFixed(0)} km route · baseline {baselineFuelL.toFixed(1)} L
          </p>
        </div>
        {knee && (
          <div className="text-right">
            <p className="text-xs text-stone-500">Sweet spot</p>
            <p className="text-sm font-semibold text-forest-700">
              +{knee.extra_min.toFixed(0)} min → ${knee.cost_saved.toFixed(2)} saved
            </p>
          </div>
        )}
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
          <XAxis
            dataKey="extra_min"
            tick={{ fontSize: 11, fill: "#78716c" }}
            tickFormatter={(v) => `+${Number(v).toFixed(0)}m`}
            label={{ value: "Extra time (min)", position: "insideBottom", offset: -2, fontSize: 11, fill: "#a8a29e" }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#78716c" }}
            tickFormatter={(v) => `$${v}`}
            width={52}
          />
          <Tooltip
            formatter={(v, name) => [
              name === "cost_saved" ? `$${Number(v).toFixed(2)}` : `${Number(v).toFixed(1)}%`,
              name === "cost_saved" ? "Cost saved" : "Fuel saved",
            ]}
            labelFormatter={(v) => `+${Number(v).toFixed(1)} min`}
            contentStyle={{ fontSize: 12 }}
          />
          <Line
            type="monotone"
            dataKey="cost_saved"
            stroke="#4d7c0f"
            strokeWidth={2}
            dot={{ r: 3, fill: "#4d7c0f" }}
            activeDot={{ r: 5 }}
          />
          {knee && (
            <ReferenceDot
              x={knee.extra_min}
              y={knee.cost_saved}
              r={6}
              fill="#84cc16"
              stroke="#3f6212"
              strokeWidth={2}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* Curve table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-stone-400 border-b border-stone-100">
              <th className="py-1 text-left font-medium">Budget</th>
              <th className="py-1 text-right font-medium">+Time</th>
              <th className="py-1 text-right font-medium">Fuel saved</th>
              <th className="py-1 text-right font-medium">Cost saved</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-50">
            {curve.map((p) => (
              <tr
                key={p.time_budget_fraction}
                className={
                  knee && p.extra_time_min === knee.extra_min
                    ? "bg-forest-50 font-semibold"
                    : ""
                }
              >
                <td className="py-1 text-stone-600">
                  {((p.time_budget_fraction - 1) * 100).toFixed(0)}% slack
                </td>
                <td className="py-1 text-right text-stone-500">
                  +{p.extra_time_min.toFixed(0)} min
                </td>
                <td className="py-1 text-right text-stone-600">
                  {p.fuel_saved_L.toFixed(1)} L ({p.fuel_saved_pct.toFixed(1)}%)
                </td>
                <td className="py-1 text-right text-stone-700">${p.cost_saved_usd.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
