import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  createCorridor,
  deleteCorridor,
  duplicateCorridor,
  fetchCorridors,
  type SavedCorridor,
} from "../api/client";

export function CorridorsPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["corridors"], queryFn: fetchCorridors });
  const [name, setName] = useState("");
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [vehicleId, setVehicleId] = useState("freightliner_2022");

  const createMut = useMutation({
    mutationFn: () =>
      createCorridor({
        name: name.trim(),
        origin: origin.trim(),
        destination: destination.trim(),
        vehicle_id: vehicleId,
      }),
    onSuccess: () => {
      setName("");
      setOrigin("");
      setDestination("");
      void qc.invalidateQueries({ queryKey: ["corridors"] });
      void qc.invalidateQueries({ queryKey: ["ops-board"] });
    },
  });

  const dupMut = useMutation({
    mutationFn: (id: string) => duplicateCorridor(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["corridors"] });
    },
  });

  const delMut = useMutation({
    mutationFn: (id: string) => deleteCorridor(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["corridors"] });
      void qc.invalidateQueries({ queryKey: ["ops-board"] });
    },
  });

  return (
    <div className="p-6 max-w-4xl">
      <h1 className="text-xl font-semibold text-stone-900 mb-1">Saved corridors</h1>
      <p className="text-sm text-stone-600 mb-6">
        Lane library for batch runs and ops reporting. Use the same spelling you want for optimization jobs.
      </p>

      <div className="bg-white border border-stone-200 rounded-lg p-4 mb-8 shadow-sm">
        <h2 className="text-sm font-medium text-stone-800 mb-3">Add corridor</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            className="border border-stone-300 rounded px-3 py-2 text-sm"
            placeholder="Name (e.g. I-70 westbound)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="border border-stone-300 rounded px-3 py-2 text-sm"
            placeholder="Vehicle profile id"
            value={vehicleId}
            onChange={(e) => setVehicleId(e.target.value)}
          />
          <input
            className="border border-stone-300 rounded px-3 py-2 text-sm sm:col-span-2"
            placeholder="Origin"
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
          />
          <input
            className="border border-stone-300 rounded px-3 py-2 text-sm sm:col-span-2"
            placeholder="Destination"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
          />
        </div>
        <button
          type="button"
          className="mt-4 px-4 py-2 bg-forest-700 text-white text-sm rounded-md hover:bg-forest-800 disabled:opacity-50"
          disabled={createMut.isPending || !name.trim() || !origin.trim() || !destination.trim()}
          onClick={() => createMut.mutate()}
        >
          {createMut.isPending ? "Saving…" : "Save corridor"}
        </button>
        {createMut.isError && (
          <p className="text-sm text-red-600 mt-2">Could not save — check inputs or try again.</p>
        )}
      </div>

      {isLoading && <p className="text-stone-500 text-sm">Loading…</p>}
      {data && data.length === 0 && !isLoading && (
        <p className="text-stone-500 text-sm">No corridors yet — add one above.</p>
      )}
      <ul className="space-y-2">
        {(data ?? []).map((c: SavedCorridor) => (
          <li
            key={c.id}
            className="flex flex-wrap items-center justify-between gap-2 bg-white border border-stone-200 rounded-lg px-4 py-3 shadow-sm"
          >
            <div>
              <p className="font-medium text-stone-900">{c.name}</p>
              <p className="text-xs text-stone-600">
                {c.origin} → {c.destination}
              </p>
              <p className="text-xs text-stone-500 mt-0.5">Vehicle: {c.vehicle_id}</p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                className="text-xs px-2 py-1 border border-stone-300 rounded hover:bg-stone-50"
                onClick={() => dupMut.mutate(c.id)}
                disabled={dupMut.isPending}
              >
                Duplicate
              </button>
              <button
                type="button"
                className="text-xs px-2 py-1 border border-red-200 text-red-700 rounded hover:bg-red-50"
                onClick={() => {
                  if (window.confirm(`Delete “${c.name}”?`)) delMut.mutate(c.id);
                }}
                disabled={delMut.isPending}
              >
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
