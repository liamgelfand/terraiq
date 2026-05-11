import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, TrendingUp } from "lucide-react";
import { listJobs, type Job } from "../api/client";
import { JobStatusBadge } from "../components/JobStatusBadge";
import { RouteMap } from "../components/map/RouteMap";
import { ChartsPanel } from "../components/ChartsPanel";
import { SweepChart } from "../components/charts/SweepChart";

function JobRow({ job }: { job: Job }) {
  const [open, setOpen] = useState(false);
  const isSweep = job.config.job_type === "sweep" || !!(job.result?.curve);
  const hasSweepResult = isSweep && job.status === "completed" && !!job.result?.curve;
  const hasOptResult = !isSweep && job.status === "completed" && !!job.result?.savings;

  return (
    <div className="border border-stone-200 rounded-xl overflow-hidden bg-white">
      {/* Header row — always visible */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-4 px-5 py-4 hover:bg-stone-50 transition-colors text-left"
      >
        {/* Route */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            {isSweep && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs bg-earth-100 text-earth-700 border border-earth-200 font-medium">
                <TrendingUp size={10} />
                Sweep
              </span>
            )}
            <span className="text-sm font-semibold text-stone-800 truncate">
              {job.config.origin?.split(",")[0]}
              <span className="text-stone-400 font-normal mx-1">→</span>
              {job.config.destination?.split(",")[0]}
            </span>
          </div>
          <p className="text-xs text-stone-400">
            {new Date(job.created_at).toLocaleString()}
          </p>
        </div>

        {/* Savings summary */}
        {hasOptResult && (
          <div className="hidden sm:flex gap-6 text-right">
            <div>
              <p className="text-xs text-stone-400">Fuel saved</p>
              <p className="text-sm font-semibold text-stone-700">
                {job.result!.savings.fuel_saved_liters.toFixed(1)} L
              </p>
            </div>
            <div>
              <p className="text-xs text-stone-400">Cost saved</p>
              <p className="text-sm font-semibold text-forest-700">
                ${job.result!.savings.cost_saved_usd.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-xs text-stone-400">CO₂ avoided</p>
              <p className="text-sm font-semibold text-stone-700">
                {job.result!.savings.co2_saved_kg.toFixed(1)} kg
              </p>
            </div>
          </div>
        )}

        {hasSweepResult && (
          <div className="hidden sm:block text-right">
            <p className="text-xs text-stone-400">Max savings</p>
            <p className="text-sm font-semibold text-forest-700">
              ${Math.max(...job.result!.curve!.map((p) => p.cost_saved_usd)).toFixed(2)}
            </p>
          </div>
        )}

        <div className="flex items-center gap-3 flex-shrink-0 ml-2">
          <JobStatusBadge status={job.status} />
          {(hasOptResult || hasSweepResult) && (
            open ? <ChevronUp size={16} className="text-stone-400" /> : <ChevronDown size={16} className="text-stone-400" />
          )}
        </div>
      </button>

      {/* Expanded detail */}
      {open && hasOptResult && (
        <div className="border-t border-stone-100 p-5 space-y-4">
          {/* Savings breakdown */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Distance", value: `${job.result!.optimized.total_distance_km.toFixed(1)} km` },
              { label: "Fuel saved", value: `${job.result!.savings.fuel_saved_liters.toFixed(2)} L (${job.result!.savings.fuel_saved_pct.toFixed(1)}%)` },
              { label: "Cost saved", value: `$${job.result!.savings.cost_saved_usd.toFixed(2)}` },
              { label: "CO₂ avoided", value: `${job.result!.savings.co2_saved_kg.toFixed(1)} kg` },
            ].map((s) => (
              <div key={s.label} className="bg-stone-50 rounded-lg px-4 py-3">
                <p className="text-xs text-stone-400">{s.label}</p>
                <p className="text-sm font-semibold text-stone-800 mt-0.5">{s.value}</p>
              </div>
            ))}
          </div>

          {/* Map */}
          <div className="h-64 rounded-lg overflow-hidden border border-stone-200">
            <RouteMap
              baseline={job.result!.baseline}
              optimized={job.result!.optimized}
            />
          </div>

          {/* Charts */}
          <div className="h-64">
            <ChartsPanel result={job.result!} />
          </div>
        </div>
      )}

      {open && hasSweepResult && (
        <div className="border-t border-stone-100 p-5">
          <SweepChart
            curve={job.result!.curve!}
            baselineFuelL={job.result!.baseline_fuel_L ?? 0}
            distanceKm={job.result!.distance_km ?? 0}
          />
        </div>
      )}
    </div>
  );
}

export function History() {
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: listJobs,
  });

  if (isLoading) {
    return <div className="p-8 text-stone-400 text-sm animate-pulse">Loading…</div>;
  }

  return (
    <div className="p-6 space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-stone-800">Job History</h2>
        <p className="text-sm text-stone-500 mt-0.5">
          All optimization and sweep jobs for your fleet. Click a completed job to expand.
        </p>
      </div>

      {jobs.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-xl p-12 text-center">
          <p className="text-stone-400 text-sm">No jobs yet. Run your first simulation from the Dashboard.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <JobRow key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}
