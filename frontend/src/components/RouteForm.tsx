import { useState } from "react";
import { Loader2, Play } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { listVehicles, type JobConfig } from "../api/client";

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
  const [vehicleId, setVehicleId] = useState("freightliner_2022");
  const [timeBudget, setTimeBudget] = useState(1.05);
  const [loadKg, setLoadKg] = useState<string>("");

  const { data: vehicles = [] } = useQuery({
    queryKey: ["vehicles"],
    queryFn: listVehicles,
    staleTime: Infinity,
  });

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
      vehicle_id: vehicleId,
      job_type: sweepMode ? "sweep" : "optimize",
      time_budget_fraction: sweepMode ? 1.0 : timeBudget,
      load_kg: loadKg !== "" ? parseFloat(loadKg) : undefined,
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

      {/* Origin */}
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

      {/* Destination */}
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
        <label className="label" htmlFor="vehicle">Vehicle</label>
        {vehicles.length > 1 ? (
          <select
            id="vehicle"
            className="input"
            value={vehicleId}
            onChange={(e) => setVehicleId(e.target.value)}
          >
            {vehicles.map((v) => (
              <option key={v.id} value={v.id}>{v.name}</option>
            ))}
          </select>
        ) : (
          <div className="input bg-stone-50 text-stone-500 cursor-default select-none">
            {vehicles[0]?.name ?? "Freightliner Cascadia 2022"}
          </div>
        )}
      </div>

      {/* Payload weight */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="label mb-0" htmlFor="load">Payload weight</label>
          <span className="text-xs text-stone-400">optional</span>
        </div>
        <div className="relative">
          <input
            id="load"
            type="number"
            min={0}
            max={17000}
            step={100}
            value={loadKg}
            onChange={(e) => setLoadKg(e.target.value)}
            placeholder="Full GVW (default)"
            className="input pr-10"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-stone-400 pointer-events-none">
            kg
          </span>
        </div>
        <p className="text-xs text-stone-400 mt-1">0–17,000 kg. Leave blank for full laden weight.</p>
      </div>

      {/* Time budget — hidden in sweep mode */}
      {!sweepMode && (
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="label mb-0">Time Budget</label>
            <span className="text-sm font-medium text-forest-700">
              +{((timeBudget - 1) * 100).toFixed(0)}%
            </span>
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
          <p className="text-xs text-stone-400 mt-1">Max allowed travel time vs. baseline drive</p>
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
