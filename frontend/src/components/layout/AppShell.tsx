import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { Analytics } from "../../pages/Analytics";
import { ApiKeys } from "../../pages/ApiKeys";
import { Dashboard } from "../../pages/Dashboard";
import { ForgotPassword } from "../../pages/ForgotPassword";
import { History } from "../../pages/History";
import { Login } from "../../pages/Login";
import { Register } from "../../pages/Register";
import { ResetPassword } from "../../pages/ResetPassword";
import { Sidebar } from "./Sidebar";

type AuthScreen = "login" | "register" | "forgot" ;

function getResetToken(): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get("reset_token");
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

  // Password reset link takes priority over everything
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
        {page === "dashboard" && <Dashboard />}
        {page === "history" && <History />}
        {page === "analytics" && <Analytics />}
        {page === "api-keys" && <ApiKeys />}
      </main>
    </div>
  );
}
