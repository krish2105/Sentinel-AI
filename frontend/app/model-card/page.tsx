"use client";

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import {
  BarChart,
  Bar,
  Cell,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import { ScanLine, Gauge, Scale, BookMarked } from "lucide-react";
import { api } from "@/lib/api";

export default function ModelCardPage() {
  const [data, setData] = useState<Awaited<ReturnType<typeof api.evals>> | null>(null);
  useEffect(() => {
    api.evals().then(setData).catch(() => {});
  }, []);

  const c = data?.classifier;
  const ab = data?.guardrail_ab;
  const judge = data?.judge;
  const rag = data?.rag;

  const cm = c?.confusion_matrix;

  return (
    <div className="max-w-5xl mx-auto px-6 pt-28 pb-20">
      <div className="mb-8">
        <span className="mono text-xs text-cyan tracking-widest">EVALUATION</span>
        <h1 className="text-3xl font-bold mt-1">Model Card & Evals</h1>
        <p className="text-muted mt-1 max-w-2xl">
          The differentiator: measured, reproducible evaluation of the classifier, the
          guardrail, the LLM-as-judge, and the RAG grounding.
        </p>
      </div>

      {/* Headline metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Metric
          icon={Gauge}
          label="Guardrail ASR reduction"
          value={ab ? `${ab.attack_success_rate_reduction_pct}%` : "—"}
          accent="#22E9D3"
        />
        <Metric
          icon={ScanLine}
          label="Classifier F1"
          value={c ? c.f1.toFixed(2) : "—"}
        />
        <Metric
          icon={Scale}
          label="Judge agreement"
          value={judge ? `${Math.round(judge.agreement_accuracy * 100)}%` : "—"}
        />
        <Metric
          icon={BookMarked}
          label="RAG precision@3"
          value={rag ? `${Math.round(rag.context_precision_at_3 * 100)}%` : "—"}
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Classifier card */}
        <div className="glass rounded-2xl p-6">
          <h2 className="font-semibold mb-1 flex items-center gap-2">
            <ScanLine className="h-4 w-4 text-cyan" /> Prompt-Injection Classifier
          </h2>
          <p className="text-xs text-muted mb-4">
            engine: <span className="mono text-fg/70">{c?.engine ?? "—"}</span> · n=
            {c?.n ?? "—"}
          </p>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <Cell2 label="Precision" value={c?.precision} />
            <Cell2 label="Recall" value={c?.recall} />
            <Cell2 label="F1" value={c?.f1} />
            <Cell2 label="False-positive rate" value={c?.false_positive_rate} danger />
          </div>
          {cm && (
            <div>
              <div className="text-xs uppercase tracking-widest text-muted mb-2">
                Confusion matrix
              </div>
              <div className="grid grid-cols-2 gap-1.5 max-w-[220px]">
                <ConfCell label="TP" value={cm.tp} tone="good" />
                <ConfCell label="FP" value={cm.fp} tone="bad" />
                <ConfCell label="FN" value={cm.fn} tone="bad" />
                <ConfCell label="TN" value={cm.tn} tone="good" />
              </div>
            </div>
          )}
        </div>

        {/* Guardrail A/B */}
        <div className="glass rounded-2xl p-6">
          <h2 className="font-semibold mb-1 flex items-center gap-2">
            <Gauge className="h-4 w-4 text-cyan" /> Guardrail A/B Effectiveness
          </h2>
          <p className="text-xs text-muted mb-4">
            Attack-success-rate with the proxy off vs on.
          </p>
          {ab && (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={[
                  { name: "Proxy OFF", asr: Math.round(ab.asr_proxy_off * 100) },
                  { name: "Proxy ON", asr: Math.round(ab.asr_proxy_on * 100) },
                ]}
              >
                <XAxis dataKey="name" stroke="#8A93A6" fontSize={12} tickLine={false} />
                <YAxis stroke="#8A93A6" fontSize={11} domain={[0, 100]} tickLine={false} />
                <Tooltip
                  cursor={{ fill: "rgba(255,255,255,0.03)" }}
                  contentStyle={{
                    background: "#12141C",
                    border: "1px solid #232838",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="asr" radius={[6, 6, 0, 0]}>
                  <Cell fill="#FF4D5E" />
                  <Cell fill="#22E9D3" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
          <p className="text-sm text-center mt-2">
            <span className="text-cyan font-bold text-lg">
              {ab ? `${ab.attack_success_rate_reduction_pct}%` : "—"}
            </span>{" "}
            <span className="text-muted">reduction · {ab?.attacks_blocked ?? 0} attacks blocked</span>
          </p>
        </div>

        {/* Judge */}
        <div className="glass rounded-2xl p-6">
          <h2 className="font-semibold mb-1 flex items-center gap-2">
            <Scale className="h-4 w-4 text-cyan" /> LLM-as-Judge Agreement
          </h2>
          <p className="text-xs text-muted mb-4">
            Golden set of {judge?.n ?? "—"} (payload, response, expected verdict) cases.
          </p>
          <div
            className="space-y-1.5 max-h-56 overflow-auto"
            tabIndex={0}
            role="region"
            aria-label="Judge golden-set results"
          >
            {judge?.cases?.map((cse: any, i: number) => (
              <div
                key={i}
                className="flex items-center gap-2 text-xs rounded-lg bg-base/40 border border-line/50 px-3 py-1.5"
              >
                <span className={cse.pass ? "text-cyan" : "text-danger"}>
                  {cse.pass ? "✓" : "✗"}
                </span>
                <span className="mono text-xs text-muted flex-1 truncate">
                  {cse.category}
                </span>
                <span className="mono text-xs text-muted">
                  {cse.expected} → {cse.got}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* RAG */}
        <div className="glass rounded-2xl p-6">
          <h2 className="font-semibold mb-1 flex items-center gap-2">
            <BookMarked className="h-4 w-4 text-cyan" /> RAG Grounding
          </h2>
          <p className="text-xs text-muted mb-4">
            Does the retriever surface the correct OWASP entry for each category?
          </p>
          <div
            className="space-y-1.5 max-h-56 overflow-auto"
            tabIndex={0}
            role="region"
            aria-label="RAG grounding results"
          >
            {rag?.per_category?.map((r: any, i: number) => (
              <div
                key={i}
                className="flex items-center gap-2 text-xs rounded-lg bg-base/40 border border-line/50 px-3 py-1.5"
              >
                <span className={r.hit ? "text-cyan" : "text-danger"}>
                  {r.hit ? "✓" : "✗"}
                </span>
                <span className="mono text-xs text-muted flex-1 truncate">
                  {r.category}
                </span>
                <span className="mono text-xs text-cyan">{r.expected_ref}</span>
                <span className="mono text-xs text-muted">
                  [{r.retrieved.join(", ")}]
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Metric({ icon: Icon, label, value, accent }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="gradient-border rounded-xl p-4"
    >
      <Icon className="h-4 w-4 text-cyan mb-2" />
      <div className={"text-2xl font-bold" + (accent ? " text-cyan" : "")}>
        {value}
      </div>
      <div className="text-[11px] text-muted mt-0.5">{label}</div>
    </motion.div>
  );
}

function Cell2({ label, value, danger }: { label: string; value?: number; danger?: boolean }) {
  return (
    <div className="rounded-lg bg-base/40 border border-line/50 p-3">
      <div className="text-xs uppercase tracking-widest text-muted">{label}</div>
      <div className={"text-lg font-bold mono " + (danger ? "text-danger" : "text-cyan")}>
        {value !== undefined ? value.toFixed(2) : "—"}
      </div>
    </div>
  );
}

function ConfCell({ label, value, tone }: { label: string; value: number; tone: "good" | "bad" }) {
  return (
    <div
      className="rounded-lg p-2.5 text-center"
      style={{
        background: tone === "good" ? "rgba(34,233,211,0.1)" : "rgba(255,77,94,0.1)",
        border: `1px solid ${tone === "good" ? "#22E9D344" : "#FF4D5E44"}`,
      }}
    >
      <div className="mono text-xs text-muted">{label}</div>
      <div className={"text-xl font-bold mono " + (tone === "good" ? "text-cyan" : "text-danger")}>
        {value}
      </div>
    </div>
  );
}
