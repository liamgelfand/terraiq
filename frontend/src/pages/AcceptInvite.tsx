import { type FormEvent, useEffect, useState } from "react";
import { acceptInvite, getInviteInfo } from "../api/client";
import { useAuth } from "../contexts/AuthContext";

interface AcceptInviteProps {
  token: string;
}

export function AcceptInvite({ token }: AcceptInviteProps) {
  const { refreshUser } = useAuth();
  const [fleetName, setFleetName] = useState("");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loadingInfo, setLoadingInfo] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const info = await getInviteInfo(token);
        if (!cancelled) {
          setFleetName(info.fleet_name);
          setEmail(info.email);
        }
      } catch {
        if (!cancelled) setError("Invalid or expired invitation.");
      } finally {
        if (!cancelled) setLoadingInfo(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const tok = await acceptInvite(token, fullName.trim(), password);
      localStorage.setItem("tiq_token", tok.access_token);
      await refreshUser();
      window.history.replaceState({}, "", "/");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Could not accept invitation.";
      setError(String(detail));
    }
  }

  if (loadingInfo) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center text-stone-400 text-sm">
        Loading invitation…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <h1 className="text-xl font-semibold text-stone-800 text-center mb-2">Join fleet</h1>
        <p className="text-sm text-stone-500 text-center mb-6">
          You were invited to <span className="font-medium text-stone-800">{fleetName}</span>
          <br />
          <span className="text-stone-400">{email}</span>
        </p>
        <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm">
          {error && (
            <div className="mb-4 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Full name</label>
              <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            </div>
            <div>
              <label className="label">Password (min 8 characters)</label>
              <input
                type="password"
                className="input"
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn-primary w-full">
              Join fleet
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
