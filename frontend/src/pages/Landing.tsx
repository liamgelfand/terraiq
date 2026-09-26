import { type FormEvent, useState } from "react";
import { Fuel, MapPinned, Route, ShieldCheck } from "lucide-react";
import { submitDemoRequest } from "../api/client";
import { extractApiError } from "../lib/errors";

interface LandingProps {
  onSignIn: () => void;
  onRegister: () => void;
  onLegal: (slug: "terms" | "privacy" | "pilot") => void;
}

export function Landing({ onSignIn, onRegister, onLegal }: LandingProps) {
  const [form, setForm] = useState({
    name: "",
    email: "",
    company: "",
    fleet_size: "",
    message: "",
  });
  const [sending, setSending] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  async function handleDemo(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSending(true);
    try {
      await submitDemoRequest({
        name: form.name.trim(),
        email: form.email.trim(),
        company: form.company.trim(),
        fleet_size: form.fleet_size.trim() || undefined,
        message: form.message.trim() || undefined,
      });
      setDone(true);
    } catch (err) {
      setError(extractApiError(err, "Could not send the request. Try emailing us instead."));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="min-h-screen bg-stone-50 text-stone-900">
      <header className="border-b border-stone-200 bg-white">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="TerraIQ" className="h-8 w-auto" />
            <span className="font-semibold tracking-tight">TerraIQ</span>
          </div>
          <div className="flex items-center gap-2">
            <button type="button" className="btn-secondary text-sm" onClick={onSignIn}>
              Sign in
            </button>
            <button type="button" className="btn-primary text-sm" onClick={onRegister}>
              Create account
            </button>
          </div>
        </div>
      </header>

      <main>
        <section className="bg-forest-800 text-white">
          <div className="max-w-5xl mx-auto px-4 py-16 md:py-20 grid md:grid-cols-2 gap-10 items-center">
            <div>
              <p className="text-forest-200 text-xs font-medium uppercase tracking-wider mb-3">
                Terrain-aware fuel optimization
              </p>
              <h1 className="text-3xl md:text-4xl font-semibold leading-tight">
                Tell the truck how fast to drive each hill, not just which road to take.
              </h1>
              <p className="mt-4 text-forest-100 text-base leading-relaxed">
                TerraIQ builds a physics-based speed profile from real highway grades and your
                vehicle. Dispatchers get a printable driver brief. Fleets measure whether drivers
                can follow it. We do not guarantee a fuel percentage until your corridors are
                measured.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <button type="button" className="btn-primary bg-white text-forest-800 hover:bg-forest-50" onClick={onRegister}>
                  Start a trial
                </button>
                <a
                  href="#pilot"
                  className="inline-flex items-center justify-center font-medium rounded-md px-4 py-2 border border-white bg-transparent text-white hover:bg-forest-700"
                >
                  Paid 60-90 day pilot
                </a>
              </div>
            </div>
            <ul className="space-y-3 text-sm">
              {[
                { icon: <Route size={18} />, t: "Saved corridors", d: "Your repeating lanes, batched overnight." },
                { icon: <MapPinned size={18} />, t: "Driver briefs", d: "Mile-by-mile target speeds, ready to print." },
                { icon: <Fuel size={18} />, t: "Adherence", d: "Upload GPS/speed CSV and score vs the profile." },
                { icon: <ShieldCheck size={18} />, t: "API + webhooks", d: "Same optimizer your dashboard uses." },
              ].map((item) => (
                <li key={item.t} className="flex gap-3 bg-forest-700/60 rounded-lg p-3">
                  <span className="mt-0.5 text-forest-200">{item.icon}</span>
                  <span>
                    <span className="font-medium">{item.t}</span>
                    <span className="block text-forest-100/90">{item.d}</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="max-w-5xl mx-auto px-4 py-14">
          <h2 className="text-xl font-semibold">How a pilot works</h2>
          <ol className="mt-6 grid md:grid-cols-3 gap-4">
            {[
              { n: "1", t: "Load 5-15 lanes", d: "Origins, destinations, vehicle, and typical payload. We optimize each corridor." },
              { n: "2", t: "Coach the speed", d: "Print the driver brief. Hold the target on grades. This is not another routing app." },
              { n: "3", t: "Measure", d: "Upload ELD/GPS CSV. Compare adherence and fuel to the simulated baseline before you scale." },
            ].map((s) => (
              <li key={s.n} className="card p-5">
                <p className="text-forest-700 text-xs font-semibold uppercase tracking-wide">Step {s.n}</p>
                <p className="font-semibold mt-1">{s.t}</p>
                <p className="text-sm text-stone-600 mt-2">{s.d}</p>
              </li>
            ))}
          </ol>
        </section>

        <section id="pilot" className="bg-white border-y border-stone-200">
          <div className="max-w-5xl mx-auto px-4 py-14 grid md:grid-cols-2 gap-10">
            <div>
              <h2 className="text-xl font-semibold">Paid pilot, not a self-serve gamble</h2>
              <p className="text-sm text-stone-600 mt-3 leading-relaxed">
                Built for small and mid-size fleets with repeating mountain or rolling-terrain
                lanes. Trial accounts can run a limited number of optimizations per month. A paid
                pilot raises those limits, includes setup of your corridors, and gives you a
                weekly ops pack (briefs + adherence).
              </p>
              <p className="text-sm text-stone-600 mt-3 leading-relaxed">
                Simulated savings on a corridor are a planning number. The commercial claim is
                whatever you measure on the truck while drivers stay in-band.
              </p>
            </div>
            <form onSubmit={handleDemo} className="card p-5 space-y-3">
              <h3 className="text-sm font-semibold">Request a pilot conversation</h3>
              {done ? (
                <p className="text-sm text-forest-800">
                  Thanks. We logged your request and will follow up at the email you provided.
                </p>
              ) : (
                <>
                  {error && (
                    <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">{error}</p>
                  )}
                  <input className="input" required placeholder="Your name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                  <input className="input" required type="email" placeholder="Work email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
                  <input className="input" required placeholder="Fleet / company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
                  <input className="input" placeholder="Power units (e.g. 40)" value={form.fleet_size} onChange={(e) => setForm({ ...form, fleet_size: e.target.value })} />
                  <textarea
                    className="input min-h-[88px]"
                    placeholder="Corridors you care about (e.g. Denver-Grand Junction)"
                    value={form.message}
                    onChange={(e) => setForm({ ...form, message: e.target.value })}
                  />
                  <button type="submit" className="btn-primary w-full" disabled={sending}>
                    {sending ? "Sending…" : "Request a pilot"}
                  </button>
                </>
              )}
            </form>
          </div>
        </section>
      </main>

      <footer className="max-w-5xl mx-auto px-4 py-8 text-xs text-stone-500 flex flex-wrap gap-4 justify-between">
        <p>© {new Date().getFullYear()} TerraIQ. Simulation is not a fuel guarantee.</p>
        <div className="flex gap-4">
          <button type="button" className="hover:text-stone-800" onClick={() => onLegal("terms")}>Terms</button>
          <button type="button" className="hover:text-stone-800" onClick={() => onLegal("privacy")}>Privacy</button>
          <button type="button" className="hover:text-stone-800" onClick={() => onLegal("pilot")}>Pilot agreement</button>
        </div>
      </footer>
    </div>
  );
}
