import { useQuery } from "@tanstack/react-query";
import { fetchOnboardingStatus } from "../api/client";
import { useAuth } from "../contexts/AuthContext";

interface OnboardingChecklistProps {
  onGoCorridors: () => void;
  onGoOps: () => void;
  onGoTelemetry: () => void;
  onDismiss: () => void;
}

export function OnboardingChecklist({
  onGoCorridors,
  onGoOps,
  onGoTelemetry,
  onDismiss,
}: OnboardingChecklistProps) {
  const { user } = useAuth();
  const { data } = useQuery({
    queryKey: ["onboarding-status"],
    queryFn: fetchOnboardingStatus,
    enabled: !!user && !user.onboarding_completed,
  });
  if (!user || user.onboarding_completed) return null;

  const steps = [
    {
      done: !!data?.starter_seeded,
      label: "Two starter mountain corridors are on Corridors",
      action: "Open corridors",
      onClick: onGoCorridors,
    },
    {
      done: (data?.completed_jobs ?? 0) > 0,
      label: "Run one optimization (Dashboard or a corridor)",
      action: null,
      onClick: undefined,
    },
    {
      done: !!data?.ready_for_brief,
      label: "Print a driver brief from the Ops board",
      action: "Ops board",
      onClick: onGoOps,
    },
    {
      done: (data?.telemetry_uploads ?? 0) > 0,
      label: "Optional: upload a GPS/speed CSV after a real trip",
      action: "Telemetry",
      onClick: onGoTelemetry,
    },
  ];

  return (
    <div className="bg-forest-50 border-b border-forest-200 px-6 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-forest-900">First pilot week</p>
          <p className="text-xs text-forest-800 mt-0.5">
            Simulated liters are a planning number. Measure the truck before you quote a percentage.
          </p>
        </div>
        <button type="button" className="btn-secondary text-xs" onClick={onDismiss}>
          Dismiss
        </button>
      </div>
      <ol className="mt-3 space-y-1.5 text-sm">
        {steps.map((s) => (
          <li key={s.label} className="flex flex-wrap items-center gap-2">
            <span className={s.done ? "text-forest-700" : "text-stone-500"}>{s.done ? "✓" : "○"}</span>
            <span className={s.done ? "text-stone-600 line-through" : "text-stone-800"}>{s.label}</span>
            {s.action && s.onClick && !s.done && (
              <button type="button" className="text-xs text-forest-700 underline" onClick={s.onClick}>
                {s.action}
              </button>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
