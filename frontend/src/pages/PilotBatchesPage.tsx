import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { createJobBatch, fetchCorridors, listJobBatches, type SavedCorridor } from "../api/client";

export function PilotBatchesPage() {
  const qc = useQueryClient();
  const { data: corridors } = useQuery({ queryKey: ["corridors"], queryFn: fetchCorridors });
  const { data: batches, isLoading } = useQuery({ queryKey: ["batches"], queryFn: () => listJobBatches(1) });
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [batchName, setBatchName] = useState("");

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const batchMut = useMutation({
    mutationFn: () => createJobBatch(Array.from(selected), batchName.trim() || undefined),
    onSuccess: () => {
      setBatchName("");
      void qc.invalidateQueries({ queryKey: ["batches"] });
      void qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const corridorList: SavedCorridor[] = useMemo(() => corridors ?? [], [corridors]);

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-xl font-semibold text-stone-900 mb-1">Batch optimization</h1>
      <p className="text-sm text-stone-600 mb-6">
        Queue one optimization job per selected corridor. Workers process them asynchronously.
      </p>

      <div className="bg-white border border-stone-200 rounded-lg p-4 mb-8 shadow-sm">
        <h2 className="text-sm font-medium text-stone-800 mb-3">Select corridors</h2>
        {corridorList.length === 0 && <p className="text-sm text-stone-500">Add corridors first.</p>}
        <ul className="max-h-56 overflow-y-auto space-y-1 mb-3">
          {corridorList.map((c) => (
            <li key={c.id}>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={selected.has(c.id)}
                  onChange={() => toggle(c.id)}
                />
                <span>
                  {c.name} — {c.origin} → {c.destination}
                </span>
              </label>
            </li>
          ))}
        </ul>
        <input
          className="border border-stone-300 rounded px-3 py-2 text-sm w-full max-w-md mb-3"
          placeholder="Optional batch label"
          value={batchName}
          onChange={(e) => setBatchName(e.target.value)}
        />
        <button
          type="button"
          className="px-4 py-2 bg-forest-700 text-white text-sm rounded-md hover:bg-forest-800 disabled:opacity-50"
          disabled={batchMut.isPending || selected.size === 0}
          onClick={() => batchMut.mutate()}
        >
          {batchMut.isPending ? "Starting…" : "Run batch"}
        </button>
        {batchMut.isError && (
          <p className="text-sm text-red-600 mt-2">Batch could not be started.</p>
        )}
      </div>

      <h2 className="text-sm font-medium text-stone-800 mb-2">Recent batches</h2>
      {isLoading && <p className="text-stone-500 text-sm">Loading…</p>}
      <ul className="space-y-2">
        {(batches?.items ?? []).map((b) => (
          <li key={b.id} className="bg-white border border-stone-200 rounded-lg px-4 py-3 text-sm shadow-sm">
            <p className="font-medium text-stone-900">{b.name ?? b.id.slice(0, 8)}</p>
            <p className="text-stone-600">
              Status: <span className="font-mono">{b.status}</span>
            </p>
            {b.summary && (
              <p className="text-xs text-stone-500 mt-1">
                Completed jobs summary: {JSON.stringify(b.summary)}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
