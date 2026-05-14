import { useQuery } from "@tanstack/react-query";
import { fetchAuditLog } from "../api/client";

export function AuditLog() {
  const { data, isLoading } = useQuery({
    queryKey: ["audit-log"],
    queryFn: () => fetchAuditLog(1, 50),
  });

  if (isLoading) {
    return <div className="p-8 text-stone-400 text-sm animate-pulse">Loading…</div>;
  }

  const rows = data?.items ?? [];

  return (
    <div className="p-6 space-y-4 max-w-5xl">
      <div>
        <h2 className="text-lg font-semibold text-stone-800">Audit log</h2>
        <p className="text-sm text-stone-500 mt-0.5">Recent fleet administration events.</p>
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-stone-400">No events yet.</p>
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-stone-200 text-left text-stone-500">
                <th className="py-2 pr-4 font-medium">Time</th>
                <th className="py-2 pr-4 font-medium">Action</th>
                <th className="py-2 pr-4 font-medium">Resource</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-b border-stone-100">
                  <td className="py-2 pr-4 text-stone-600 whitespace-nowrap">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="py-2 pr-4 font-medium text-stone-800">{r.action}</td>
                  <td className="py-2 pr-4 text-stone-600">
                    {r.resource_type}
                    {r.resource_id ? ` · ${r.resource_id.slice(0, 8)}…` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
