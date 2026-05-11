import { useState } from "react";
import { AlertCircle, TrendingUp } from "lucide-react";
import { RouteForm } from "../components/RouteForm";
import { MetricsBar } from "../components/MetricsBar";
import { RouteMap } from "../components/map/RouteMap";
import { ChartsPanel } from "../components/ChartsPanel";
import { SweepChart } from "../components/charts/SweepChart";
import { JobStatusBadge } from "../components/JobStatusBadge";
import { useSubmitJob, useJob, useSubmitSweep } from "../hooks/useJob";
import type { JobConfig } from "../api/client";

type Mode = "optimize" | "sweep";

export function Dashboard() {
  const [mode, setMode] = useState<Mode>("optimize");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [activeSweepId, setActiveSweepId] = useState<string | null>(null);

  const submitMutation = useSubmitJob();
  const sweepMutation = useSubmitSweep();

  const { data: job } = useJob(activeJobId);
  const { data: sweepJob } = useJob(activeSweepId);

  function handleSubmit(config: JobConfig) {
    submitMutation.mutate(config, {
      onSuccess: (newJob) => {
        setActiveJobId(newJob.id);
        setMode("optimize");
      },
    });
  }

  function handleSweep(config: Pick<JobConfig, "origin" | "destination" | "vehicle_id">) {
    sweepMutation.mutate(config, {
      onSuccess: (newJob) => {
        setActiveSweepId(newJob.id);
        setMode("sweep");
      },
    });
  }

  const isOptimizing =
    submitMutation.isPending ||
    job?.status === "pending" ||
    job?.status === "running";

  const isSweeping =
    sweepMutation.isPending ||
    sweepJob?.status === "pending" ||
    sweepJob?.status === "running";

  const hasOptResults = job?.status === "completed" && job.result;
  const hasSweepResults =
    sweepJob?.status === "completed" && sweepJob.result?.curve;

  const activeJob = mode === "sweep" ? sweepJob : job;
  const isLoading = mode === "sweep" ? isSweeping : isOptimizing;

  return (
    <div className="flex flex-col h-full">
      {/* Metrics bar */}
      {hasOptResults && mode === "optimize" && (
        <MetricsBar
          baseline={job.result!.baseline}
          savings={job.result!.savings}
        />
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* ── Left panel ── */}
        <aside className="w-72 flex-shrink-0 border-r border-stone-200 bg-white overflow-y-auto">
          <div className="p-5">
            {/* Mode toggle */}
            <div className="flex rounded-lg border border-stone-200 p-0.5 mb-5">
              <button
                onClick={() => setMode("optimize")}
                className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  mode === "optimize"
                    ? "bg-forest-600 text-white"
                    : "text-stone-500 hover:text-stone-700"
                }`}
              >
                Optimize
              </button>
              <button
                onClick={() => setMode("sweep")}
                className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-colors flex items-center justify-center gap-1 ${
                  mode === "sweep"
                    ? "bg-forest-600 text-white"
                    : "text-stone-500 hover:text-stone-700"
                }`}
              >
                <TrendingUp size={12} />
                Pareto Sweep
              </button>
            </div>

            <div className="flex items-center justify-between mb-5">
              <h1 className="text-base font-semibold text-stone-900">
                {mode === "optimize" ? "Route Optimization" : "Time vs. Savings"}
              </h1>
              {activeJob && <JobStatusBadge status={activeJob.status} />}
            </div>

            {mode === "optimize" ? (
              <RouteForm onSubmit={handleSubmit} isLoading={isOptimizing} />
            ) : (
              <RouteForm
                onSubmit={(cfg) =>
                  handleSweep({
                    origin: cfg.origin,
                    destination: cfg.destination,
                    vehicle_id: cfg.vehicle_id,
                  })
                }
                isLoading={isSweeping}
                sweepMode
              />
            )}

            {/* Error */}
            {activeJob?.status === "failed" && activeJob.error_message && (
              <div className="mt-4 p-3 rounded-md bg-red-50 border border-red-200 flex gap-2">
                <AlertCircle size={16} className="text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-red-700">{activeJob.error_message}</p>
              </div>
            )}

            {/* Running hint */}
            {isLoading && (
              <div className="mt-4 p-3 rounded-md bg-stone-50 border border-stone-200">
                <p className="text-xs text-stone-500">
                  {mode === "sweep"
                    ? "Running optimizer at 6 time budgets. This takes 3–8 minutes."
                    : "Fetching route and running MPC optimizer. This typically takes 1–3 minutes."}
                </p>
              </div>
            )}

            {/* Sweep explanation when idle */}
            {mode === "sweep" && !isSweeping && !hasSweepResults && (
              <div className="mt-4 p-3 rounded-md bg-stone-50 border border-stone-200">
                <p className="text-xs text-stone-500 leading-relaxed">
                  Runs the optimizer at 6 different time budgets and plots the
                  cost savings vs. extra time trade-off (Pareto curve).
                </p>
              </div>
            )}
          </div>
        </aside>

        {/* ── Right area ── */}
        <div className="flex-1 flex flex-col overflow-hidden bg-stone-50 gap-3 p-3">
          {mode === "sweep" ? (
            // Sweep results panel
            hasSweepResults ? (
              <div className="flex-1 bg-white border border-stone-200 rounded-lg p-5 overflow-auto">
                <h2 className="text-sm font-semibold text-stone-800 mb-4">
                  Pareto Frontier — Cost Savings vs. Extra Time
                </h2>
                <SweepChart
                  curve={sweepJob!.result!.curve!}
                  baselineFuelL={sweepJob!.result!.baseline_fuel_L ?? 0}
                  distanceKm={sweepJob!.result!.distance_km ?? 0}
                />
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-stone-300 text-sm">
                {isSweeping
                  ? "Running sweep…"
                  : "Enter a route and click Run Sweep"}
              </div>
            )
          ) : (
            // Optimize results
            <>
              <div className="flex-1 min-h-0 rounded-lg overflow-hidden border border-stone-200">
                <RouteMap
                  baseline={hasOptResults ? job.result!.baseline : undefined}
                  optimized={hasOptResults ? job.result!.optimized : undefined}
                />
              </div>
              {hasOptResults && (
                <div className="h-64 flex-shrink-0">
                  <ChartsPanel result={job.result!} />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
