import { type FormEvent, useState } from "react";
import { useAuth } from "../contexts/AuthContext";

interface RegisterProps {
  onGoLogin: () => void;
  onGoHome?: () => void;
  onGoLegal?: (slug: "terms" | "privacy" | "pilot") => void;
}

interface FieldErrors {
  email?: string;
  general?: string;
}

function extractError(err: unknown): FieldErrors {
  const detail =
    (err as { response?: { data?: { detail?: string } } })?.response?.data
      ?.detail ?? "";
  const status = (err as { response?: { status?: number } })?.response?.status;

  if (status === 409 || detail.toLowerCase().includes("email")) {
    return { email: "An account with this email already exists." };
  }
  return { general: detail || "Registration failed. Please try again." };
}

export function Register({ onGoLogin, onGoHome, onGoLegal }: RegisterProps) {
  const { register } = useAuth();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    fleet_name: "",
  });
  const [agreed, setAgreed] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [loading, setLoading] = useState(false);

  function set(field: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setForm((f) => ({ ...f, [field]: e.target.value }));
      // Clear field-specific error as user types
      if (field === "email") setErrors((prev) => ({ ...prev, email: undefined }));
    };
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErrors({});
    if (!agreed) {
      setErrors({ general: "Please accept the Terms and Pilot Agreement to continue." });
      return;
    }
    setLoading(true);
    try {
      await register(form.email, form.password, form.full_name, form.fleet_name);
    } catch (err: unknown) {
      setErrors(extractError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-stone-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-white border border-stone-200 rounded-xl p-3 shadow-sm mb-4">
            <img src="/logo.png" alt="TerraIQ" className="h-12 w-auto" />
          </div>
          <h1 className="text-xl font-semibold text-stone-800">Create your account</h1>
          <p className="text-sm text-stone-500 mt-1">Start a trial for your fleet</p>
          {onGoHome && (
            <button type="button" onClick={onGoHome} className="text-xs text-forest-700 mt-2 hover:underline">
              ← Back to home
            </button>
          )}
        </div>

        <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm">
          {errors.general && (
            <div className="mb-4 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
              {errors.general}
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
                className={`w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:border-transparent ${
                  errors.email
                    ? "border-red-400 focus:ring-red-400 bg-red-50"
                    : "border-stone-300 focus:ring-forest-500"
                }`}
              />
              {errors.email && (
                <p className="mt-1 text-xs text-red-600">{errors.email}{" "}
                  <button
                    type="button"
                    onClick={onGoLogin}
                    className="underline font-medium"
                  >
                    Sign in instead?
                  </button>
                </p>
              )}
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
            <label className="flex items-start gap-2 text-xs text-stone-600">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
              />
              <span>
                I agree to the{" "}
                <button type="button" className="text-forest-700 underline" onClick={() => onGoLegal?.("terms")}>
                  Terms
                </button>{" "}
                and{" "}
                <button type="button" className="text-forest-700 underline" onClick={() => onGoLegal?.("pilot")}>
                  Pilot Agreement
                </button>
                .
              </span>
            </label>
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
