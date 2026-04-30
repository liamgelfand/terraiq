import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import type { SimulationResult } from "../../api/client";

interface ElevationChartProps {
  result: SimulationResult;
}

export function ElevationChart({ result }: ElevationChartProps) {
  const data = result.distances_m.map((d, i) => ({
    km: parseFloat((d / 1000).toFixed(2)),
    elevation: parseFloat(result.elevations_m[i].toFixed(1)),
  }));

  // Sample to keep the chart responsive (max 500 points)
  const step = Math.max(1, Math.floor(data.length / 500));
  const sampled = data.filter((_, i) => i % step === 0);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={sampled} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="elevGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#2d8040" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#2d8040" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0ede8" />
        <XAxis
          dataKey="km"
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 11, fill: "#8e8779" }}
          tickFormatter={(v) => `${v} km`}
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tick={{ fontSize: 11, fill: "#8e8779" }}
          tickFormatter={(v) => `${v} m`}
          width={55}
        />
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 6, border: "1px solid #e8e6e1" }}
          formatter={(v) => [`${Number(v).toFixed(0)} m`, "Elevation"]}
          labelFormatter={(v) => `${v} km`}
        />
        <Area
          type="monotone"
          dataKey="elevation"
          stroke="#1c5228"
          strokeWidth={2}
          fill="url(#elevGrad)"
          dot={false}
          activeDot={{ r: 4 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
