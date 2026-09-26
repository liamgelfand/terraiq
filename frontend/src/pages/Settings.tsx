import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useAuth } from "../contexts/AuthContext";
import { changePassword, createFleetInvite, downloadPilotPackageCsv, fetchFleetDataExport, fetchFleetUsage, purgeFleetData, startBillingCheckout, startBillingPortal, updateFleetName, updateProfile } from "../api/client";
import { extractApiError } from "../lib/errors";

export function Settings() {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState("");
  const [fleetName, setFleetName] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name);
      setFleetName(user.fleet_name);
    }
  }, [user]);

  const profileMut = useMutation({
    mutationFn: () => updateProfile(fullName.trim()),
    onSuccess: async () => {
      setError(null);
      setMessage("Profile updated.");
      await refreshUser();
    },
    onError: (e: unknown) => {
      setMessage(null);
      setError(extractApiError(e));
    },
  });

  const fleetMut = useMutation({
    mutationFn: () => updateFleetName(fleetName.trim()),
    onSuccess: async () => {
      setError(null);
      setMessage("Fleet name updated.");
      await refreshUser();
    },
    onError: (e: unknown) => {
      setMessage(null);
      setError(extractApiError(e));
    },
  });

  const [inviteEmail, setInviteEmail] = useState("");
  const isAdmin = user?.role === "admin";

  const passMut = useMutation({
    mutationFn: () => changePassword(currentPassword, newPassword),
    onSuccess: () => {
      setError(null);
      setMessage("Password updated.");
      setCurrentPassword("");
      setNewPassword("");
    },
    onError: (e: unknown) => {
      setMessage(null);
      setError(extractApiError(e));
    },
  });

  const inviteMut = useMutation({
    mutationFn: () => createFleetInvite(inviteEmail.trim()),
    onSuccess: () => {
      setError(null);
      setMessage("Invitation sent. The recipient will receive an email when outbound mail is configured.");
      setInviteEmail("");
    },
    onError: (e: unknown) => {
      setMessage(null);
      setError(extractApiError(e));
    },
  });

  const exportJsonMut = useMutation({
    mutationFn: async () => {
      const data = await fetchFleetDataExport();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `terraiq-fleet-export-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    },
    onError: (e: unknown) => {
      setMessage(null);
      setError(extractApiError(e));
    },
  });

  const purgeMut = useMutation({
    mutationFn: (includeJobs: boolean) => purgeFleetData(includeJobs),
    onSuccess: () => {
      setError(null);
      setMessage("Pilot data purged. Jobs were kept unless you chose full delete.");
    },
    onError: (e: unknown) => {
      setMessage(null);
      setError(extractApiError(e));
    },
  });

  const billingMut = useMutation({
    mutationFn: () => startBillingCheckout(),
    onSuccess: (data) => {
      if (data.url) window.location.href = data.url;
    },
    onError: (e: unknown) => {
      setMessage(null);
      setError(extractApiError(e));
    },
  });

  const portalMut = useMutation({
    mutationFn: () => startBillingPortal(),
    onSuccess: (data) => {
      if (data.url) window.location.href = data.url;
    },
    onError: (e: unknown) => {
      setMessage(null);
      setError(extractApiError(e));
    },
  });

  const { data: usage } = useQuery({ queryKey: ["fleet-usage"], queryFn: fetchFleetUsage });

  if (!user) {
    return null;
  }

  return (
    <div className="p-6 max-w-2xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-stone-800">Account &amp; fleet</h2>
        <p className="text-sm text-stone-500 mt-0.5">
          Update your profile, fleet display name, or password.
        </p>
      </div>

      {(message || error) && (
        <div
          className={
            error
              ? "rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
              : "rounded-lg border border-forest-200 bg-forest-50 px-4 py-3 text-sm text-forest-900"
          }
        >
          {error ?? message}
        </div>
      )}

      <div className="card p-5 space-y-4">
        <h3 className="text-sm font-semibold text-stone-800">Profile</h3>
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (!fullName.trim()) return;
            profileMut.mutate();
          }}
        >
          <div>
            <label className="label" htmlFor="full_name">
              Full name
            </label>
            <input
              id="full_name"
              className="input"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoComplete="name"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              className="btn-primary"
              disabled={profileMut.isPending || !fullName.trim()}
            >
              {profileMut.isPending ? "Saving…" : "Save profile"}
            </button>
          </div>
        </form>
      </div>

      {!isAdmin ? (
        <div className="card p-5 space-y-2">
          <h3 className="text-sm font-semibold text-stone-800">Fleet</h3>
          <p className="text-sm text-stone-600">
            You are signed in to <strong>{user.fleet_name}</strong>. Only fleet administrators can change the fleet name.
          </p>
        </div>
      ) : (
        <div className="card p-5 space-y-4">
          <h3 className="text-sm font-semibold text-stone-800">Fleet</h3>
          <form
            className="space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              if (!fleetName.trim()) return;
              fleetMut.mutate();
            }}
          >
            <div>
              <label className="label" htmlFor="fleet_name">
                Fleet name
              </label>
              <input
                id="fleet_name"
                className="input"
                value={fleetName}
                onChange={(e) => setFleetName(e.target.value)}
              />
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                className="btn-primary"
                disabled={fleetMut.isPending || !fleetName.trim()}
              >
                {fleetMut.isPending ? "Saving…" : "Save fleet name"}
              </button>
            </div>
          </form>
        </div>
      )}

      {isAdmin && (
        <div className="card p-5 space-y-4">
          <h3 className="text-sm font-semibold text-stone-800">Invite teammate</h3>
          <p className="text-xs text-stone-500">
            Sends an email with a signup link (requires transactional email in server configuration).
          </p>
          <form
            className="flex flex-col sm:flex-row gap-3 sm:items-end"
            onSubmit={(e) => {
              e.preventDefault();
              if (!inviteEmail.trim()) return;
              inviteMut.mutate();
            }}
          >
            <div className="flex-1">
              <label className="label" htmlFor="invite_email">
                Email
              </label>
              <input
                id="invite_email"
                type="email"
                className="input"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="driver@company.com"
              />
            </div>
            <button type="submit" className="btn-primary sm:mb-0" disabled={inviteMut.isPending || !inviteEmail.trim()}>
              {inviteMut.isPending ? "Sending…" : "Send invite"}
            </button>
          </form>
        </div>
      )}

      {isAdmin && (
        <div className="card p-5 space-y-4">
          <h3 className="text-sm font-semibold text-stone-800">Pilot data &amp; billing</h3>
          {usage && (
            <p className="text-sm text-stone-700">
              Plan: <span className="font-medium">{usage.plan_label}</span>
              {usage.jobs_limit_monthly != null && usage.jobs_remaining_this_month != null && (
                <> · {usage.jobs_this_month}/{usage.jobs_limit_monthly} jobs this month</>
              )}
              {usage.corridors_limit != null && (
                <> · {usage.corridors_count}/{usage.corridors_limit} corridors</>
              )}
            </p>
          )}
          <p className="text-xs text-stone-500">
            Export JSON metadata (no raw GPS points). Purge removes corridors, batches, and telemetry;
            optionally all jobs. Stripe checkout requires server env configuration.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="btn-primary"
              disabled={exportJsonMut.isPending}
              onClick={() => exportJsonMut.mutate()}
            >
              {exportJsonMut.isPending ? "Preparing…" : "Download fleet JSON"}
            </button>
            <button
              type="button"
              className="px-3 py-2 text-sm border border-stone-300 rounded-md hover:bg-stone-50"
              onClick={() => void downloadPilotPackageCsv()}
            >
              Pilot CSV bundle
            </button>
            <button
              type="button"
              className="px-3 py-2 text-sm border border-stone-300 rounded-md hover:bg-stone-50"
              disabled={billingMut.isPending}
              onClick={() => billingMut.mutate()}
            >
              {billingMut.isPending ? "Redirecting…" : "Stripe checkout"}
            </button>
            <button
              type="button"
              className="px-3 py-2 text-sm border border-stone-300 rounded-md hover:bg-stone-50"
              disabled={portalMut.isPending}
              onClick={() => portalMut.mutate()}
            >
              {portalMut.isPending ? "Opening…" : "Manage subscription"}
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="text-xs px-3 py-2 border border-red-200 text-red-700 rounded-md hover:bg-red-50"
              disabled={purgeMut.isPending}
              onClick={() => {
                if (window.confirm("Delete corridors, batches, and telemetry for this fleet? Jobs are kept.")) {
                  purgeMut.mutate(false);
                }
              }}
            >
              Purge pilot tables
            </button>
            <button
              type="button"
              className="text-xs px-3 py-2 border border-red-300 text-red-800 rounded-md hover:bg-red-50"
              disabled={purgeMut.isPending}
              onClick={() => {
                if (
                  window.confirm(
                    "Danger: also delete ALL jobs and webhook logs for this fleet. Confirm in next step.",
                  ) &&
                  window.prompt('Type "OK" to confirm full purge') === "OK"
                ) {
                  purgeMut.mutate(true);
                }
              }}
            >
              Full purge (+ jobs)
            </button>
          </div>
        </div>
      )}

      <div className="card p-5 space-y-4">
        <h3 className="text-sm font-semibold text-stone-800">Change password</h3>
        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (newPassword.length < 8) {
              setError("New password must be at least 8 characters.");
              setMessage(null);
              return;
            }
            passMut.mutate();
          }}
        >
          <div>
            <label className="label" htmlFor="current_password">
              Current password
            </label>
            <input
              id="current_password"
              type="password"
              className="input"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          <div>
            <label className="label" htmlFor="new_password">
              New password
            </label>
            <input
              id="new_password"
              type="password"
              className="input"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              minLength={8}
              autoComplete="new-password"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              className="btn-primary"
              disabled={passMut.isPending || !currentPassword || !newPassword}
            >
              {passMut.isPending ? "Updating…" : "Update password"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
