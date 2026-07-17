"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ChevronDown, ShieldAlert, ShieldCheck, BookMarked, FileText } from "lucide-react";
import type { Attack } from "@/lib/api";
import { ATTACK_CATEGORIES } from "@/lib/api";
import { SeverityBadge, VerdictChip, PayloadViewer } from "./primitives";

function label(cat: string) {
  return ATTACK_CATEGORIES.find((c) => c.key === cat)?.label ?? cat;
}

export function FindingCard({ attack, index }: { attack: Attack; index: number }) {
  const [open, setOpen] = useState(false);
  const exploited = attack.verdict === "LEAKED" || attack.verdict === "HIJACKED";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      className="glass rounded-xl overflow-hidden"
    >
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-3 p-4 text-left hover:bg-fg/[0.02] transition-colors"
      >
        {exploited ? (
          <ShieldAlert className="h-5 w-5 text-danger shrink-0" />
        ) : (
          <ShieldCheck className="h-5 w-5 text-cyan shrink-0" />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium">{label(attack.category)}</span>
            <span className="mono text-[10px] text-muted px-1.5 py-0.5 rounded bg-fg/5">
              {attack.owasp_ref}
            </span>
            {attack.injection_vector === "document" && (
              <span
                className="mono text-[10px] text-warning px-1.5 py-0.5 rounded bg-warning/10 inline-flex items-center gap-1"
                title="Delivered indirectly — hidden inside a retrieved document the target ingested"
              >
                <FileText className="h-3 w-3" /> via document
              </span>
            )}
          </div>
          <div className="text-xs text-muted mt-0.5 truncate">
            classifier {(attack.classifier_score * 100).toFixed(0)}% · blast radius{" "}
            {attack.blast_radius}/5
          </div>
        </div>
        <SeverityBadge severity={attack.severity} />
        <VerdictChip verdict={attack.verdict} size="sm" />
        <ChevronDown
          className={`h-4 w-4 text-muted transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-3">
              {attack.injection_vector === "document" && (
                <div className="rounded-lg bg-warning/[0.07] border border-warning/25 p-3 flex items-start gap-2">
                  <FileText className="h-3.5 w-3.5 text-warning mt-0.5 shrink-0" />
                  <p className="text-xs text-fg/75 leading-relaxed">
                    <b className="text-warning">Indirect injection.</b> The user request was
                    benign — this payload was hidden inside a retrieved document the target
                    ingested as context, so the instruction never appeared in the user turn.
                  </p>
                </div>
              )}
              <PayloadViewer
                label={
                  attack.injection_vector === "document"
                    ? "Poisoned document (payload)"
                    : "Attack payload"
                }
                text={attack.payload}
                tone="danger"
              />
              <PayloadViewer
                label="Target response"
                text={attack.target_response}
                tone={exploited ? "danger" : "safe"}
              />
              {attack.citation && (
                <div className="rounded-lg bg-cyan/[0.06] border border-cyan/20 p-3">
                  <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-cyan mb-1">
                    <BookMarked className="h-3 w-3" /> Grounded citation
                  </div>
                  <p className="text-xs text-fg/70 leading-relaxed">{attack.citation}</p>
                </div>
              )}
              <div className="rounded-lg bg-surface-2 border border-line p-3">
                <div className="text-[10px] uppercase tracking-widest text-muted mb-1">
                  Recommended mitigation
                </div>
                <p className="text-sm text-fg/85">{attack.mitigation}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
