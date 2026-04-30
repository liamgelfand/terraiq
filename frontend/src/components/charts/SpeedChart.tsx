import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import type { SimulationResult } from "../../api/client";

interface SpeedChartProps {
  baseline: SimulationResult;
  optimized: SimulationResult;
}

export function SpeedChart({ baseline, optimized }: SpeedChartProps) {
  const data = baseline.distances_m.map((d, i) => ({
    km: parseFloat((d / 1000).toFixed(2)),
    baseline: parseFloat((baseline.speed_profile_ms[i] * 3.6).toFixed(1)),
    optimized: parseFloat(((optimized.speed_profile_ms[i] ?? 0) * 3.6).toFixed(1)),
  }));

  const step = Math.max(1, Math.floor(data.length / 500));
  const sampled = data.filter((_, i) => i % step === 0);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={sampled} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
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
          tickFormatter={(v) => `${v} km/h`}
          width={65}
        />
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 6, border: "1px solid #e8e6e1" }}
          formatter={(v, name) => [`${Number(v).toFixed(1)} km/h`, name === "baseline" ? "Baseline" : "Optimized"]}
          labelFormatter={(v) => `${v} km`}
        />
        <Legend
          wrapperStyle={{ fontSize: 12 }}
          formatter={(value) => (value === "baseline" ? "Baseline" : "Optimized")}
        />
        <Line
          type="monotone"
          dataKey="baseline"
          stroke="#b0aa9d"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 3 }}
        />
        <Line
          type="monotone"
          dataKey="optimized"
          stroke="#1c5228"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
