import { type FormEvent, useState } from "react";
import { useAuth } from "../contexts/AuthContext";

interface LoginProps {
  onGoRegister: () => void;
}

export function Login({ onGoRegister }: LoginProps) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Login failed. Check your credentials.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-stone-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="bg-white border border-stone-200 rounded-xl p-3 shadow-sm mb-4">
            <img src="/logo.png" alt="TerraIQ" className="h-12 w-auto" />
          </div>
          <h1 className="text-xl font-semibold text-stone-800">Sign in to TerraIQ</h1>
          <p className="text-sm text-stone-500 mt-1">Fleet Intelligence API</p>
        </div>

        <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm">
          {error && (
            <div className="mb-4 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@fleet.com"
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-forest-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-forest-500 focus:border-transparent"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 rounded-lg bg-forest-600 hover:bg-forest-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-stone-500">
            No account?{" "}
            <button
              onClick={onGoRegister}
              className="text-forest-600 hover:text-forest-700 font-medium"
            >
              Create one
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
