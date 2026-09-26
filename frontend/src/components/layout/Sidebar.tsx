import { BarChart3, ClipboardList, History, KeyRound, LayoutDashboard, LogOut, MapPin, Radar, Route, ScrollText, Settings, Webhook } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { cn } from "../../lib/utils";

interface NavItem {
  label: string;
  icon: React.ReactNode;
  page: string;
}

interface SidebarProps {
  page: string;
  onNavigate: (page: string) => void;
  isAdmin?: boolean;
  isFounder?: boolean;
}

const baseNav: NavItem[] = [
  { label: "Dashboard", icon: <LayoutDashboard size={18} />, page: "dashboard" },
  { label: "Corridors", icon: <Route size={18} />, page: "corridors" },
  { label: "Batch runs", icon: <ClipboardList size={18} />, page: "batches" },
  { label: "Telemetry", icon: <Radar size={18} />, page: "telemetry" },
  { label: "Ops board", icon: <MapPin size={18} />, page: "ops" },
  { label: "History", icon: <History size={18} />, page: "history" },
  { label: "Analytics", icon: <BarChart3 size={18} />, page: "analytics" },
  { label: "API Keys", icon: <KeyRound size={18} />, page: "api-keys" },
  { label: "Settings", icon: <Settings size={18} />, page: "settings" },
];

const adminNav: NavItem[] = [
  { label: "Audit log", icon: <ScrollText size={18} />, page: "audit" },
  { label: "Webhook log", icon: <Webhook size={18} />, page: "webhooks" },
];

const founderNav: NavItem[] = [{ label: "Leads", icon: <ClipboardList size={18} />, page: "leads" }];

export function Sidebar({ page, onNavigate, isAdmin = false, isFounder = false }: SidebarProps) {
  const { user, logout } = useAuth();
  const navItems = [
    ...baseNav,
    ...(isAdmin ? adminNav : []),
    ...(isFounder ? founderNav : []),
  ];

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
            onClick={() => onNavigate(item.page)}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
              page === item.page
                ? "bg-forest-600 text-white"
                : "text-forest-200 hover:bg-forest-600 hover:text-white"
            )}
          >
            {item.icon}
            {item.label}
          </button>
        ))}
      </nav>

      {/* User footer */}
      <div className="px-4 py-4 border-t border-forest-600 space-y-2">
        {user && (
          <div className="px-1">
            <p className="text-white text-xs font-medium truncate">{user.full_name}</p>
            <p className="text-forest-400 text-xs truncate">{user.fleet_name}</p>
          </div>
        )}
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-md text-xs text-forest-300 hover:bg-forest-600 hover:text-white transition-colors"
        >
          <LogOut size={14} />
          Sign out
        </button>
      </div>
    </aside>
  );
}
