"use client";

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import { Download, FileJson, ShieldAlert, Radar } from "lucide-react";
import { api, API_BASE, type Attack } from "@/lib/api";
import { PostureGauge } from "@/components/PostureGauge";
import { OwaspCoverageGrid } from "@/components/OwaspCoverageGrid";
import { BlastRadiusDiagram } from "@/components/BlastRadiusDiagram";
import { FindingCard } from "@/components/FindingCard";
import { Stat } from "@/components/primitives";

const VERDICT_COLORS: Record<string, string> = {
  SAFE: "#22E9D3",
  BLOCKED: "#3ba99c",
  LEAKED: "#FFB020",
  HIJACKED: "#FF4D5E",
};

export default function ReportPage({ params }: { params: { id: string } }) {
  const [data, setData] = useState<Awaited<ReturnType<typeof api.getReport>> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getReport(params.id)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [params.id]);

  if (error)
    return (
      <div className="max-w-3xl mx-auto px-6 pt-40 text-center text-muted">
        Could not load report: {error}
      </div>
    );
  if (!data)
    return (
      <div className="max-w-6xl mx-auto px-6 pt-40">
        <div className="h-64 rounded-2xl bg-surface/50 animate-pulse" />
      </div>
    );

  const report = data.report || {};
  const attacks: Attack[] = data.attacks || [];
  const exploited = attacks.filter(
    (a) => a.verdict === "LEAKED" || a.verdict === "HIJACKED"
  );

  const verdictData = Object.entries(report.verdict_counts || {})
    .map(([name, value]) => ({ name, value: value as number }))
    .filter((d) => d.value > 0);

  const severityData = Object.entries(report.severity_counts || {}).map(
    ([name, value]) => ({ name, value: value as number })
  );

  return (
    <div className="max-w-6xl mx-auto px-6 pt-28 pb-20">
      <div className="flex items-end justify-between flex-wrap gap-4 mb-8">
        <div>
          <span className="mono text-xs text-cyan tracking-widest">SCORED REPORT</span>
          <h1 className="text-3xl font-bold mt-1">{data.target?.name}</h1>
          <p className="text-muted mt-1">
            {attacks.length} attacks · {exploited.length} successful exploits ·{" "}
            {((report.attack_success_rate || 0) * 100).toFixed(0)}% attack-success rate
          </p>
        </div>
        <div className="flex gap-3">
          <a
            href={`${API_BASE}/reports/${params.id}/json`}
            className="inline-flex items-center gap-2 rounded-full border border-line px-4 py-2.5 text-sm hover:border-cyan/50 transition-colors"
          >
            <FileJson className="h-4 w-4" /> JSON
          </a>
          <a
            href={`${API_BASE}/reports/${params.id}/pdf`}
            className="inline-flex items-center gap-2 rounded-full bg-cyan px-4 py-2.5 text-sm font-medium text-base hover:shadow-glow transition-shadow"
          >
            <Download className="h-4 w-4" /> Export PDF
          </a>
        </div>
      </div>

      {/* Top summary grid */}
      <div className="grid lg:grid-cols-3 gap-6 mb-6">
        <div className="glass rounded-2xl p-6 flex flex-col items-center justify-center">
          <PostureGauge score={data.posture_score} />
        </div>

        <div className="glass rounded-2xl p-6">
          <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
            <Radar className="h-4 w-4 text-cyan" /> Verdict distribution
          </h3>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={verdictData}
                dataKey="value"
                nameKey="name"
                innerRadius={45}
                outerRadius={70}
                paddingAngle={3}
                stroke="none"
              >
                {verdictData.map((d) => (
                  <Cell key={d.name} fill={VERDICT_COLORS[d.name] ?? "#8A93A6"} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "#12141C",
                  border: "1px solid #232838",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-3 justify-center mt-2">
            {verdictData.map((d) => (
              <span key={d.name} className="text-[11px] flex items-center gap-1.5 text-muted">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ background: VERDICT_COLORS[d.name] }}
                />
                {d.name} {d.value}
              </span>
            ))}
          </div>
        </div>

        <div className="glass rounded-2xl p-6">
          <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-danger" /> Blast radius
          </h3>
          <BlastRadiusDiagram
            tools={data.target?.tools || []}
            compromised={exploited.length > 0}
          />
          <p className="text-xs text-muted mt-2">
            Reach score {report.blast_radius ?? 1}/5 — severity is amplified by declared
            tool access.
          </p>
        </div>
      </div>

      {/* OWASP + severity */}
      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        <div className="glass rounded-2xl p-6">
          <h3 className="text-sm font-semibold mb-4">OWASP coverage</h3>
          <OwaspCoverageGrid attacks={attacks} />
        </div>
        <div className="glass rounded-2xl p-6">
          <h3 className="text-sm font-semibold mb-4">Successful exploits by severity</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={severityData}>
              <XAxis dataKey="name" stroke="#8A93A6" fontSize={11} tickLine={false} />
              <YAxis stroke="#8A93A6" fontSize={11} allowDecimals={false} tickLine={false} />
              <Tooltip
                cursor={{ fill: "rgba(255,255,255,0.03)" }}
                contentStyle={{
                  background: "#12141C",
                  border: "1px solid #232838",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {severityData.map((d) => (
                  <Cell
                    key={d.name}
                    fill={
                      d.name === "CRITICAL"
                        ? "#FF4D5E"
                        : d.name === "HIGH"
                        ? "#FF7A45"
                        : d.name === "MEDIUM"
                        ? "#FFB020"
                        : "#8A93A6"
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Findings */}
      <h2 className="text-xl font-bold mb-4">
        Findings <span className="text-muted text-base font-normal">({attacks.length})</span>
      </h2>
      <div className="space-y-3">
        {[...attacks]
          .sort((a, b) => {
            const rank: Record<string, number> = {
              HIJACKED: 0,
              LEAKED: 1,
              BLOCKED: 2,
              SAFE: 3,
            };
            return (rank[a.verdict] ?? 3) - (rank[b.verdict] ?? 3);
          })
          .map((a, i) => (
            <FindingCard key={a.id} attack={a} index={i} />
          ))}
      </div>
    </div>
  );
}
