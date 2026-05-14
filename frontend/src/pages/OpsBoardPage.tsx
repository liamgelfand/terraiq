import { useQuery } from "@tanstack/react-query";
import { downloadPilotPackageCsv, fetchOpsBoard, type OpsBoardRow } from "../api/client";

export function OpsBoardPage() {
  const { data, isLoading, refetch } = useQuery({ queryKey: ["ops-board"], queryFn: fetchOpsBoard });

  return (
    <div className="p-6 max-w-6xl">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">Ops board</h1>
          <p className="text-sm text-stone-600">Latest job and adherence by saved corridor.</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="text-sm px-3 py-2 border border-stone-300 rounded-md hover:bg-stone-50"
            onClick={() => void refetch()}
          >
            Refresh
          </button>
          <button
            type="button"
            className="text-sm px-3 py-2 bg-forest-700 text-white rounded-md hover:bg-forest-800"
            onClick={() => void downloadPilotPackageCsv()}
          >
            Download pilot CSV
          </button>
        </div>
      </div>

      {isLoading && <p className="text-stone-500 text-sm">Loading…</p>}
      <div className="overflow-x-auto border border-stone-200 rounded-lg bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-stone-200 bg-stone-50 text-left text-stone-700">
              <th className="px-3 py-2 font-medium">Corridor</th>
              <th className="px-3 py-2 font-medium">Route</th>
              <th className="px-3 py-2 font-medium">Last job</th>
              <th className="px-3 py-2 font-medium">Fuel saved (L)</th>
              <th className="px-3 py-2 font-medium">Adherence %</th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((row: OpsBoardRow) => (
              <tr key={row.corridor_id} className="border-b border-stone-100">
                <td className="px-3 py-2 font-medium text-stone-900">{row.corridor_name}</td>
                <td className="px-3 py-2 text-stone-600 max-w-xs truncate">
                  {row.origin} → {row.destination}
                </td>
                <td className="px-3 py-2">
                  {row.last_job_id ? (
                    <span className="font-mono text-xs text-stone-700">
                      {row.last_job_id.slice(0, 8)}… ({row.last_job_status})
                    </span>
                  ) : (
                    <span className="text-stone-400">—</span>
                  )}
                </td>
                <td className="px-3 py-2 text-stone-800">
                  {row.fuel_saved_liters != null ? row.fuel_saved_liters.toFixed(2) : "—"}
                </td>
                <td className="px-3 py-2">
                  {row.adherence_pct != null ? (
                    <span className="text-forest-800 font-medium">{row.adherence_pct}%</span>
                  ) : (
                    <span className="text-stone-400">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data && data.length === 0 && !isLoading && (
        <p className="text-stone-500 text-sm mt-4">No corridors — add some under Corridors.</p>
      )}
    </div>
  );
}
