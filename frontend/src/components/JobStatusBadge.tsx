import { Loader2, CheckCircle, XCircle, Clock } from "lucide-react";
import type { JobStatus } from "../api/client";
import { cn } from "../lib/utils";

const CONFIG: Record<JobStatus, { label: string; icon: React.ReactNode; className: string }> = {
  pending: {
    label: "Queued",
    icon: <Clock size={14} />,
    className: "bg-stone-100 text-stone-600",
  },
  running: {
    label: "Running",
    icon: <Loader2 size={14} className="animate-spin" />,
    className: "bg-earth-50 text-earth-600 border border-earth-200",
  },
  completed: {
    label: "Completed",
    icon: <CheckCircle size={14} />,
    className: "bg-forest-50 text-forest-700 border border-forest-200",
  },
  failed: {
    label: "Failed",
    icon: <XCircle size={14} />,
    className: "bg-red-50 text-red-600 border border-red-200",
  },
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  const { label, icon, className } = CONFIG[status];
  return (
    <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium", className)}>
      {icon}
      {label}
    </span>
  );
}
