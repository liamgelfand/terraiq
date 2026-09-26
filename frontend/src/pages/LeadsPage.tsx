import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchLeads, updateLeadStatus, type LeadRow } from "../api/client";

const STATUSES = ["new", "contacted", "won", "lost"] as const;

export function LeadsPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["leads"], queryFn: fetchLeads });
  const mut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => updateLeadStatus(id, status),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["leads"] }),
  });

  if (isLoading) return <p className="p-6 text-sm text-stone-500">Loading leads…</p>;

  return (
    <div className="p-6 max-w-5xl">
      <h1 className="text-xl font-semibold text-stone-900">Pilot leads</h1>
      <p className="text-sm text-stone-600 mt-1">
        From the landing-page form. Follow up here. This is how the first paid pilots start.
      </p>
      <div className="mt-4 overflow-x-auto border border-stone-200 rounded-lg bg-white">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-stone-200 bg-stone-50 text-left">
              <th className="px-3 py-2 font-medium">When</th>
              <th className="px-3 py-2 font-medium">Company</th>
              <th className="px-3 py-2 font-medium">Contact</th>
              <th className="px-3 py-2 font-medium">Size</th>
              <th className="px-3 py-2 font-medium">Note</th>
              <th className="px-3 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((row: LeadRow) => (
              <tr key={row.id} className="border-b border-stone-100 align-top">
                <td className="px-3 py-2 text-stone-500 whitespace-nowrap">
                  {row.created_at ? new Date(row.created_at).toLocaleString() : "-"}
                </td>
                <td className="px-3 py-2 font-medium">{row.company}</td>
                <td className="px-3 py-2">
                  {row.name}
                  <br />
                  <a className="text-forest-700 underline" href={`mailto:${row.email}`}>
                    {row.email}
                  </a>
                </td>
                <td className="px-3 py-2">{row.fleet_size || "-"}</td>
                <td className="px-3 py-2 max-w-xs text-stone-600">{row.message || "-"}</td>
                <td className="px-3 py-2">
                  <select
                    className="input py-1"
                    value={row.status}
                    onChange={(e) => mut.mutate({ id: row.id, status: e.target.value })}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data && data.length === 0 && (
        <p className="text-sm text-stone-500 mt-4">No leads yet. Share the landing page.</p>
      )}
    </div>
  );
}
