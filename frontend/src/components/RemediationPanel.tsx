import React, { useState } from "react";
import { Wrench, CheckCircle, XCircle, Loader2 } from "lucide-react";

interface RemResult {
  success: boolean;
  action: string;
  resource: string;
  message: string;
}

const QUICK_ACTIONS = [
  { label: "Restart crash-loop-demo", type: "Pod", name: "crash-loop-demo-abc", ns: "default", action: "restart_pod" },
  { label: "Scale worker to 3", type: "Deployment", name: "worker", ns: "default", action: "scale_deployment" },
  { label: "Rollback auth-service", type: "Deployment", name: "auth-service", ns: "default", action: "rollback_deployment" },
];

export default function RemediationPanel() {
  const [results, setResults] = useState<RemResult[]>([]);
  const [loading, setLoading] = useState<string | null>(null);

  const execute = async (qa: typeof QUICK_ACTIONS[0]) => {
    setLoading(qa.label);
    try {
      const res = await fetch("/api/v1/remediate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resource_type: qa.type,
          resource_name: qa.name,
          namespace: qa.ns,
          action: qa.action,
          reason: qa.action === "scale_deployment" ? "3" : "",
        }),
      });
      if (res.ok) {
        const data: RemResult = await res.json();
        setResults((prev) => [data, ...prev].slice(0, 5));
      }
    } finally { setLoading(null); }
  };

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Wrench size={14} className="text-brand-blue" />
        <p className="text-sm font-semibold text-white">Remediation</p>
      </div>

      <div className="space-y-2 mb-4">
        {QUICK_ACTIONS.map((qa) => (
          <button
            key={qa.label}
            onClick={() => execute(qa)}
            disabled={!!loading}
            className="w-full text-left text-xs bg-brand-muted/40 hover:bg-brand-muted/70 border border-brand-border
              rounded-lg px-3 py-2.5 text-gray-300 transition-all flex items-center justify-between disabled:opacity-50"
          >
            <span>{qa.label}</span>
            {loading === qa.label ? (
              <Loader2 size={12} className="animate-spin text-brand-blue" />
            ) : (
              <span className="text-gray-600">{qa.action}</span>
            )}
          </button>
        ))}
      </div>

      {results.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-500">Recent Actions</p>
          {results.map((r, i) => (
            <div key={i} className={`flex items-start gap-2 text-xs rounded-lg px-3 py-2 border
              ${r.success ? "border-brand-green/30 bg-brand-green/5" : "border-red-500/30 bg-red-500/5"}`}>
              {r.success
                ? <CheckCircle size={12} className="text-brand-green mt-0.5 flex-shrink-0" />
                : <XCircle size={12} className="text-red-400 mt-0.5 flex-shrink-0" />}
              <span className={r.success ? "text-gray-300" : "text-red-300"}>{r.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
