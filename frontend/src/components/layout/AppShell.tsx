import { Suspense, lazy, useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { ForgotPassword } from "../../pages/ForgotPassword";
import { Login } from "../../pages/Login";
import { Register } from "../../pages/Register";
import { ResetPassword } from "../../pages/ResetPassword";
import { Sidebar } from "./Sidebar";

// Heavy pages are lazy-loaded so their JS chunks are fetched only on first visit.
// Auth pages are kept eager since they're shown before any navigation occurs.
const Dashboard = lazy(() => import("../../pages/Dashboard").then((m) => ({ default: m.Dashboard })));
const History   = lazy(() => import("../../pages/History").then((m) => ({ default: m.History })));
const Analytics = lazy(() => import("../../pages/Analytics").then((m) => ({ default: m.Analytics })));
const ApiKeys   = lazy(() => import("../../pages/ApiKeys").then((m) => ({ default: m.ApiKeys })));

type AuthScreen = "login" | "register" | "forgot";

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
      <Sidebar page={page} onNavigate={setPage} />
      <main className="flex-1 overflow-auto">
        <Suspense fallback={<PageFallback />}>
          {page === "dashboard" && <Dashboard />}
          {page === "history"   && <History />}
          {page === "analytics" && <Analytics />}
          {page === "api-keys"  && <ApiKeys />}
        </Suspense>
      </main>
    </div>
  );
}
