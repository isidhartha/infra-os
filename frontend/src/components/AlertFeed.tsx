import React, { useEffect, useState } from "react";
import { Bell, RefreshCw, CheckCircle } from "lucide-react";

interface Alert {
  id: string;
  name: string;
  severity: "critical" | "warning" | "info";
  message: string;
  namespace: string;
  resource: string;
  timestamp: string;
}

interface AlertsResponse {
  alerts: Alert[];
  summary: { total: number; critical: number; warning: number; info: number };
}

const SEV_STYLE = {
  critical: "border-red-500/30 bg-red-500/5 text-red-400",
  warning: "border-yellow-500/30 bg-yellow-500/5 text-yellow-400",
  info: "border-blue-500/30 bg-blue-500/5 text-blue-400",
};
const SEV_DOT = { critical: "bg-red-500", warning: "bg-yellow-500", info: "bg-blue-500" };

export default function AlertFeed() {
  const [data, setData] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/alerts");
      if (res.ok) setData(await res.json());
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchAlerts(); const t = setInterval(fetchAlerts, 15000); return () => clearInterval(t); }, []);

  const alerts = data?.alerts ?? [];
  const summary = data?.summary;

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Bell size={14} className="text-brand-green" />
          <p className="text-sm font-semibold text-white">Alert Feed</p>
          {summary && (
            <div className="flex gap-1.5 ml-2">
              {summary.critical > 0 && <span className="text-xs bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded">{summary.critical} crit</span>}
              {summary.warning > 0 && <span className="text-xs bg-yellow-500/20 text-yellow-400 px-1.5 py-0.5 rounded">{summary.warning} warn</span>}
            </div>
          )}
        </div>
        <button onClick={fetchAlerts} className="text-gray-500 hover:text-brand-green transition-colors">
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      <div className="space-y-2 max-h-80 overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="flex items-center gap-2 text-brand-green text-sm py-4 justify-center">
            <CheckCircle size={16} /> All clear — no active alerts
          </div>
        ) : (
          alerts.map((a) => (
            <div key={a.id} className={`border rounded-lg p-3 text-xs ${SEV_STYLE[a.severity] ?? SEV_STYLE.info}`}>
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-2 h-2 rounded-full ${SEV_DOT[a.severity]}`} />
                <span className="font-semibold">{a.name}</span>
                <span className="ml-auto text-gray-600">{new Date(a.timestamp).toLocaleTimeString()}</span>
              </div>
              <p className="text-gray-300">{a.message}</p>
              {a.resource && (
                <p className="text-gray-600 mt-1 font-mono">{a.namespace}/{a.resource}</p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
