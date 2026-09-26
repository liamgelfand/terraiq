import { type FormEvent, useState } from "react";
import { forgotPassword } from "../api/client";

interface ForgotPasswordProps {
  onGoLogin: () => void;
}

export function ForgotPassword({ onGoLogin }: ForgotPasswordProps) {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await forgotPassword(email);
      setSubmitted(true);
    } catch {
      setError("Something went wrong. Please try again.");
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
          <h1 className="text-xl font-semibold text-stone-800">Reset your password</h1>
          <p className="text-sm text-stone-500 mt-1">
            We'll send a reset link if email is configured.
          </p>
        </div>

        <div className="bg-white border border-stone-200 rounded-xl p-6 shadow-sm">
          {submitted ? (
            <div className="text-center space-y-4">
              <p className="text-sm text-stone-700">
                If <span className="font-medium">{email}</span> is registered, a reset
                link has been printed to the server console.
              </p>
              <p className="text-xs text-stone-400">
                Check the uvicorn terminal window for the link.
              </p>
              <button
                onClick={onGoLogin}
                className="w-full py-2 rounded-lg bg-forest-600 hover:bg-forest-700 text-white text-sm font-medium transition-colors"
              >
                Back to sign in
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
                    Email address
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@fleet.com"
                    className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-forest-500 focus:border-transparent"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2 rounded-lg bg-forest-600 hover:bg-forest-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {loading ? "Sending…" : "Send reset link"}
                </button>
              </form>
              <p className="mt-4 text-center text-sm text-stone-500">
                <button
                  onClick={onGoLogin}
                  className="text-forest-600 hover:text-forest-700 font-medium"
                >
                  Back to sign in
                </button>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
