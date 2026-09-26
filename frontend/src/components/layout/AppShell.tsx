import { Suspense, lazy, useEffect, useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { updateOnboarding } from "../../api/client";
import { OnboardingChecklist } from "../OnboardingChecklist";
import { PlanBanner } from "../PlanBanner";
import { ForgotPassword } from "../../pages/ForgotPassword";
import { Landing } from "../../pages/Landing";
import { LegalPage } from "../../pages/LegalPage";
import { Login } from "../../pages/Login";
import { Register } from "../../pages/Register";
import { ResetPassword } from "../../pages/ResetPassword";
import { AcceptInvite } from "../../pages/AcceptInvite";
import { Sidebar } from "./Sidebar";

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
const DriverBriefPage = lazy(() =>
  import("../../pages/DriverBriefPage").then((m) => ({ default: m.DriverBriefPage }))
);
const LeadsPage = lazy(() => import("../../pages/LeadsPage").then((m) => ({ default: m.LeadsPage })));

type AuthScreen = "landing" | "login" | "register" | "forgot";
type LegalSlug = "terms" | "privacy" | "pilot";

function getInviteToken(): string | null {
  return new URLSearchParams(window.location.search).get("invite_token");
}

function getResetToken(): string | null {
  return new URLSearchParams(window.location.search).get("reset_token");
}

function readAuthScreen(): AuthScreen {
  const auth = new URLSearchParams(window.location.search).get("auth");
  if (auth === "login" || auth === "register" || auth === "forgot") return auth;
  return "landing";
}

function readLegal(): LegalSlug | null {
  const legal = new URLSearchParams(window.location.search).get("legal");
  if (legal === "terms" || legal === "privacy" || legal === "pilot") return legal;
  return null;
}

function readBriefJobId(): string | null {
  const params = new URLSearchParams(window.location.search);
  if (params.get("page") === "brief") return params.get("job");
  return null;
}

function pushQuery(next: URLSearchParams) {
  const qs = next.toString();
  window.history.pushState({}, "", qs ? `/?${qs}` : "/");
}

function PageFallback() {
  return (
    <div className="flex-1 flex items-center justify-center min-h-[60vh]">
      <div className="text-stone-400 text-sm">Loading…</div>
    </div>
  );
}

export function AppShell() {
  const { user, isLoading, refreshUser } = useAuth();
  const [page, setPage] = useState("dashboard");
  const [authScreen, setAuthScreen] = useState<AuthScreen>(readAuthScreen);
  const [legal, setLegal] = useState<LegalSlug | null>(readLegal);
  const [briefJobId, setBriefJobId] = useState<string | null>(readBriefJobId);

  useEffect(() => {
    const onPop = () => {
      setAuthScreen(readAuthScreen());
      setLegal(readLegal());
      setBriefJobId(readBriefJobId());
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  function goPublic(screen: AuthScreen, legalSlug: LegalSlug | null = null) {
    const params = new URLSearchParams();
    if (legalSlug) params.set("legal", legalSlug);
    else if (screen !== "landing") params.set("auth", screen);
    pushQuery(params);
    setLegal(legalSlug);
    setAuthScreen(screen);
  }

  function openBrief(jobId: string) {
    const params = new URLSearchParams();
    params.set("page", "brief");
    params.set("job", jobId);
    pushQuery(params);
    setBriefJobId(jobId);
  }

  function closeBrief() {
    pushQuery(new URLSearchParams());
    setBriefJobId(null);
    setPage("ops");
  }

  function navigateApp(next: string) {
    setBriefJobId(null);
    setPage(next);
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <div className="text-stone-400 text-sm">Loading...</div>
      </div>
    );
  }

  const resetToken = getResetToken();
  const inviteToken = getInviteToken();

  if (resetToken) {
    return (
      <ResetPassword
        token={resetToken}
        onGoLogin={() => goPublic("login")}
      />
    );
  }

  if (inviteToken && !user) {
    return <AcceptInvite token={inviteToken} />;
  }

  if (!user) {
    if (legal) {
      return (
        <LegalPage
          slug={legal}
          onHome={() => goPublic("landing")}
          onSignIn={() => goPublic("login")}
        />
      );
    }
    if (authScreen === "register") {
      return (
        <Register
          onGoLogin={() => goPublic("login")}
          onGoHome={() => goPublic("landing")}
          onGoLegal={(slug) => goPublic("landing", slug)}
        />
      );
    }
    if (authScreen === "forgot") {
      return <ForgotPassword onGoLogin={() => goPublic("login")} />;
    }
    if (authScreen === "login") {
      return (
        <Login
          onGoRegister={() => goPublic("register")}
          onForgotPassword={() => goPublic("forgot")}
          onGoHome={() => goPublic("landing")}
        />
      );
    }
    return (
      <Landing
        onSignIn={() => goPublic("login")}
        onRegister={() => goPublic("register")}
        onLegal={(slug) => goPublic("landing", slug)}
      />
    );
  }

  if (briefJobId) {
    return (
      <Suspense fallback={<PageFallback />}>
        <DriverBriefPage jobId={briefJobId} onBack={closeBrief} />
      </Suspense>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-stone-50">
      <Sidebar
        page={page}
        onNavigate={navigateApp}
        isAdmin={user.role === "admin"}
        isFounder={!!user.is_founder}
      />
      <main className="flex-1 overflow-auto flex flex-col">
        <OnboardingChecklist
          onGoCorridors={() => navigateApp("corridors")}
          onGoOps={() => navigateApp("ops")}
          onGoTelemetry={() => navigateApp("telemetry")}
          onDismiss={() => {
            void updateOnboarding(true).then(() => refreshUser());
          }}
        />
        <PlanBanner onOpenSettings={() => navigateApp("settings")} />
        <div className="flex-1 overflow-auto">
          <Suspense fallback={<PageFallback />}>
            {page === "dashboard" && <Dashboard />}
            {page === "corridors" && <CorridorsPage />}
            {page === "batches" && <PilotBatchesPage />}
            {page === "telemetry" && <TelemetryPage />}
            {page === "ops" && <OpsBoardPage onOpenBrief={openBrief} />}
            {page === "history"   && <History onOpenBrief={openBrief} />}
            {page === "analytics" && <Analytics />}
            {page === "api-keys"  && <ApiKeys />}
            {page === "settings" && <SettingsPage />}
            {page === "audit" && <AuditLog />}
            {page === "webhooks" && <WebhookDeliveries />}
            {page === "leads" && user.is_founder && <LeadsPage />}
          </Suspense>
        </div>
      </main>
    </div>
  );
}
