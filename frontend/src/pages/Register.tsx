import { type FormEvent, useState } from "react";
import { useAuth } from "../contexts/AuthContext";

interface RegisterProps {
  onGoLogin: () => void;
}

export function Register({ onGoLogin }: RegisterProps) {
  const { register } = useAuth();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    fleet_name: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function set(field: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form.email, form.password, form.full_name, form.fleet_name);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Registration failed. Please try again.";
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
          <h1 className="text-xl font-semibold text-stone-800">Create your account</h1>
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
              <label className="block text-sm font-medium text-stone-700 mb-1">Full name</label>
              <input
                type="text"
                required
                value={form.full_name}
                onChange={set("full_name")}
                placeholder="Alex Johnson"
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-forest-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1">
                Fleet / company name
              </label>
              <input
                type="text"
                required
                value={form.fleet_name}
                onChange={set("fleet_name")}
                placeholder="Acme Logistics"
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-forest-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1">Email</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={set("email")}
                placeholder="you@fleet.com"
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-forest-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1">
                Password <span className="text-stone-400 font-normal">(min 8 chars)</span>
              </label>
              <input
                type="password"
                required
                minLength={8}
                value={form.password}
                onChange={set("password")}
                placeholder="••••••••"
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-forest-500 focus:border-transparent"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 rounded-lg bg-forest-600 hover:bg-forest-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? "Creating account..." : "Create account"}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-stone-500">
            Already have an account?{" "}
            <button
              onClick={onGoLogin}
              className="text-forest-600 hover:text-forest-700 font-medium"
            >
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
