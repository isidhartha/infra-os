import React, { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

interface Pod {
  name: string;
  namespace: string;
  phase: string;
  ready: boolean;
  restarts: number;
  node: string;
  cpu_usage: string;
  memory_usage: string;
}

function PodBadge({ pod }: { pod: Pod }) {
  const dot =
    pod.phase === "Running" && pod.ready ? "healthy"
    : pod.phase === "Running" ? "degraded"
    : pod.phase === "Failed" ? "critical"
    : "unknown";

  const bg =
    dot === "healthy" ? "border-brand-green/30 bg-brand-green/5"
    : dot === "degraded" ? "border-yellow-500/30 bg-yellow-500/5"
    : dot === "critical" ? "border-red-500/30 bg-red-500/5"
    : "border-gray-600/30 bg-gray-600/5";

  return (
    <div className={`border rounded-lg p-3 text-xs font-mono ${bg}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className={`status-dot ${dot}`} />
        <span className="text-white truncate max-w-[120px]" title={pod.name}>{pod.name}</span>
      </div>
      <div className="text-gray-500 space-y-0.5">
        <p>{pod.namespace}</p>
        <p>CPU: {pod.cpu_usage} | MEM: {pod.memory_usage}</p>
        {pod.restarts > 0 && (
          <p className={pod.restarts > 20 ? "text-red-400" : pod.restarts > 5 ? "text-yellow-400" : "text-gray-500"}>
            Restarts: {pod.restarts}
          </p>
        )}
      </div>
    </div>
  );
}

export default function PodGrid() {
  const [pods, setPods] = useState<Pod[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  const fetchPods = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/k8s/pods");
      if (res.ok) setPods(await res.json());
    } catch { /* use stale data */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchPods(); }, []);

  const filtered = pods.filter(
    (p) => p.name.includes(filter) || p.namespace.includes(filter) || p.phase.includes(filter)
  );

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-semibold text-white">Pod Grid</p>
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Filter pods..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="text-xs bg-brand-muted border border-brand-border rounded px-2 py-1 text-gray-300 placeholder-gray-600 outline-none focus:border-brand-green/50 w-32"
          />
          <button onClick={fetchPods} className="text-gray-500 hover:text-brand-green transition-colors">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>
      {loading ? (
        <div className="text-center py-8 text-gray-600 text-sm">Loading pods...</div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-72 overflow-y-auto">
          {filtered.map((pod) => (
            <PodBadge key={`${pod.namespace}/${pod.name}`} pod={pod} />
          ))}
        </div>
      )}
      <p className="text-xs text-gray-600 mt-3">{filtered.length} pods shown</p>
    </div>
  );
}
