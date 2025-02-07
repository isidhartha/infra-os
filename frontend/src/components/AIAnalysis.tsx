import React, { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";

interface AnalysisResult {
  cluster_status: string;
  failing_pods: number;
  high_restart_pods: number;
  failing_pod_names: string[];
  recommendations: string[];
  mock_mode: boolean;
}

export default function AIAnalysis() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);

  const runAnalysis = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/k8s/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ focus: "general" }),
      });
      if (res.ok) setResult(await res.json());
    } finally { setLoading(false); }
  };

  const statusColor = (s: string) =>
    s === "healthy" ? "text-brand-green" : s === "degraded" ? "text-yellow-400" : "text-red-400";

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sparkles size={14} className="text-brand-green" />
          <p className="text-sm font-semibold text-white">AI Cluster Analysis</p>
        </div>
        <button
          onClick={runAnalysis}
          disabled={loading}
          className="flex items-center gap-1.5 text-xs bg-brand-green/10 border border-brand-green/30 text-brand-green
            px-3 py-1.5 rounded-lg hover:bg-brand-green/20 transition-all disabled:opacity-50"
        >
          {loading ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
          Analyze
        </button>
      </div>

      {!result && !loading && (
        <p className="text-gray-500 text-sm text-center py-6">Click Analyze to inspect cluster health</p>
      )}

      {loading && (
        <div className="flex items-center justify-center gap-3 py-6 text-gray-400 text-sm">
          <Loader2 size={18} className="animate-spin text-brand-green" />
          Running AI analysis...
        </div>
      )}

      {result && !loading && (
        <div className="space-y-3 animate-fade-in">
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="bg-brand-muted/40 rounded-lg p-2">
              <p className={`text-lg font-bold ${statusColor(result.cluster_status)}`}>
                {result.cluster_status.toUpperCase()}
              </p>
              <p className="text-xs text-gray-500">Cluster</p>
            </div>
            <div className="bg-brand-muted/40 rounded-lg p-2">
              <p className={`text-lg font-bold ${result.failing_pods > 0 ? "text-red-400" : "text-brand-green"}`}>
                {result.failing_pods}
              </p>
              <p className="text-xs text-gray-500">Failing Pods</p>
            </div>
            <div className="bg-brand-muted/40 rounded-lg p-2">
              <p className={`text-lg font-bold ${result.high_restart_pods > 0 ? "text-yellow-400" : "text-brand-green"}`}>
                {result.high_restart_pods}
              </p>
              <p className="text-xs text-gray-500">High Restarts</p>
            </div>
          </div>

          <div>
            <p className="text-xs text-gray-500 mb-2">Recommendations</p>
            <ul className="space-y-1.5">
              {result.recommendations.map((rec, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-300">
                  <span className="text-brand-green mt-0.5">→</span>
                  {rec}
                </li>
              ))}
            </ul>
          </div>

          {result.mock_mode && (
            <p className="text-xs text-brand-green/50 border border-brand-green/20 rounded px-2 py-1">
              Mock Mode — connect a real cluster for live analysis
            </p>
          )}
        </div>
      )}
    </div>
  );
}
