import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, Download, TrendingUp } from "lucide-react";
import { downloadJobsExport, listJobs, type Job } from "../api/client";
import { JobStatusBadge } from "../components/JobStatusBadge";
import { RouteMap } from "../components/map/RouteMap";
import { ChartsPanel } from "../components/ChartsPanel";
import { SweepChart } from "../components/charts/SweepChart";

function JobRow({ job, onOpenBrief }: { job: Job; onOpenBrief?: (jobId: string) => void }) {
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
            {job.status === "failed" && job.error_code && (
              <span className="ml-2 text-red-600 font-medium">({job.error_code})</span>
            )}
          </p>
          {job.status === "failed" && (job.error_hint || job.error_message) && (
            <p className="text-xs text-red-600 mt-1 max-w-xl">
              {job.error_hint ?? job.error_message}
            </p>
          )}
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
          {onOpenBrief && (
            <button
              type="button"
              className="btn-secondary text-sm"
              onClick={() => onOpenBrief(job.id)}
            >
              Print driver brief
            </button>
          )}
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

export function History({ onOpenBrief }: { onOpenBrief?: (jobId: string) => void }) {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [statusF, setStatusF] = useState<string>("");
  const pageSize = 15;

  const { data, isLoading } = useQuery({
    queryKey: ["jobs", page, q, statusF],
    queryFn: () =>
      listJobs({
        page,
        page_size: pageSize,
        q: q.trim() || undefined,
        status: statusF || undefined,
      }),
  });

  const jobs = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const [exporting, setExporting] = useState(false);

  async function handleExport() {
    setExporting(true);
    try {
      await downloadJobsExport();
    } finally {
      setExporting(false);
    }
  }

  if (isLoading) {
    return <div className="p-8 text-stone-400 text-sm animate-pulse">Loading…</div>;
  }

  const noFilters = !q.trim() && !statusF;

  return (
    <div className="p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-stone-800">Job History</h2>
          <p className="text-sm text-stone-500 mt-0.5">
            All optimization and sweep jobs for your fleet. Click a completed job to expand.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void handleExport()}
          disabled={exporting || total === 0}
          className="btn-secondary inline-flex items-center gap-2 self-start shrink-0"
        >
          <Download size={16} />
          {exporting ? "Exporting…" : "Export CSV"}
        </button>
      </div>

      <div className="flex flex-wrap gap-3 items-end">
        <div className="min-w-[200px]">
          <label className="label">Search</label>
          <input
            className="input"
            placeholder="Origin / destination"
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div>
          <label className="label">Status</label>
          <select
            className="input"
            value={statusF}
            onChange={(e) => {
              setStatusF(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Any</option>
            <option value="pending">Queued</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {jobs.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-xl p-12 text-center">
          <p className="text-stone-400 text-sm">
            {noFilters ? "No jobs yet. Run your first simulation from the Dashboard." : "No jobs match your filters."}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <JobRow key={job.id} job={job} onOpenBrief={onOpenBrief} />
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2 text-sm text-stone-600">
          <span>
            Page {page} of {totalPages} ({total} jobs)
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              className="btn-secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </button>
            <button
              type="button"
              className="btn-secondary"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
