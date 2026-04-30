import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";
import type { SimulationResult, Savings } from "../../api/client";
import { formatNumber } from "../../lib/utils";

interface FuelChartProps {
  baseline: SimulationResult;
  optimized: SimulationResult;
  savings: Savings;
}

export function FuelChart({ baseline, optimized, savings }: FuelChartProps) {
  const summary = [
    { name: "Baseline", fuel: parseFloat(baseline.total_fuel_liters.toFixed(2)), color: "#b0aa9d" },
    { name: "Optimized", fuel: parseFloat(optimized.total_fuel_liters.toFixed(2)), color: "#1c5228" },
  ];

  return (
    <div className="flex flex-col gap-4">
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={summary} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0ede8" vertical={false} />
          <XAxis
            dataKey="name"
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 12, fill: "#8e8779" }}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 11, fill: "#8e8779" }}
            tickFormatter={(v) => `${v} L`}
            width={55}
          />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 6, border: "1px solid #e8e6e1" }}
            formatter={(v) => [`${Number(v).toFixed(2)} L`, "Total Fuel"]}
          />
          <Bar dataKey="fuel" radius={[4, 4, 0, 0]}>
            {summary.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Savings breakdown */}
      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="bg-forest-50 border border-forest-100 rounded-md p-3">
          <p className="text-forest-700 text-lg font-semibold">{formatNumber(savings.fuel_saved_liters, 2)} L</p>
          <p className="text-xs text-stone-500">Fuel saved</p>
        </div>
        <div className="bg-forest-50 border border-forest-100 rounded-md p-3">
          <p className="text-forest-700 text-lg font-semibold">{formatNumber(savings.fuel_saved_pct, 1)}%</p>
          <p className="text-xs text-stone-500">Reduction</p>
        </div>
        <div className="bg-forest-50 border border-forest-100 rounded-md p-3">
          <p className="text-forest-700 text-lg font-semibold">{formatNumber(savings.co2_saved_kg, 1)} kg</p>
          <p className="text-xs text-stone-500">CO₂ saved</p>
        </div>
      </div>
    </div>
  );
}
