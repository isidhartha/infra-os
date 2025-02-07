import React, { useState } from "react";
import { Search, Loader2, Terminal } from "lucide-react";
import type { MetricsSnapshot } from "../App";
import ClusterOverview from "../components/ClusterOverview";
import PodGrid from "../components/PodGrid";
import MetricsChart from "../components/MetricsChart";
import AlertFeed from "../components/AlertFeed";
import AIAnalysis from "../components/AIAnalysis";
import RemediationPanel from "../components/RemediationPanel";

interface Props {
  metrics: MetricsSnapshot | null;
}

interface NLResponse {
  query: string;
  kubectl_command: string;
  explanation: string;
  result: string;
  suggestions: string[];
}

function NLQueryBox() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<NLResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResponse(null);
    try {
      const res = await fetch("/api/v1/k8s/nl-query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, namespace: "default" }),
      });
      if (res.ok) setResponse(await res.json());
    } finally { setLoading(false); }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") submit();
  };

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Terminal size={14} className="text-brand-green" />
        <p className="text-sm font-semibold text-white">Natural Language Query</p>
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKey}
          placeholder='Ask anything... "why is my pod crashing?" or "show node status"'
          className="flex-1 text-sm bg-brand-muted/60 border border-brand-border rounded-lg px-3 py-2
            text-gray-200 placeholder-gray-600 outline-none focus:border-brand-green/50 transition-colors"
        />
        <button
          onClick={submit}
          disabled={loading || !query.trim()}
          className="flex items-center gap-1.5 bg-brand-green text-gray-900 text-sm font-semibold
            px-4 py-2 rounded-lg hover:bg-brand-green/90 transition-all disabled:opacity-50"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
          Ask
        </button>
      </div>

      {response && (
        <div className="mt-3 space-y-2 animate-fade-in">
          <div className="bg-brand-muted/40 rounded-lg p-3 font-mono text-xs">
            <p className="text-brand-green mb-1">$ {response.kubectl_command}</p>
            <p className="text-gray-300 font-sans text-xs">{response.explanation}</p>
          </div>
          {response.result && (
            <pre className="bg-gray-900/60 border border-brand-border rounded-lg p-3 text-xs text-gray-400 overflow-x-auto whitespace-pre-wrap">
              {response.result}
            </pre>
          )}
          {response.suggestions?.length > 0 && (
            <div className="text-xs text-gray-500">
              <p className="mb-1">Suggestions:</p>
              {response.suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => setQuery(s)}
                  className="text-brand-blue/70 hover:text-brand-blue block"
                >
                  → {s}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Dashboard({ metrics }: Props) {
  return (
    <div className="p-6 space-y-5 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">InfraOS AI Dashboard</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            AI DevOps Infrastructure Platform
            {metrics && (
              <span className="ml-2 text-brand-green/60">
                — Live at {new Date(metrics.timestamp * 1000).toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          {metrics && (
            <>
              <span className="bg-brand-muted/60 border border-brand-border rounded px-2 py-1 text-gray-400">
                {metrics.request_rate.toFixed(0)} req/s
              </span>
              <span className={`rounded px-2 py-1 border ${
                metrics.error_rate_pct > 5
                  ? "border-red-500/40 bg-red-500/10 text-red-400"
                  : "border-brand-green/30 bg-brand-green/10 text-brand-green"
              }`}>
                {metrics.error_rate_pct.toFixed(2)}% errors
              </span>
            </>
          )}
        </div>
      </div>

      {/* Cluster overview row */}
      <ClusterOverview metrics={metrics} />

      {/* Charts + Alerts */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        <div className="xl:col-span-2">
          <MetricsChart metrics={metrics} />
        </div>
        <AlertFeed />
      </div>

      {/* Pod grid */}
      <PodGrid />

      {/* NL Query */}
      <NLQueryBox />

      {/* AI Analysis + Remediation */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <AIAnalysis />
        <RemediationPanel />
      </div>
    </div>
  );
}
