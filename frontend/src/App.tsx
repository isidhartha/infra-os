import React, { useState, useEffect, useRef } from "react";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Incidents from "./pages/Incidents";

export type Page = "dashboard" | "incidents";

export interface MetricsSnapshot {
  timestamp: number;
  cluster: {
    cpu_usage_pct: number;
    memory_usage_pct: number;
    pod_count: number;
    node_count: number;
    alert_count: number;
  };
  nodes: Array<{ name: string; cpu_pct: number; memory_pct: number; pod_count: number }>;
  top_pods: Array<{ name: string; namespace: string; cpu_millicores: number; memory_mib: number; restarts: number }>;
  request_rate: number;
  error_rate_pct: number;
  p99_latency_ms: number;
}

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [metrics, setMetrics] = useState<MetricsSnapshot | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = () => {
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      const host = window.location.hostname;
      const port = import.meta.env.DEV ? "8000" : window.location.port;
      const url = `${proto}://${host}:${port}/ws/metrics`;

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => setWsConnected(true);
      ws.onmessage = (e) => {
        try { setMetrics(JSON.parse(e.data)); } catch { /* ignore */ }
      };
      ws.onclose = () => {
        setWsConnected(false);
        setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();
    };
    connect();
    return () => wsRef.current?.close();
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-brand-dark text-gray-200">
      <Sidebar currentPage={page} onNavigate={setPage} wsConnected={wsConnected} />
      <main className="flex-1 overflow-y-auto">
        {page === "dashboard" && <Dashboard metrics={metrics} />}
        {page === "incidents" && <Incidents />}
      </main>
    </div>
  );
}
