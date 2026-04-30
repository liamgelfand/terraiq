import { useState } from "react";
import { cn } from "../lib/utils";
import { ElevationChart } from "./charts/ElevationChart";
import { SpeedChart } from "./charts/SpeedChart";
import { FuelChart } from "./charts/FuelChart";
import type { JobResult } from "../api/client";

type Tab = "elevation" | "speed" | "fuel";

const TABS: { id: Tab; label: string }[] = [
  { id: "elevation", label: "Elevation Profile" },
  { id: "speed", label: "Speed Comparison" },
  { id: "fuel", label: "Fuel Analysis" },
];

interface ChartsPanelProps {
  result: JobResult;
}

export function ChartsPanel({ result }: ChartsPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("elevation");

  return (
    <div className="card h-full flex flex-col">
      {/* Tab bar */}
      <div className="flex border-b border-stone-200 px-4">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-4 py-3 text-sm font-medium border-b-2 transition-colors -mb-px",
              activeTab === tab.id
                ? "border-forest-700 text-forest-700"
                : "border-transparent text-stone-500 hover:text-stone-700"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Chart content */}
      <div className="flex-1 p-4">
        {activeTab === "elevation" && (
          <ElevationChart result={result.baseline} />
        )}
        {activeTab === "speed" && (
          <SpeedChart baseline={result.baseline} optimized={result.optimized} />
        )}
        {activeTab === "fuel" && (
          <FuelChart
            baseline={result.baseline}
            optimized={result.optimized}
            savings={result.savings}
          />
        )}
      </div>
    </div>
  );
}
