import React from "react";
import { LayoutDashboard, AlertTriangle, Settings, Cpu, Wifi, WifiOff } from "lucide-react";
import type { Page } from "../App";

interface Props {
  currentPage: Page;
  onNavigate: (p: Page) => void;
  wsConnected: boolean;
}

const NAV = [
  { id: "dashboard" as Page, label: "Dashboard", icon: LayoutDashboard },
  { id: "incidents" as Page, label: "Incidents", icon: AlertTriangle },
];

export default function Sidebar({ currentPage, onNavigate, wsConnected }: Props) {
  return (
    <aside className="w-60 flex-shrink-0 bg-brand-surface border-r border-brand-border flex flex-col">
      {/* Logo */}
      <div className="p-5 border-b border-brand-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-green to-brand-blue flex items-center justify-center">
            <Cpu size={16} className="text-gray-900" />
          </div>
          <div>
            <p className="font-bold text-sm text-white leading-none">InfraOS AI</p>
            <p className="text-xs text-gray-500 mt-0.5">DevOps Platform</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 mb-2">Platform</p>
        {NAV.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => onNavigate(id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all mb-1
              ${currentPage === id
                ? "bg-brand-green/10 text-brand-green border border-brand-green/20"
                : "text-gray-400 hover:text-white hover:bg-brand-muted/40"
              }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </nav>

      {/* Connection status */}
      <div className="p-4 border-t border-brand-border">
        <div className={`flex items-center gap-2 text-xs px-3 py-2 rounded-lg
          ${wsConnected ? "bg-brand-green/10 text-brand-green" : "bg-red-500/10 text-red-400"}`}>
          {wsConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
          {wsConnected ? "Live stream active" : "Reconnecting..."}
        </div>
        <p className="text-xs text-gray-600 mt-3 px-1">
          InfraOS AI v1.0.0<br />
          <span className="text-brand-green/60">Mock Mode Enabled</span>
        </p>
      </div>
    </aside>
  );
}
