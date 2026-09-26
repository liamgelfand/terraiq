import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Plus, Trash2, Check, KeyRound } from "lucide-react";
import { apiClient } from "../api/client";
import { useAuth } from "../contexts/AuthContext";

interface ApiKey {
  id: string;
  name: string;
  fleet_name: string | null;
  key_prefix: string;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  last_used_at: string | null;
}

interface ApiKeyCreated extends ApiKey {
  raw_key: string;
}

async function fetchKeys(): Promise<ApiKey[]> {
  const { data } = await apiClient.get("/api/keys");
  return data;
}

async function createKey(body: { name: string; fleet_name?: string }): Promise<ApiKeyCreated> {
  const { data } = await apiClient.post("/api/keys", body);
  return data;
}

async function revokeKey(id: string): Promise<void> {
  await apiClient.delete(`/api/keys/${id}`);
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  function copy() {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }
  return (
    <button onClick={copy} className="p-1.5 rounded hover:bg-stone-100 text-stone-400 hover:text-stone-700 transition-colors">
      {copied ? <Check size={14} className="text-forest-700" /> : <Copy size={14} />}
    </button>
  );
}

function NewKeyModal({ onClose, onCreated }: { onClose: () => void; onCreated: (key: ApiKeyCreated) => void }) {
  const [name, setName] = useState("");
  const mutation = useMutation({ mutationFn: createKey });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate(
      { name: name.trim() },
      { onSuccess: onCreated }
    );
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="card w-full max-w-md p-6 shadow-lg">
        <h2 className="text-base font-semibold text-stone-900 mb-4">Create API Key</h2>
        <form onSubmit={submit} className="flex flex-col gap-4">
          <div>
            <label className="label">Key name</label>
            <input className="input" placeholder="e.g. Production, Staging, Partner A" value={name} onChange={e => setName(e.target.value)} required />
          </div>
          <div className="flex gap-2 justify-end pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" className="btn-primary" disabled={mutation.isPending || !name.trim()}>
              {mutation.isPending ? "Creating…" : "Create key"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function KeyRevealModal({ apiKey, onClose }: { apiKey: ApiKeyCreated; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="card w-full max-w-lg p-6 shadow-lg">
        <div className="flex items-center gap-2 mb-1">
          <KeyRound size={18} className="text-forest-700" />
          <h2 className="text-base font-semibold text-stone-900">API Key Created</h2>
        </div>
        <p className="text-sm text-stone-500 mb-4">
          Copy this key now. It will <strong>not</strong> be shown again.
        </p>
        <div className="bg-stone-50 border border-stone-200 rounded-md p-3 flex items-center justify-between gap-2 mb-5">
          <code className="text-sm font-mono text-stone-800 break-all">{apiKey.raw_key}</code>
          <CopyButton text={apiKey.raw_key} />
        </div>
        <div className="text-xs text-stone-400 mb-4 space-y-1">
          <p>Pass this key in the <code className="bg-stone-100 px-1 rounded">X-API-Key</code> header of every API request.</p>
        </div>
        <div className="flex justify-end">
          <button className="btn-primary" onClick={onClose}>Done</button>
        </div>
      </div>
    </div>
  );
}

export function ApiKeys() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [showNew, setShowNew] = useState(false);
  const [revealedKey, setRevealedKey] = useState<ApiKeyCreated | null>(null);

  const { data: keys = [], isLoading } = useQuery({ queryKey: ["api-keys"], queryFn: fetchKeys });

  const revokeMutation = useMutation({
    mutationFn: revokeKey,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys"] }),
  });

  function handleCreated(key: ApiKeyCreated) {
    queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    setShowNew(false);
    setRevealedKey(key);
  }

  return (
    <div className="p-8 max-w-4xl">
      {showNew && <NewKeyModal onClose={() => setShowNew(false)} onCreated={handleCreated} />}
      {revealedKey && <KeyRevealModal apiKey={revealedKey} onClose={() => setRevealedKey(null)} />}

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">API Keys</h1>
          <p className="text-sm text-stone-500 mt-0.5">
            Use these keys to authenticate requests to <code className="bg-stone-100 px-1 rounded text-xs">/v1/optimize</code>
          </p>
          {!isAdmin && (
            <p className="text-xs text-earth-700 mt-2 bg-earth-50 border border-earth-200 rounded-md px-2 py-1.5 inline-block">
              Only fleet administrators can create or revoke keys. You can still use existing keys below.
            </p>
          )}
        </div>
        {isAdmin && (
          <button onClick={() => setShowNew(true)} className="btn-primary flex items-center gap-2">
            <Plus size={16} />
            New key
          </button>
        )}
      </div>

      {/* Usage example */}
      <div className="card p-4 mb-6 bg-stone-50">
        <p className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-2">Example request</p>
        <pre className="text-xs font-mono text-stone-700 overflow-x-auto whitespace-pre-wrap">{`curl -X POST https://api.terraiq.io/v1/optimize \\
  -H "X-API-Key: tiq_YOUR_KEY_HERE" \\
  -H "Content-Type: application/json" \\
  -d '{"origin":"Denver, CO","destination":"Grand Junction, CO","vehicle":{"load_kg":15000}}'`}</pre>
      </div>

      {/* Keys table */}
      {isLoading ? (
        <p className="text-sm text-stone-400">Loading…</p>
      ) : keys.length === 0 ? (
        <div className="card p-8 text-center">
          <KeyRound size={32} className="text-stone-300 mx-auto mb-3" />
          <p className="text-stone-500 text-sm">No API keys yet. Create one to start making requests.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-stone-50 border-b border-stone-200">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wide">Name</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wide">Fleet</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wide">Key</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wide">Requests</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wide">Last used</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wide">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {keys.map(key => (
                <tr key={key.id} className="hover:bg-stone-50">
                  <td className="px-4 py-3 font-medium text-stone-800">{key.name}</td>
                  <td className="px-4 py-3 text-stone-500">{key.fleet_name ?? "-"}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <code className="text-xs font-mono text-stone-600 bg-stone-100 px-2 py-0.5 rounded">
                        {key.key_prefix}
                      </code>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-stone-600">{key.usage_count.toLocaleString()}</td>
                  <td className="px-4 py-3 text-stone-500">
                    {key.last_used_at
                      ? new Date(key.last_used_at).toLocaleDateString()
                      : "Never"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      key.is_active
                        ? "bg-forest-50 text-forest-700 border border-forest-200"
                        : "bg-stone-100 text-stone-500"
                    }`}>
                      {key.is_active ? "Active" : "Revoked"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {isAdmin && key.is_active && (
                      <button
                        onClick={() => revokeMutation.mutate(key.id)}
                        className="p-1.5 rounded hover:bg-red-50 text-stone-400 hover:text-red-500 transition-colors"
                        title="Revoke key"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
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
