import { LayoutDashboard, History } from "lucide-react";
import { cn } from "../../lib/utils";

interface NavItem {
  label: string;
  icon: React.ReactNode;
  active?: boolean;
}

const navItems: NavItem[] = [
  { label: "Dashboard", icon: <LayoutDashboard size={18} />, active: true },
  { label: "History", icon: <History size={18} /> },
];

export function Sidebar() {
  return (
    <aside className="w-56 flex-shrink-0 h-screen bg-forest-700 flex flex-col">
      {/* Logo */}
      <div className="px-5 py-6 border-b border-forest-600">
        <div className="flex items-center gap-3">
          <div className="bg-white rounded-md p-1 flex-shrink-0">
            <img src="/logo.png" alt="TerraIQ" className="h-7 w-auto" />
          </div>
          <span className="text-white font-semibold text-lg tracking-tight">TerraIQ</span>
        </div>
        <p className="text-forest-300 text-xs mt-1 leading-snug">
          Terrain-Aware Fuel Optimization
        </p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => (
          <button
            key={item.label}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
              item.active
                ? "bg-forest-600 text-white"
                : "text-forest-200 hover:bg-forest-600 hover:text-white"
            )}
          >
            {item.icon}
            {item.label}
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-forest-600">
        <p className="text-forest-400 text-xs">Phase 1 — Simulation</p>
      </div>
    </aside>
  );
}
