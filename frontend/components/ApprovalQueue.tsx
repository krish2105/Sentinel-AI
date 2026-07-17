"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Check, ShieldQuestion, X } from "lucide-react";
import { api, type Approval } from "@/lib/api";
import { useToast } from "@/components/Toaster";

/**
 * Shadow-mode approval queue — the interactive half of least-privilege (LLM06).
 * Write/external tool calls the guardrail policy holds show up here for a human
 * to approve or deny. Polls (robust vs SSE buffering) and refreshes on `signal`.
 */
export function ApprovalQueue({ signal = 0 }: { signal?: number }) {
  const { toast } = useToast();
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setApprovals(await api.listApprovals("pending"));
    } catch {
      /* backend may be waking; the poll retries */
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, [load]);

  useEffect(() => {
    if (signal) load();
  }, [signal, load]);

  const decide = async (id: string, decision: "approve" | "deny") => {
    setBusy(id);
    try {
      await api.decideApproval(id, decision);
      setApprovals((a) => a.filter((x) => x.id !== id));
      toast(
        decision === "approve" ? "Tool call approved." : "Tool call denied.",
        decision === "approve" ? "success" : "info"
      );
    } catch (e) {
      toast(e instanceof Error ? e.message : "Decision failed.", "error");
    }
    setBusy(null);
  };

  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <ShieldQuestion className="h-4 w-4 text-warning" />
        <span className="font-semibold text-sm">Shadow-mode approval queue</span>
        {approvals.length > 0 && (
          <span className="mono text-[10px] px-1.5 py-0.5 rounded bg-warning/15 text-warning">
            {approvals.length} pending
          </span>
        )}
      </div>

      {approvals.length === 0 ? (
        <p className="text-xs text-muted py-6 text-center">
          No pending approvals. Request a <span className="text-warning">write</span> or{" "}
          <span className="text-danger">external</span> tool call below and it will be
          held here for your decision instead of executing.
        </p>
      ) : (
        <div className="space-y-2">
          <AnimatePresence initial={false}>
            {approvals.map((a) => (
              <motion.div
                key={a.id}
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="rounded-lg bg-base/50 border border-warning/30 p-3"
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="mono text-sm font-semibold">{a.tool_name}</span>
                  <span
                    className={
                      "mono text-[10px] px-1.5 py-0.5 rounded " +
                      (a.risk === "external"
                        ? "text-danger bg-danger/10"
                        : "text-warning bg-warning/10")
                    }
                  >
                    {a.risk}
                  </span>
                  <span className="mono text-[10px] text-cyan">{a.owasp_ref}</span>
                  {a.target_name && (
                    <span className="text-[11px] text-muted">· {a.target_name}</span>
                  )}
                  <div className="flex-1" />
                  <button
                    onClick={() => decide(a.id, "deny")}
                    disabled={busy === a.id}
                    className="flex items-center gap-1 rounded-full border border-line px-3 py-1 text-xs hover:border-danger/50 hover:text-danger transition-colors disabled:opacity-50"
                  >
                    <X className="h-3 w-3" /> Deny
                  </button>
                  <button
                    onClick={() => decide(a.id, "approve")}
                    disabled={busy === a.id}
                    className="flex items-center gap-1 rounded-full bg-cyan text-accent-fg px-3 py-1 text-xs font-medium hover:shadow-glow transition-shadow disabled:opacity-50"
                  >
                    <Check className="h-3 w-3" /> Approve
                  </button>
                </div>
                <p className="text-[11px] text-muted mt-1.5">{a.reason}</p>
                {a.arguments && (
                  <code className="mono text-[10px] text-muted block mt-1 truncate">
                    args: {a.arguments}
                  </code>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
