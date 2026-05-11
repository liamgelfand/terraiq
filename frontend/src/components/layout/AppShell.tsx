import { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import { Analytics } from "../../pages/Analytics";
import { ApiKeys } from "../../pages/ApiKeys";
import { Dashboard } from "../../pages/Dashboard";
import { History } from "../../pages/History";
import { Login } from "../../pages/Login";
import { Register } from "../../pages/Register";
import { Sidebar } from "./Sidebar";

export function AppShell() {
  const { user, isLoading } = useAuth();
  const [page, setPage] = useState("dashboard");
  const [authPage, setAuthPage] = useState<"login" | "register">("login");

  if (isLoading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <div className="text-stone-400 text-sm">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return authPage === "login" ? (
      <Login onGoRegister={() => setAuthPage("register")} />
    ) : (
      <Register onGoLogin={() => setAuthPage("login")} />
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-stone-50">
      <Sidebar page={page} onNavigate={setPage} />
      <main className="flex-1 overflow-auto">
        {page === "dashboard" && <Dashboard />}
        {page === "analytics" && <Analytics />}
        {page === "history" && <History />}
        {page === "api-keys" && <ApiKeys />}
      </main>
    </div>
  );
}
