type LegalSlug = "terms" | "privacy" | "pilot";

interface LegalPageProps {
  slug: LegalSlug;
  onHome: () => void;
  onSignIn: () => void;
}

const COPY: Record<LegalSlug, { title: string; body: string[] }> = {
  terms: {
    title: "Terms of Service",
    body: [
      "TerraIQ provides terrain-aware speed-profile optimization and related software as a service. By creating an account you agree to these terms.",
      "The service is provided “as is.” Optimization results are simulations based on map, elevation, and vehicle models. They are decision-support tools, not a warranty of fuel use, safety, or on-time performance. You remain responsible for complying with posted speed limits, hours of service, and company policy.",
      "You must not reverse engineer the optimizer, resell access without a written agreement, or use the API in a way that degrades the service for others. We may suspend accounts that abuse rate limits or quotas.",
      "Trial (free) plans are limited. Paid pilots and subscriptions are billed through Stripe when configured. Fees are non-refundable except as required by law or as stated in a signed pilot order.",
      "We may update these terms. Continued use after notice constitutes acceptance. Governing law: the State of Colorado, USA, unless a signed order says otherwise.",
    ],
  },
  privacy: {
    title: "Privacy Policy",
    body: [
      "We collect account data (name, email, fleet name), job inputs (origins, destinations, vehicle settings), optimization results, optional telemetry CSVs you upload, and billing identifiers if you subscribe via Stripe.",
      "We use this data to run the product, enforce quotas, send transactional email (password reset, invites), and, if you submit a demo request, to contact you about a pilot.",
      "Telemetry files may include GPS traces. Do not upload data you are not authorized to share. Pilot exports omit raw GPS points from the JSON bundle; CSV packages include job-level summaries.",
      "We do not sell personal information. Subprocessors typically include our hosting provider, PostgreSQL/Redis infrastructure, Stripe (payments), and Resend (email) when those services are configured.",
      "You may export or purge fleet pilot data from Settings (administrators). To delete an account entirely, contact us. We retain backups for a limited period consistent with the documented retention target.",
    ],
  },
  pilot: {
    title: "Pilot Agreement (summary)",
    body: [
      "A TerraIQ pilot is a time-boxed engagement (typically 60-90 days) to optimize a named set of corridors, deliver driver briefs, and optionally score telemetry adherence.",
      "Setup and monthly fees are defined on the Stripe checkout page or a written quote. The trial quota applies until checkout completes and the webhook marks the fleet as a pilot plan.",
      "Success for the pilot is measured evidence: simulated vs driven speed adherence, and, when the fleet provides fuel data, a fuel delta on those lanes. TerraIQ does not guarantee a specific percentage of fuel savings.",
      "You grant TerraIQ a license to use de-identified, aggregated corridor statistics to improve the models. We will not publish your company name as a case study without written permission.",
      "Either party may end the pilot at period-end. After cancellation the fleet returns to the trial plan and quotas. This page is a product summary; a signed order (if any) controls if it conflicts.",
    ],
  },
};

export function LegalPage({ slug, onHome, onSignIn }: LegalPageProps) {
  const doc = COPY[slug];
  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-200 bg-white">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between">
          <button type="button" onClick={onHome} className="flex items-center gap-2">
            <img src="/logo.png" alt="TerraIQ" className="h-8 w-auto" />
            <span className="font-semibold">TerraIQ</span>
          </button>
          <button type="button" className="btn-secondary text-sm" onClick={onSignIn}>
            Sign in
          </button>
        </div>
      </header>
      <article className="max-w-3xl mx-auto px-4 py-10">
        <h1 className="text-2xl font-semibold text-stone-900">{doc.title}</h1>
        <p className="text-xs text-stone-500 mt-2">Last updated August 15, 2026. Not a substitute for counsel.</p>
        <div className="mt-6 space-y-4 text-sm text-stone-700 leading-relaxed">
          {doc.body.map((p) => (
            <p key={p.slice(0, 40)}>{p}</p>
          ))}
        </div>
        <button type="button" className="mt-8 text-sm text-forest-700 hover:underline" onClick={onHome}>
          ← Back to home
        </button>
      </article>
    </div>
  );
}
