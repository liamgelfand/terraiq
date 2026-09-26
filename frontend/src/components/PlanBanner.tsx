import { useQuery } from "@tanstack/react-query";
import { fetchFleetUsage } from "../api/client";

interface PlanBannerProps {
  onOpenSettings: () => void;
}

export function PlanBanner({ onOpenSettings }: PlanBannerProps) {
  const { data: usage } = useQuery({ queryKey: ["fleet-usage"], queryFn: fetchFleetUsage });
  if (!usage) return null;

  const remaining = usage.jobs_remaining_this_month;
  const limit = usage.jobs_limit_monthly;
  const tight = remaining != null && remaining <= 5;
  if (!tight && usage.billing_plan !== "free") return null;

  return (
    <div
      className={`px-6 py-2.5 text-sm flex flex-wrap items-center justify-between gap-2 border-b ${
        remaining === 0
          ? "bg-red-50 border-red-200 text-red-900"
          : "bg-earth-50 border-earth-200 text-earth-900"
      }`}
    >
      <p>
        <span className="font-medium">{usage.plan_label}</span>
        {limit != null && remaining != null && (
          <>
            {" "}
            · {usage.jobs_this_month}/{limit} jobs this month ({remaining} remaining)
          </>
        )}
        {remaining === 0 && " Start a paid pilot to keep optimizing."}
      </p>
      {usage.stripe_configured && usage.billing_plan === "free" && (
        <button type="button" className="text-xs font-medium underline" onClick={onOpenSettings}>
          Billing in Settings
        </button>
      )}
    </div>
  );
}
