import { useState } from "react";
import { Sidebar } from "./Sidebar";
import { Dashboard } from "../../pages/Dashboard";
import { ApiKeys } from "../../pages/ApiKeys";

export function AppShell() {
  const [page, setPage] = useState("dashboard");

  return (
    <div className="flex h-screen overflow-hidden bg-stone-50">
      <Sidebar page={page} onNavigate={setPage} />
      <main className="flex-1 overflow-auto">
        {page === "dashboard" && <Dashboard />}
        {page === "api-keys" && <ApiKeys />}
        {page === "history" && (
          <div className="p-8 text-stone-400 text-sm">History coming soon.</div>
        )}
      </main>
    </div>
  );
}
