"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { Check, Copy } from "lucide-react";
import { SEVERITY_STYLES, VERDICT_STYLES, cn } from "@/lib/utils";

export function SeverityBadge({ severity }: { severity: string }) {
  const s = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.LOW;
  return (
    <span
      className="mono text-[11px] font-semibold px-2 py-0.5 rounded"
      style={{ color: s.color, background: s.bg }}
    >
      {severity}
    </span>
  );
}

export function VerdictChip({ verdict, size = "md" }: { verdict: string; size?: "sm" | "md" }) {
  const v = VERDICT_STYLES[verdict] ?? VERDICT_STYLES.SAFE;
  const blocked = verdict === "SAFE" || verdict === "BLOCKED";
  return (
    <motion.span
      initial={{ scale: 0.6, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 400, damping: 18 }}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md font-semibold mono border",
        size === "sm" ? "text-[10px] px-1.5 py-0.5" : "text-xs px-2.5 py-1"
      )}
      style={{ color: v.color, background: v.bg, borderColor: `${v.color}40` }}
    >
      <span
        className={cn("h-1.5 w-1.5 rounded-full", !blocked && "animate-pulse")}
        style={{ background: v.color }}
      />
      {v.label}
    </motion.span>
  );
}

export function PayloadViewer({
  text,
  label,
  tone = "neutral",
}: {
  text: string;
  label?: string;
  tone?: "neutral" | "danger" | "safe";
}) {
  const [copied, setCopied] = useState(false);
  const border =
    tone === "danger"
      ? "border-danger/30"
      : tone === "safe"
      ? "border-cyan/30"
      : "border-line";
  return (
    <div className={cn("rounded-lg bg-base/60 border overflow-hidden", border)}>
      {label && (
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-line/60 bg-surface/40">
          <span className="mono text-[10px] uppercase tracking-widest text-muted">
            {label}
          </span>
          <button
            onClick={() => {
              navigator.clipboard.writeText(text);
              setCopied(true);
              setTimeout(() => setCopied(false), 1200);
            }}
            className="text-muted hover:text-cyan transition-colors"
            aria-label="Copy payload"
          >
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          </button>
        </div>
      )}
      <pre className="mono text-[12px] leading-relaxed p-3 whitespace-pre-wrap break-words text-white/80 max-h-52 overflow-auto">
        {text}
      </pre>
    </div>
  );
}

export function Stat({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="gradient-border rounded-xl p-4">
      <div className="text-[11px] uppercase tracking-widest text-muted mb-1">{label}</div>
      <div className="text-2xl font-bold" style={{ color: accent }}>
        {value}
      </div>
      {sub && <div className="text-xs text-muted mt-1">{sub}</div>}
    </div>
  );
}
