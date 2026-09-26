import { useQuery } from "@tanstack/react-query";
import { Printer } from "lucide-react";
import { fetchDriverBrief } from "../api/client";

interface DriverBriefPageProps {
  jobId: string;
  onBack: () => void;
}

export function DriverBriefPage({ jobId, onBack }: DriverBriefPageProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["driver-brief", jobId],
    queryFn: () => fetchDriverBrief(jobId),
  });

  if (isLoading) {
    return <div className="p-8 text-stone-500 text-sm">Loading brief…</div>;
  }
  if (error || !data) {
    return (
      <div className="p-8">
        <p className="text-sm text-red-700">Could not load this driver brief. The job may still be running.</p>
        <button type="button" className="btn-secondary mt-4 text-sm" onClick={onBack}>
          Back
        </button>
      </div>
    );
  }

  const segments = data.brief.segments ?? [];
  const savings = data.savings ?? {};

  return (
    <div className="min-h-screen bg-white print:bg-white">
      <div className="max-w-3xl mx-auto px-6 py-8 print:px-0 print:py-2">
        <div className="flex items-start justify-between gap-3 print:hidden mb-6">
          <button type="button" className="btn-secondary text-sm" onClick={onBack}>
            Back
          </button>
          <button type="button" className="btn-primary inline-flex items-center gap-2 text-sm" onClick={() => window.print()}>
            <Printer size={16} />
            Print brief
          </button>
        </div>

        <p className="text-xs uppercase tracking-wide text-forest-700 font-semibold">TerraIQ driver brief</p>
        <h1 className="text-2xl font-semibold text-stone-900 mt-1">{data.route}</h1>
        <p className="text-sm text-stone-500 mt-1">
          {data.fleet_name}
          {data.vehicle_id ? ` · ${data.vehicle_id}` : ""}
          {data.brief.distance_km != null ? ` · ${Number(data.brief.distance_km).toFixed(1)} km` : ""}
        </p>

        {(savings.fuel_saved_liters != null || savings.fuel_saved_pct != null) && (
          <div className="mt-4 text-sm text-stone-700 bg-stone-50 border border-stone-200 rounded-lg p-3">
            Simulated vs baseline:{" "}
            {savings.fuel_saved_liters != null ? `${Number(savings.fuel_saved_liters).toFixed(1)} L` : "-"}{" "}
            {savings.fuel_saved_pct != null ? `(${Number(savings.fuel_saved_pct).toFixed(1)}%)` : ""}
            {savings.cost_saved_usd != null ? ` · $${Number(savings.cost_saved_usd).toFixed(2)}` : ""}
            <p className="text-xs text-stone-500 mt-1">
              Not a guarantee. Fuel on the truck is what counts; stay within posted limits.
            </p>
          </div>
        )}

        <table className="mt-6 w-full text-sm border-collapse">
          <thead>
            <tr className="text-left border-b border-stone-300">
              <th className="py-2 pr-2 font-medium">#</th>
              <th className="py-2 pr-2 font-medium">Along route (km)</th>
              <th className="py-2 pr-2 font-medium">mph</th>
              <th className="py-2 pr-2 font-medium">km/h</th>
              <th className="py-2 font-medium">Coaching</th>
            </tr>
          </thead>
          <tbody>
            {segments.map((seg, i) => (
              <tr key={`${seg.start_km}-${i}`} className="border-b border-stone-100">
                <td className="py-2 pr-2 text-stone-500">{i + 1}</td>
                <td className="py-2 pr-2">
                  {seg.start_km}–{seg.end_km}
                </td>
                <td className="py-2 pr-2 font-semibold">{seg.target_speed_mph ?? "-"}</td>
                <td className="py-2 pr-2">{seg.target_speed_kmh}</td>
                <td className="py-2 text-stone-700">{seg.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {segments.length === 0 && <p className="text-sm text-stone-500 mt-4">No speed segments for this job.</p>}
      </div>
    </div>
  );
}
