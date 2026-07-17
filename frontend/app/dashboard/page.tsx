"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import {
  LineChart,
  Line,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  ScatterChart,
  Scatter,
  ZAxis,
  CartesianGrid,
} from "recharts";
import { Activity, ShieldCheck, Crosshair, Gauge, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { Stat } from "@/components/primitives";
import { timeAgo } from "@/lib/utils";

export default function DashboardPage() {
  const [data, setData] = useState<Awaited<ReturnType<typeof api.dashboard>> | null>(null);

  useEffect(() => {
    api.dashboard().then(setData).catch(() => {});
  }, []);

  const t = data?.totals;
  const trend = (data?.posture_trend || []).map((p, i) => ({
    idx: i + 1,
    posture: p.posture,
    asr: Math.round(p.asr * 100),
  }));
  const clusters = (data?.failure_clusters || []).map((c) => ({
    ...c,
    x: Math.round(c.avg_classifier * 100),
    y: Math.round(c.fail_rate * 100),
    z: c.total,
  }));

  return (
    <div className="max-w-6xl mx-auto px-6 pt-28 pb-20">
      <div className="mb-8">
        <span className="mono text-xs text-cyan tracking-widest">SECURITY OPERATIONS</span>
        <h1 className="text-3xl font-bold mt-1">Dashboard</h1>
        <p className="text-muted mt-1">
          Posture trend, failure clustering, and live firewall activity.
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Stat label="Runs" value={t?.runs ?? "—"} sub={`${t?.completed ?? 0} completed`} />
        <Stat
          label="Avg posture"
          value={t?.avg_posture ?? "—"}
          accent="#22E9D3"
          sub="across completed runs"
        />
        <Stat label="Attacks fired" value={t?.attacks ?? "—"} />
        <Stat
          label="Firewall blocks"
          value={t?.firewall_blocks ?? "—"}
          accent="#FF4D5E"
          sub="proxy events"
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* Posture trend */}
        <div className="glass rounded-2xl p-6">
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <Gauge className="h-4 w-4 text-cyan" /> Posture trend
          </h3>
          {trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={230}>
              <LineChart data={trend}>
                <defs>
                  <linearGradient id="posLine" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#22E9D3" />
                    <stop offset="100%" stopColor="#7cf2e4" />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#232838" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="idx" stroke="#8A93A6" fontSize={11} tickLine={false} />
                <YAxis stroke="#8A93A6" fontSize={11} domain={[0, 100]} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    background: "#12141C",
                    border: "1px solid #232838",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="posture"
                  stroke="url(#posLine)"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: "#22E9D3" }}
                  animationDuration={1400}
                />
                <Line
                  type="monotone"
                  dataKey="asr"
                  stroke="#FF4D5E"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart label="Run a red-team to build the trend" />
          )}
          <div className="flex gap-4 mt-2 text-[11px] text-muted">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-cyan" /> posture
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-danger" /> attack-success %
            </span>
          </div>
        </div>

        {/* Failure clusters */}
        <div className="glass rounded-2xl p-6">
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <Crosshair className="h-4 w-4 text-danger" /> Failure clustering
          </h3>
          {clusters.length > 0 ? (
            <ResponsiveContainer width="100%" height={230}>
              <ScatterChart margin={{ left: -10 }}>
                <CartesianGrid stroke="#232838" strokeDasharray="3 3" />
                <XAxis
                  type="number"
                  dataKey="x"
                  name="classifier"
                  stroke="#8A93A6"
                  fontSize={11}
                  domain={[0, 100]}
                  tickLine={false}
                  label={{ value: "classifier %", position: "insideBottom", offset: -2, fill: "#8A93A6", fontSize: 10 }}
                />
                <YAxis
                  type="number"
                  dataKey="y"
                  name="failrate"
                  stroke="#8A93A6"
                  fontSize={11}
                  domain={[0, 100]}
                  tickLine={false}
                />
                <ZAxis type="number" dataKey="z" range={[60, 400]} />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  contentStyle={{
                    background: "#12141C",
                    border: "1px solid #232838",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  formatter={(v: any, n: any) => [v, n === "x" ? "classifier%" : n === "y" ? "fail%" : n]}
                />
                <Scatter data={clusters} fill="#FF4D5E" fillOpacity={0.7} />
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart label="No attack data yet" />
          )}
          <p className="text-[11px] text-muted mt-2">
            Bubble size = attempts · Y = exploit rate · X = mean classifier score.
          </p>
        </div>
      </div>

      {/* Firewall activity */}
      <div className="glass rounded-2xl p-6">
        <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
          <Activity className="h-4 w-4 text-cyan" /> Firewall activity
        </h3>
        {data?.recent_activity && data.recent_activity.length > 0 ? (
          <div className="space-y-1.5">
            {data.recent_activity.map((e, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                className="flex items-center gap-3 text-sm rounded-lg bg-base/40 border border-line/50 px-3 py-2"
              >
                <span
                  className="mono text-[10px] px-1.5 py-0.5 rounded"
                  style={{
                    background: e.action === "BLOCK" ? "rgba(255,77,94,0.12)" : "rgba(34,233,211,0.1)",
                    color: e.action === "BLOCK" ? "#FF4D5E" : "#22E9D3",
                  }}
                >
                  {e.action}
                </span>
                <span className="mono text-[10px] text-muted">{e.direction}</span>
                {e.owasp_ref && (
                  <span className="mono text-[10px] text-muted">{e.owasp_ref}</span>
                )}
                <span className="flex-1 text-muted truncate">{e.reason}</span>
                <span className="text-[10px] text-muted">{timeAgo(e.at)}</span>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-muted text-sm">
            No firewall activity yet.{" "}
            <Link href="/proxy" className="text-cyan hover:underline inline-flex items-center gap-1">
              Try the firewall <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

function EmptyChart({ label }: { label: string }) {
  return (
    <div className="h-[230px] flex items-center justify-center text-muted text-sm border border-dashed border-line rounded-xl">
      {label}
    </div>
  );
}
