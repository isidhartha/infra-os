import React from "react";
import { Server, Box, Layers, Globe } from "lucide-react";
import type { MetricsSnapshot } from "../App";

interface Props {
  metrics: MetricsSnapshot | null;
}

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
  sub?: string;
}

function StatCard({ label, value, icon: Icon, color, sub }: StatCardProps) {
  return (
    <div className="glass rounded-xl p-4 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
        <Icon size={18} className="text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-xs text-gray-400">{label}</p>
        {sub && <p className="text-xs text-gray-600 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

function UsageBar({ label, value, warn = 70, crit = 90 }: { label: string; value: number; warn?: number; crit?: number }) {
  const color = value >= crit ? "bg-red-500" : value >= warn ? "bg-yellow-500" : "bg-brand-green";
  const textColor = value >= crit ? "text-red-400" : value >= warn ? "text-yellow-400" : "text-brand-green";
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-400">{label}</span>
        <span className={textColor}>{value.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-brand-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
    </div>
  );
}

export default function ClusterOverview({ metrics }: Props) {
  const cluster = metrics?.cluster;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Nodes" value={cluster?.node_count ?? "—"} icon={Server} color="bg-brand-blue/80" />
        <StatCard label="Pods" value={cluster?.pod_count ?? "—"} icon={Box} color="bg-purple-600/80" />
        <StatCard label="Active Alerts" value={cluster?.alert_count ?? "—"} icon={Layers} color="bg-orange-600/80" />
        <StatCard label="Namespaces" value={6} icon={Globe} color="bg-teal-600/80" />
      </div>

      {cluster && (
        <div className="glass rounded-xl p-4 space-y-3">
          <p className="text-sm font-semibold text-white">Cluster Resource Usage</p>
          <UsageBar label="CPU Usage" value={cluster.cpu_usage_pct} />
          <UsageBar label="Memory Usage" value={cluster.memory_usage_pct} />
        </div>
      )}
    </div>
  );
}
