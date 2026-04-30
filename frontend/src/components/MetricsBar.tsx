import { Fuel, DollarSign, Leaf, Route, TrendingDown } from "lucide-react";
import { formatCurrency, formatNumber } from "../lib/utils";
import type { Savings, SimulationResult } from "../api/client";

interface MetricsBarProps {
  baseline: SimulationResult;
  savings: Savings;
}

interface MetricProps {
  label: string;
  value: string;
  delta?: string;
  icon: React.ReactNode;
  highlight?: boolean;
}

function Metric({ label, value, delta, icon, highlight }: MetricProps) {
  return (
    <div className={`metric-card flex-1 min-w-0 ${highlight ? "border-forest-200 bg-forest-50" : ""}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="metric-label">{label}</span>
        <span className={highlight ? "text-forest-600" : "text-stone-400"}>{icon}</span>
      </div>
      <p className={`metric-value ${highlight ? "text-forest-700" : ""}`}>{value}</p>
      {delta && (
        <p className="metric-delta-positive">{delta}</p>
      )}
    </div>
  );
}

export function MetricsBar({ baseline, savings }: MetricsBarProps) {
  return (
    <div className="flex gap-3 p-4 bg-white border-b border-stone-200">
      <Metric
        label="Distance"
        value={`${formatNumber(baseline.total_distance_km, 0)} km`}
        icon={<Route size={16} />}
      />
      <Metric
        label="Baseline Fuel"
        value={`${formatNumber(baseline.total_fuel_liters, 1)} L`}
        icon={<Fuel size={16} />}
      />
      <Metric
        label="Optimized Fuel"
        value={`${formatNumber(baseline.total_fuel_liters - savings.fuel_saved_liters, 1)} L`}
        icon={<Fuel size={16} />}
      />
      <Metric
        label="Fuel Saved"
        value={`${formatNumber(savings.fuel_saved_liters, 2)} L`}
        delta={`${formatNumber(savings.fuel_saved_pct, 1)}% reduction`}
        icon={<TrendingDown size={16} />}
        highlight
      />
      <Metric
        label="Cost Saved"
        value={formatCurrency(savings.cost_saved_usd)}
        delta="per trip"
        icon={<DollarSign size={16} />}
        highlight
      />
      <Metric
        label="CO₂ Saved"
        value={`${formatNumber(savings.co2_saved_kg, 1)} kg`}
        icon={<Leaf size={16} />}
        highlight
      />
    </div>
  );
}
