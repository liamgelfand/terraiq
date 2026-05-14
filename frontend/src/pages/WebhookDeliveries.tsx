import { useQuery } from "@tanstack/react-query";
import { fetchWebhookDeliveries } from "../api/client";

export function WebhookDeliveries() {
  const { data, isLoading } = useQuery({
    queryKey: ["webhook-deliveries"],
    queryFn: () => fetchWebhookDeliveries(1, 50),
  });

  if (isLoading) {
    return <div className="p-8 text-stone-400 text-sm animate-pulse">Loading…</div>;
  }

  const rows = data?.items ?? [];

  return (
    <div className="p-6 space-y-4 max-w-5xl">
      <div>
        <h2 className="text-lg font-semibold text-stone-800">Webhook deliveries</h2>
        <p className="text-sm text-stone-500 mt-0.5">
          Outbound job webhooks with HTTP status per attempt (retries may appear as multiple rows).
        </p>
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-stone-400">No webhook deliveries recorded yet.</p>
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-stone-200 text-left text-stone-500">
                <th className="py-2 pr-4 font-medium">Time</th>
                <th className="py-2 pr-4 font-medium">Job</th>
                <th className="py-2 pr-4 font-medium">Attempt</th>
                <th className="py-2 pr-4 font-medium">Status</th>
                <th className="py-2 pr-4 font-medium">URL</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-b border-stone-100">
                  <td className="py-2 pr-4 text-stone-600 whitespace-nowrap">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="py-2 pr-4 font-mono text-xs">{r.job_id.slice(0, 8)}…</td>
                  <td className="py-2 pr-4">{r.attempt}</td>
                  <td className="py-2 pr-4">{r.http_status ?? "—"}</td>
                  <td className="py-2 pr-4 text-stone-600 truncate max-w-xs" title={r.url}>
                    {r.url}
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
