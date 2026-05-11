import { type FormEvent, useState } from "react";
import { resetPassword } from "../api/client";

interface ResetPasswordProps {
  token: string;
  onGoLogin: () => void;
}

export function ResetPassword({ token, onGoLogin }: ResetPasswordProps) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await resetPassword(token, password);
      setSuccess(true);
      // Clear token from URL without reload
      window.history.replaceState({}, "", "/");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Invalid or expired link. Please request a new one.";
      setError(detail);
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
          <h1 className="text-xl font-semibold text-stone-800">Set new password</h1>
        </div>

        <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm">
          {success ? (
            <div className="text-center space-y-4">
              <p className="text-sm text-stone-700">
                Your password has been updated.
              </p>
              <button
                onClick={onGoLogin}
                className="w-full py-2 rounded-lg bg-forest-600 hover:bg-forest-700 text-white text-sm font-medium transition-colors"
              >
                Sign in
              </button>
            </div>
          ) : (
            <>
              {error && (
                <div className="mb-4 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                  {error}
                </div>
              )}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-1">
                    New password <span className="text-stone-400 font-normal">(min 8 chars)</span>
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-forest-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-1">
                    Confirm password
                  </label>
                  <input
                    type="password"
                    required
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    placeholder="••••••••"
                    className={`w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:border-transparent ${
                      confirm && confirm !== password
                        ? "border-red-400 focus:ring-red-400"
                        : "border-stone-300 focus:ring-forest-500"
                    }`}
                  />
                  {confirm && confirm !== password && (
                    <p className="mt-1 text-xs text-red-600">Passwords do not match.</p>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={loading || (!!confirm && confirm !== password)}
                  className="w-full py-2 rounded-lg bg-forest-600 hover:bg-forest-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {loading ? "Updating…" : "Update password"}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
