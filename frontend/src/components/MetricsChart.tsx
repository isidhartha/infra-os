import React, { useEffect, useRef, useState } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import type { MetricsSnapshot } from "../App";

interface DataPoint {
  time: string;
  cpu: number;
  memory: number;
  errorRate: number;
  latency: number;
}

interface Props {
  metrics: MetricsSnapshot | null;
}

const MAX_POINTS = 30;

export default function MetricsChart({ metrics }: Props) {
  const [data, setData] = useState<DataPoint[]>([]);
  const countRef = useRef(0);

  useEffect(() => {
    if (!metrics) return;
    countRef.current += 1;
    const point: DataPoint = {
      time: new Date(metrics.timestamp * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
      cpu: metrics.cluster.cpu_usage_pct,
      memory: metrics.cluster.memory_usage_pct,
      errorRate: metrics.error_rate_pct,
      latency: metrics.p99_latency_ms,
    };
    setData((prev) => [...prev.slice(-MAX_POINTS + 1), point]);
  }, [metrics]);

  const tooltipStyle = {
    backgroundColor: "#111827",
    border: "1px solid #1f2937",
    borderRadius: "8px",
    fontSize: "11px",
  };

  return (
    <div className="glass rounded-xl p-4 space-y-6">
      <p className="text-sm font-semibold text-white">Real-Time Metrics</p>

      <div>
        <p className="text-xs text-gray-500 mb-2">CPU & Memory Usage (%)</p>
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="time" tick={{ fill: "#4b5563", fontSize: 10 }} interval="preserveStartEnd" />
            <YAxis domain={[0, 100]} tick={{ fill: "#4b5563", fontSize: 10 }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Area type="monotone" dataKey="cpu" stroke="#00BFFF" fill="#00BFFF22" name="CPU %" strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="memory" stroke="#00FF88" fill="#00FF8822" name="Memory %" strokeWidth={2} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div>
        <p className="text-xs text-gray-500 mb-2">P99 Latency (ms)</p>
        <ResponsiveContainer width="100%" height={120}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="time" tick={{ fill: "#4b5563", fontSize: 10 }} interval="preserveStartEnd" />
            <YAxis tick={{ fill: "#4b5563", fontSize: 10 }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Area type="monotone" dataKey="latency" stroke="#a78bfa" fill="#a78bfa22" name="P99 ms" strokeWidth={2} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
