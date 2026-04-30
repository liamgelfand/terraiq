import { useState } from "react";
import { AlertCircle } from "lucide-react";
import { RouteForm } from "../components/RouteForm";
import { MetricsBar } from "../components/MetricsBar";
import { RouteMap } from "../components/map/RouteMap";
import { ChartsPanel } from "../components/ChartsPanel";
import { JobStatusBadge } from "../components/JobStatusBadge";
import { useSubmitJob, useJob } from "../hooks/useJob";
import type { JobConfig } from "../api/client";

export function Dashboard() {
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const submitMutation = useSubmitJob();
  const { data: job } = useJob(activeJobId);

  function handleSubmit(config: JobConfig) {
    submitMutation.mutate(config, {
      onSuccess: (newJob) => setActiveJobId(newJob.id),
    });
  }

  const isRunning = job?.status === "pending" || job?.status === "running";
  const isLoading = submitMutation.isPending || isRunning;
  const hasResults = job?.status === "completed" && job.result;

  return (
    <div className="flex flex-col h-full">
      {/* Metrics bar — only visible when results ready */}
      {hasResults && (
        <MetricsBar
          baseline={job.result!.baseline}
          savings={job.result!.savings}
        />
      )}

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel */}
        <aside className="w-72 flex-shrink-0 border-r border-stone-200 bg-white overflow-y-auto">
          <div className="p-5">
            <div className="flex items-center justify-between mb-5">
              <h1 className="text-base font-semibold text-stone-900">Route Optimization</h1>
              {job && <JobStatusBadge status={job.status} />}
            </div>

            <RouteForm onSubmit={handleSubmit} isLoading={isLoading} />

            {/* Error state */}
            {job?.status === "failed" && job.error_message && (
              <div className="mt-4 p-3 rounded-md bg-red-50 border border-red-200 flex gap-2">
                <AlertCircle size={16} className="text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-red-700">{job.error_message}</p>
              </div>
            )}

            {/* Running state info */}
            {isRunning && (
              <div className="mt-4 p-3 rounded-md bg-stone-50 border border-stone-200">
                <p className="text-xs text-stone-500">
                  Fetching route and running MPC optimizer. This typically takes 1–3 minutes.
                </p>
              </div>
            )}
          </div>
        </aside>

        {/* Right area: map + charts */}
        <div className="flex-1 flex flex-col overflow-hidden bg-stone-50 gap-3 p-3">
          {/* Map */}
          <div className="flex-1 min-h-0 rounded-lg overflow-hidden border border-stone-200">
            <RouteMap
              baseline={hasResults ? job.result!.baseline : undefined}
              optimized={hasResults ? job.result!.optimized : undefined}
            />
          </div>

          {/* Charts — only when results available */}
          {hasResults && (
            <div className="h-64 flex-shrink-0">
              <ChartsPanel result={job.result!} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
