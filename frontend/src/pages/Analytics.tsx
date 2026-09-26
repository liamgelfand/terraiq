import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchAnalytics, fetchKeys, listJobs, openAnalyticsReport } from "../api/client";
import { JobStatusBadge } from "../components/JobStatusBadge";

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="bg-white border border-stone-200 rounded-xl p-5">
      <p className="text-xs text-stone-500 font-medium uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-semibold text-stone-800 mt-1">{value}</p>
      {sub && <p className="text-xs text-stone-400 mt-0.5">{sub}</p>}
    </div>
  );
}

export function Analytics() {
  const { data: analytics, isLoading: loadingStats } = useQuery({
    queryKey: ["analytics"],
    queryFn: fetchAnalytics,
  });

  const { data: jobPage, isLoading: loadingJobs } = useQuery({
    queryKey: ["jobs", "analytics-preview"],
    queryFn: () => listJobs({ page: 1, page_size: 100 }),
  });

  const jobs = jobPage?.items ?? [];

  const { data: keys = [] } = useQuery({
    queryKey: ["api-keys"],
    queryFn: fetchKeys,
  });

  // Per-job savings chart data
  const chartData = jobs
    .filter((j) => j.status === "completed" && j.result)
    .slice(0, 10)
    .reverse()
    .map((j) => ({
      route: `${j.config.origin?.split(",")[0] ?? "?"}→${j.config.destination?.split(",")[0] ?? "?"}`,
      saved: Number((j.result?.savings.cost_saved_usd ?? 0).toFixed(2)),
      fuel: Number((j.result?.savings.fuel_saved_liters ?? 0).toFixed(1)),
    }));

  if (loadingStats || loadingJobs) {
    return (
      <div className="p-8 text-stone-400 text-sm animate-pulse">Loading analytics...</div>
    );
  }

  const completionRate =
    analytics && analytics.total_jobs > 0
      ? Math.round((analytics.completed_jobs / analytics.total_jobs) * 100)
      : 0;

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-stone-800">Fleet Analytics</h2>
          <p className="text-sm text-stone-500 mt-0.5">
            Simulated totals vs baseline. Print this pack for a pilot conversation, not a guarantee.
          </p>
        </div>
        <button type="button" className="btn-secondary text-sm" onClick={() => void openAnalyticsReport()}>
          Print savings report
        </button>
      </div>

      {/* KPI grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          label="Total optimizations"
          value={String(analytics?.total_jobs ?? 0)}
          sub={`${analytics?.completed_jobs ?? 0} completed · ${completionRate}% success`}
        />
        <StatCard
          label="Total cost saved"
          value={`$${(analytics?.total_cost_saved_usd ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          sub="across all completed runs"
        />
        <StatCard
          label="Fuel saved"
          value={`${(analytics?.total_fuel_saved_L ?? 0).toFixed(1)} L`}
          sub={`${(analytics?.total_distance_km ?? 0).toFixed(0)} km optimized`}
        />
        <StatCard
          label="CO₂ avoided"
          value={`${(analytics?.total_co2_saved_kg ?? 0).toFixed(1)} kg`}
          sub="diesel CO₂ equivalent"
        />
        <StatCard
          label="Active API keys"
          value={String(keys.filter((k) => k.is_active).length)}
          sub={`${keys.length} total keys`}
        />
        <StatCard
          label="Avg savings / run"
          value={
            analytics && analytics.completed_jobs > 0
              ? `$${(analytics.total_cost_saved_usd / analytics.completed_jobs).toFixed(2)}`
              : "$-"
          }
          sub="per completed optimization"
        />
      </div>

      {/* Savings per job chart */}
      {chartData.length > 0 && (
        <div className="bg-white border border-stone-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-stone-700 mb-4">
            Cost savings by route (last 10 runs)
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData} margin={{ top: 0, right: 8, left: 0, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
              <XAxis
                dataKey="route"
                tick={{ fontSize: 10, fill: "#78716c" }}
                angle={-35}
                textAnchor="end"
                interval={0}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#78716c" }}
                tickFormatter={(v) => `$${v}`}
                width={48}
              />
              <Tooltip
                formatter={(v) => [`$${Number(v).toFixed(2)}`, "Cost saved"]}
                contentStyle={{ fontSize: 12 }}
              />
              <Bar dataKey="saved" fill="#4d7c0f" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent jobs table */}
      <div className="bg-white border border-stone-200 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-stone-100">
          <h3 className="text-sm font-semibold text-stone-700">Recent jobs</h3>
        </div>
        {jobs.length === 0 ? (
          <div className="px-5 py-8 text-center text-sm text-stone-400">
            No jobs yet. Run your first optimization from the Dashboard.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-stone-50 border-b border-stone-100">
              <tr>
                <th className="px-5 py-2 text-left text-xs font-medium text-stone-500">Route</th>
                <th className="px-5 py-2 text-left text-xs font-medium text-stone-500">Status</th>
                <th className="px-5 py-2 text-right text-xs font-medium text-stone-500">
                  Fuel saved
                </th>
                <th className="px-5 py-2 text-right text-xs font-medium text-stone-500">
                  Cost saved
                </th>
                <th className="px-5 py-2 text-right text-xs font-medium text-stone-500">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-50">
              {jobs.map((job) => (
                <tr key={job.id} className="hover:bg-stone-50 transition-colors">
                  <td className="px-5 py-3 text-stone-700">
                    <span className="font-medium">{job.config.origin?.split(",")[0]}</span>
                    <span className="text-stone-400 mx-1">→</span>
                    <span>{job.config.destination?.split(",")[0]}</span>
                  </td>
                  <td className="px-5 py-3">
                    <JobStatusBadge status={job.status} />
                  </td>
                  <td className="px-5 py-3 text-right text-stone-600">
                    {job.result
                      ? `${job.result.savings.fuel_saved_liters.toFixed(1)} L`
                      : "-"}
                  </td>
                  <td className="px-5 py-3 text-right text-stone-600">
                    {job.result
                      ? `$${job.result.savings.cost_saved_usd.toFixed(2)}`
                      : "-"}
                  </td>
                  <td className="px-5 py-3 text-right text-stone-400 text-xs">
                    {new Date(job.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
