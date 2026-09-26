import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { fetchCorridors, listTelemetryUploads, submitTelemetryUpload, type TelemetryUploadRow } from "../api/client";

export function TelemetryPage() {
  const qc = useQueryClient();
  const { data: uploads, isLoading } = useQuery({
    queryKey: ["telemetry"],
    queryFn: () => listTelemetryUploads(1),
  });
  const { data: corridors } = useQuery({ queryKey: ["corridors"], queryFn: fetchCorridors });
  const [jobId, setJobId] = useState("");
  const [corridorId, setCorridorId] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const upMut = useMutation({
    mutationFn: () => {
      if (!file) throw new Error("file");
      return submitTelemetryUpload(file, jobId.trim(), corridorId.trim() || undefined);
    },
    onSuccess: () => {
      setFile(null);
      void qc.invalidateQueries({ queryKey: ["telemetry"] });
      void qc.invalidateQueries({ queryKey: ["ops-board"] });
    },
  });

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-xl font-semibold text-stone-900 mb-1">Telemetry & adherence</h1>
      <p className="text-sm text-stone-600 mb-6">
        Upload a CSV with columns <code className="text-xs bg-stone-100 px-1 rounded">lat</code>,{" "}
        <code className="text-xs bg-stone-100 px-1 rounded">lon</code>, and optionally{" "}
        <code className="text-xs bg-stone-100 px-1 rounded">speed_kmh</code>. Link to a completed
        optimization job for adherence scoring.
      </p>

      <div className="bg-white border border-stone-200 rounded-lg p-4 mb-8 shadow-sm space-y-3">
        <input
          className="border border-stone-300 rounded px-3 py-2 text-sm w-full max-w-lg"
          placeholder="Completed job id (UUID)"
          value={jobId}
          onChange={(e) => setJobId(e.target.value)}
        />
        <div>
          <label className="text-xs text-stone-600 block mb-1">Corridor (optional, for ops board)</label>
          <select
            className="border border-stone-300 rounded px-3 py-2 text-sm w-full max-w-lg bg-white"
            value={corridorId}
            onChange={(e) => setCorridorId(e.target.value)}
          >
            <option value="">- None -</option>
            {(corridors ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <input
          type="file"
          accept=".csv,text/csv"
          className="text-sm"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <button
          type="button"
          className="px-4 py-2 bg-forest-700 text-white text-sm rounded-md hover:bg-forest-800 disabled:opacity-50"
          disabled={upMut.isPending || !file || !jobId.trim()}
          onClick={() => upMut.mutate()}
        >
          {upMut.isPending ? "Uploading…" : "Upload & process"}
        </button>
        {upMut.isError && (
          <p className="text-sm text-red-600">Upload failed. Check job id and CSV format.</p>
        )}
      </div>

      <h2 className="text-sm font-medium text-stone-800 mb-2">Uploads</h2>
      {isLoading && <p className="text-stone-500 text-sm">Loading…</p>}
      <ul className="space-y-2">
        {(uploads?.items ?? []).map((u: TelemetryUploadRow) => (
          <li key={u.id} className="bg-white border border-stone-200 rounded-lg px-4 py-3 text-sm shadow-sm">
            <p className="font-mono text-xs text-stone-500">{u.id}</p>
            <p className="text-stone-800">{u.original_filename}</p>
            <p className="text-stone-600">
              Status: {u.status} - rows: {u.row_count}
            </p>
            {u.adherence && typeof u.adherence.pct_in_band === "number" && (
              <p className="text-forest-800 font-medium mt-1">
                Adherence: {u.adherence.pct_in_band}% in band
              </p>
            )}
            {u.error_message && <p className="text-red-600 text-xs mt-1">{u.error_message}</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}
