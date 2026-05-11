import { useState } from "react";
import { Loader2, Play } from "lucide-react";
import { type JobConfig } from "../api/client";

interface RouteFormProps {
  onSubmit: (config: JobConfig) => void;
  isLoading: boolean;
  sweepMode?: boolean;
}

const PRESETS = [
  { label: "Denver → Grand Junction", origin: "Denver, CO", destination: "Grand Junction, CO" },
  { label: "Provo → St. George", origin: "Provo, UT", destination: "St. George, UT" },
  { label: "Nashville → Memphis", origin: "Nashville, TN", destination: "Memphis, TN" },
  { label: "Donner Pass → Sacramento", origin: "Truckee, CA", destination: "Sacramento, CA" },
  { label: "Asheville → Charlotte", origin: "Asheville, NC", destination: "Charlotte, NC" },
];

export function RouteForm({ onSubmit, isLoading, sweepMode = false }: RouteFormProps) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [timeBudget, setTimeBudget] = useState(1.05);

  function applyPreset(preset: (typeof PRESETS)[0]) {
    setOrigin(preset.origin);
    setDestination(preset.destination);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!origin.trim() || !destination.trim()) return;
    onSubmit({
      origin: origin.trim(),
      destination: destination.trim(),
      vehicle_id: "freightliner_2022",
      time_budget_fraction: timeBudget,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      {/* Presets */}
      <div>
        <label className="label">Quick Routes</label>
        <div className="flex flex-col gap-1">
          {PRESETS.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => applyPreset(p)}
              className="text-left text-xs px-3 py-2 rounded-md border border-stone-200 bg-white hover:bg-stone-50 hover:border-forest-700 text-stone-600 hover:text-forest-700 transition-colors"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <hr className="border-stone-200" />

      {/* Inputs */}
      <div>
        <label className="label" htmlFor="origin">Origin</label>
        <input
          id="origin"
          className="input"
          placeholder="e.g. Denver, CO"
          value={origin}
          onChange={(e) => setOrigin(e.target.value)}
          required
        />
      </div>

      <div>
        <label className="label" htmlFor="destination">Destination</label>
        <input
          id="destination"
          className="input"
          placeholder="e.g. Grand Junction, CO"
          value={destination}
          onChange={(e) => setDestination(e.target.value)}
          required
        />
      </div>

      {/* Vehicle */}
      <div>
        <label className="label">Vehicle</label>
        <div className="input bg-stone-50 text-stone-500 cursor-default select-none">
          Freightliner Cascadia 2022
        </div>
      </div>

      {/* Time budget — hidden in sweep mode (sweep runs all budgets) */}
      {!sweepMode && (
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="label mb-0">Time Budget</label>
            <span className="text-sm font-medium text-forest-700">+{((timeBudget - 1) * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="1.0"
            max="1.30"
            step="0.01"
            value={timeBudget}
            onChange={(e) => setTimeBudget(parseFloat(e.target.value))}
            className="w-full accent-forest-700"
          />
          <p className="text-xs text-stone-400 mt-1">
            Max allowed travel time vs. baseline drive
          </p>
        </div>
      )}

      <button
        type="submit"
        className="btn-primary flex items-center justify-center gap-2 mt-1"
        disabled={isLoading || !origin.trim() || !destination.trim()}
      >
        {isLoading ? (
          <>
            <Loader2 size={16} className="animate-spin" />
            {sweepMode ? "Running sweep…" : "Running simulation…"}
          </>
        ) : (
          <>
            <Play size={16} />
            {sweepMode ? "Run Sweep" : "Run Simulation"}
          </>
        )}
      </button>
    </form>
  );
}
