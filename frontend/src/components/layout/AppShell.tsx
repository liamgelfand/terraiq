import { Suspense, lazy, useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { ForgotPassword } from "../../pages/ForgotPassword";
import { Login } from "../../pages/Login";
import { Register } from "../../pages/Register";
import { ResetPassword } from "../../pages/ResetPassword";
import { AcceptInvite } from "../../pages/AcceptInvite";
import { Sidebar } from "./Sidebar";

// Heavy pages are lazy-loaded so their JS chunks are fetched only on first visit.
// Auth pages are kept eager since they're shown before any navigation occurs.
const Dashboard = lazy(() => import("../../pages/Dashboard").then((m) => ({ default: m.Dashboard })));
const CorridorsPage = lazy(() => import("../../pages/CorridorsPage").then((m) => ({ default: m.CorridorsPage })));
const PilotBatchesPage = lazy(() => import("../../pages/PilotBatchesPage").then((m) => ({ default: m.PilotBatchesPage })));
const TelemetryPage = lazy(() => import("../../pages/TelemetryPage").then((m) => ({ default: m.TelemetryPage })));
const OpsBoardPage = lazy(() => import("../../pages/OpsBoardPage").then((m) => ({ default: m.OpsBoardPage })));
const History   = lazy(() => import("../../pages/History").then((m) => ({ default: m.History })));
const Analytics = lazy(() => import("../../pages/Analytics").then((m) => ({ default: m.Analytics })));
const ApiKeys   = lazy(() => import("../../pages/ApiKeys").then((m) => ({ default: m.ApiKeys })));
const SettingsPage = lazy(() => import("../../pages/Settings").then((m) => ({ default: m.Settings })));
const AuditLog = lazy(() => import("../../pages/AuditLog").then((m) => ({ default: m.AuditLog })));
const WebhookDeliveries = lazy(() =>
  import("../../pages/WebhookDeliveries").then((m) => ({ default: m.WebhookDeliveries }))
);

type AuthScreen = "login" | "register" | "forgot";

function getInviteToken(): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get("invite_token");
}

function getResetToken(): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get("reset_token");
}

function PageFallback() {
  return (
    <div className="flex-1 flex items-center justify-center min-h-[60vh]">
      <div className="text-stone-400 text-sm">Loading…</div>
    </div>
  );
}

export function AppShell() {
  const { user, isLoading } = useAuth();
  const [page, setPage] = useState("dashboard");
  const [authScreen, setAuthScreen] = useState<AuthScreen>("login");

  const resetToken = getResetToken();
  const inviteToken = getInviteToken();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <div className="text-stone-400 text-sm">Loading...</div>
      </div>
    );
  }

  if (resetToken) {
    return (
      <ResetPassword
        token={resetToken}
        onGoLogin={() => setAuthScreen("login")}
      />
    );
  }

  if (inviteToken && !user) {
    return <AcceptInvite token={inviteToken} />;
  }

  if (!user) {
    if (authScreen === "register") {
      return <Register onGoLogin={() => setAuthScreen("login")} />;
    }
    if (authScreen === "forgot") {
      return <ForgotPassword onGoLogin={() => setAuthScreen("login")} />;
    }
    return (
      <Login
        onGoRegister={() => setAuthScreen("register")}
        onForgotPassword={() => setAuthScreen("forgot")}
      />
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-stone-50">
      <Sidebar page={page} onNavigate={setPage} isAdmin={user.role === "admin"} />
      <main className="flex-1 overflow-auto">
        <Suspense fallback={<PageFallback />}>
          {page === "dashboard" && <Dashboard />}
          {page === "corridors" && <CorridorsPage />}
          {page === "batches" && <PilotBatchesPage />}
          {page === "telemetry" && <TelemetryPage />}
          {page === "ops" && <OpsBoardPage />}
          {page === "history"   && <History />}
          {page === "analytics" && <Analytics />}
          {page === "api-keys"  && <ApiKeys />}
          {page === "settings" && <SettingsPage />}
          {page === "audit" && <AuditLog />}
          {page === "webhooks" && <WebhookDeliveries />}
        </Suspense>
      </main>
    </div>
  );
}
