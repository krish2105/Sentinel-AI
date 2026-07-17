"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "motion/react";
import {
  Terminal,
  ShieldAlert,
  ArrowRight,
  Zap,
  Loader2,
  Activity,
  FileText,
  MessagesSquare,
} from "lucide-react";
import { api, ATTACK_CATEGORIES, type Attack } from "@/lib/api";
import { useRunStream } from "@/hooks/useRunStream";
import { OwaspCoverageGrid } from "@/components/OwaspCoverageGrid";
import { PostureGauge } from "@/components/PostureGauge";
import { VerdictChip, SeverityBadge } from "@/components/primitives";

function catLabel(k: string) {
  return ATTACK_CATEGORIES.find((c) => c.key === k)?.label ?? k;
}

export default function RunConsolePage({ params }: { params: { id: string } }) {
  const runId = params.id;
  const { events, status, progress } = useRunStream(runId);
  const [posture, setPosture] = useState<number | null>(null);
  const [traceUrl, setTraceUrl] = useState<string | null>(null);
  const [gateOpen, setGateOpen] = useState(false);

  // Derive streaming attacks from verdict events.
  const attacks: Attack[] = useMemo(() => {
    return events
      .filter((e) => e.type === "verdict")
      .map((e) => ({
        id: e.data.id,
        category: e.data.category,
        payload: "",
        target_response: "",
        classifier_score: e.data.classifier_score ?? 0,
        verdict: e.data.verdict,
        severity: e.data.severity,
        owasp_ref: e.data.owasp_ref,
        citation: e.data.citation ?? "",
        mitigation: e.data.mitigation ?? "",
        blast_radius: e.data.blast_radius ?? 1,
        injection_vector: e.data.injection_vector ?? "direct",
        turns: e.data.turns ?? 1,
      }));
  }, [events]);

  const started = events.find((e) => e.type === "run_started");
  const total = started?.data.total ?? 0;

  useEffect(() => {
    const done = events.find((e) => e.type === "run_completed");
    if (done) {
      setPosture(done.data.posture_score);
      if (done.data.trace_url) setTraceUrl(done.data.trace_url);
    }
    setGateOpen(events.some((e) => e.type === "human_gate") && !events.some((e) => e.type === "armed"));
  }, [events]);

  const exploited = attacks.filter(
    (a) => a.verdict === "LEAKED" || a.verdict === "HIJACKED"
  ).length;

  return (
    <div className="max-w-6xl mx-auto px-6 pt-28 pb-20">
      <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
        <div>
          <span className="mono text-xs text-cyan tracking-widest">LIVE RED-TEAM CONSOLE</span>
          <h1 className="text-3xl font-bold mt-1 flex items-center gap-3">
            {started?.data.target ?? "Running…"}
            <StatusPill status={status} />
          </h1>
        </div>
        {status === "done" && (
          <div className="flex gap-3">
            {traceUrl && (
              <a
                href={traceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-full border border-line px-4 py-2.5 text-sm hover:border-cyan/50 transition-colors"
                title="Open this run's trace in Langfuse"
              >
                <Activity className="h-4 w-4" /> View trace
              </a>
            )}
            <Link
              href={`/reports/${runId}`}
              className="group inline-flex items-center gap-2 rounded-full bg-cyan px-5 py-2.5 font-medium text-base hover:shadow-glow transition-shadow"
            >
              View full report
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        )}
      </div>

      {/* progress bar */}
      <div className="h-1.5 rounded-full bg-surface overflow-hidden mb-8">
        <motion.div
          className="h-full bg-cyan"
          animate={{ width: `${progress * 100}%` }}
          transition={{ ease: "easeOut" }}
          style={{ boxShadow: "0 0 12px #22E9D3" }}
        />
      </div>

      <AnimatePresence>
        {gateOpen && <HumanGate runId={runId} onArmed={() => setGateOpen(false)} />}
      </AnimatePresence>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left: attack feed */}
        <div className="lg:col-span-2 space-y-6">
          <AttackFeed attacks={attacks} total={total} status={status} />
          <TerminalLog events={events} />
        </div>

        {/* Right: live metrics */}
        <div className="space-y-6">
          <div className="glass rounded-2xl p-6 flex flex-col items-center">
            {posture !== null ? (
              <PostureGauge score={posture} />
            ) : (
              <div className="flex flex-col items-center justify-center h-[220px] text-muted">
                <Loader2 className="h-8 w-8 animate-spin text-cyan mb-3" />
                <span className="text-sm">Scoring in progress…</span>
                <span className="mono text-2xl mt-2 text-fg">
                  {attacks.length}/{total || "…"}
                </span>
              </div>
            )}
            <div className="grid grid-cols-2 gap-3 w-full mt-4">
              <MiniStat label="Attacks" value={attacks.length} />
              <MiniStat label="Exploited" value={exploited} tone="danger" />
            </div>
          </div>

          <div className="glass rounded-2xl p-6">
            <h3 className="text-sm font-semibold mb-4">OWASP Coverage</h3>
            <OwaspCoverageGrid attacks={attacks} />
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const map: Record<string, { c: string; t: string }> = {
    connecting: { c: "#FFB020", t: "connecting" },
    streaming: { c: "#22E9D3", t: "live" },
    done: { c: "#22E9D3", t: "complete" },
    error: { c: "#FF4D5E", t: "error" },
    idle: { c: "#8A93A6", t: "idle" },
  };
  const s = map[status] ?? map.idle;
  return (
    <span
      className="mono text-[11px] px-2 py-1 rounded-full inline-flex items-center gap-1.5"
      style={{ color: s.c, background: `${s.c}1a` }}
    >
      <span className="h-1.5 w-1.5 rounded-full animate-pulse" style={{ background: s.c }} />
      {s.t}
    </span>
  );
}

function AttackFeed({
  attacks,
  total,
  status,
}: {
  attacks: Attack[];
  total: number;
  status: string;
}) {
  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold flex items-center gap-2">
          <Zap className="h-4 w-4 text-cyan" /> Attack feed
        </h3>
        <span className="mono text-xs text-muted">
          {attacks.length}/{total || "…"}
        </span>
      </div>
      <div className="space-y-2">
        <AnimatePresence initial={false}>
          {attacks.map((a, i) => {
            const exploited = a.verdict === "LEAKED" || a.verdict === "HIJACKED";
            return (
              <motion.div
                key={a.id ?? i}
                layout
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-3 rounded-lg bg-base/50 border border-line/60 p-3"
                style={exploited ? { borderColor: "#FF4D5E44" } : undefined}
              >
                <span className="mono text-[10px] text-muted w-5">{i + 1}</span>
                <span className="mono text-[10px] px-1.5 py-0.5 rounded bg-fg/5 text-muted">
                  {a.owasp_ref}
                </span>
                {a.injection_vector === "document" && (
                  <FileText
                    className="h-3 w-3 text-warning shrink-0"
                    aria-label="Indirect — via retrieved document"
                  />
                )}
                {(a.turns ?? 1) > 1 && (
                  <MessagesSquare
                    className="h-3 w-3 text-cyan shrink-0"
                    aria-label={`Multi-turn — ${a.turns} turns`}
                  />
                )}
                <span className="flex-1 text-sm truncate">{catLabel(a.category)}</span>
                <span className="mono text-[10px] text-muted hidden sm:block">
                  {(a.classifier_score * 100).toFixed(0)}%
                </span>
                <SeverityBadge severity={a.severity} />
                <VerdictChip verdict={a.verdict} size="sm" />
              </motion.div>
            );
          })}
        </AnimatePresence>
        {attacks.length === 0 && status !== "done" && (
          <div className="text-center py-10 text-muted text-sm">
            <Loader2 className="h-6 w-6 animate-spin text-cyan mx-auto mb-2" />
            Spinning up the attack swarm…
          </div>
        )}
      </div>
    </div>
  );
}

function TerminalLog({ events }: { events: { type: string; data: any }[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight });
  }, [events]);

  const lines = events
    .map((e) => {
      switch (e.type) {
        case "run_started":
          return `▸ run started · ${e.data.total} attacks queued · target=${e.data.target}`;
        case "human_gate":
          return `⚠ human gate · ${e.data.message}`;
        case "armed":
          return `✓ live attacks armed`;
        case "attack_planned":
          return `→ [${e.data.index}] planning ${e.data.label} (${e.data.owasp_ref})`;
        case "payload_generated":
          return `  ↳ payload: ${String(e.data.payload).slice(0, 90).replace(/\n/g, " ")}…`;
        case "classified":
          return `  ↳ classifier ${(e.data.classifier_score * 100).toFixed(0)}% ${
            e.data.signals?.length ? "[" + e.data.signals.join(",") + "]" : ""
          }`;
        case "target_responded":
          return `  ↳ target: ${String(e.data.response).slice(0, 90).replace(/\n/g, " ")}…`;
        case "verdict":
          return `  ✦ verdict=${e.data.verdict} severity=${e.data.severity}`;
        case "run_completed":
          return `■ run complete · posture score ${e.data.posture_score}/100`;
        default:
          return "";
      }
    })
    .filter(Boolean);

  return (
    <div className="glass rounded-2xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-line/60 bg-surface/40">
        <Terminal className="h-3.5 w-3.5 text-cyan" />
        <span className="mono text-[11px] text-muted">sentinel@redteam — live log</span>
        <div className="flex gap-1.5 ml-auto">
          <span className="h-2.5 w-2.5 rounded-full bg-danger/50" />
          <span className="h-2.5 w-2.5 rounded-full bg-warning/50" />
          <span className="h-2.5 w-2.5 rounded-full bg-cyan/50" />
        </div>
      </div>
      <div ref={ref} className="mono text-[11px] p-4 h-56 overflow-auto leading-relaxed">
        {lines.map((l, i) => (
          <div
            key={i}
            className={
              l.includes("verdict=HIJACKED") || l.includes("verdict=LEAKED")
                ? "text-danger"
                : l.startsWith("■") || l.startsWith("✓")
                ? "text-cyan"
                : l.startsWith("⚠")
                ? "text-warning"
                : "text-fg/60"
            }
          >
            {l}
          </div>
        ))}
        {lines.length > 0 && <div className="text-cyan caret" />}
      </div>
    </div>
  );
}

function HumanGate({ runId, onArmed }: { runId: string; onArmed: () => void }) {
  const [arming, setArming] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      className="glass rounded-2xl p-5 mb-6 border border-warning/30 flex items-center gap-4"
    >
      <ShieldAlert className="h-6 w-6 text-warning shrink-0" />
      <div className="flex-1">
        <div className="font-semibold text-warning">Human-in-the-loop gate</div>
        <p className="text-sm text-muted">
          This target has a live endpoint. Arm live attacks to fire against it, or wait
          to continue in simulation mode.
        </p>
      </div>
      <button
        onClick={async () => {
          setArming(true);
          await api.armRun(runId);
          onArmed();
        }}
        disabled={arming}
        className="rounded-full bg-warning text-base px-5 py-2.5 font-medium disabled:opacity-50"
      >
        {arming ? "Arming…" : "⚡ Arm live attacks"}
      </button>
    </motion.div>
  );
}

function MiniStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "danger";
}) {
  return (
    <div className="rounded-xl bg-base/50 border border-line/60 p-3 text-center">
      <div
        className="text-2xl font-bold"
        style={{ color: tone === "danger" ? "#FF4D5E" : "#22E9D3" }}
      >
        {value}
      </div>
      <div className="text-[10px] uppercase tracking-widest text-muted">{label}</div>
    </div>
  );
}
