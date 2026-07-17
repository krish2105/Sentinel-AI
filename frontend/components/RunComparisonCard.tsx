"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowDownRight,
  ArrowUpRight,
  Minus,
  TrendingUp,
  TriangleAlert,
} from "lucide-react";
import { api, ATTACK_CATEGORIES, type RunComparison } from "@/lib/api";

function catLabel(k: string) {
  return ATTACK_CATEGORIES.find((c) => c.key === k)?.label ?? k;
}

/**
 * Run-to-run comparison — posture/ASR deltas vs the previous run of the same
 * target, plus regression alerts (categories newly failing). Renders nothing on
 * the baseline run (no previous run to compare against).
 */
export function RunComparisonCard({ runId }: { runId: string }) {
  const [cmp, setCmp] = useState<RunComparison | null>(null);

  useEffect(() => {
    api.compareRun(runId).then(setCmp).catch(() => {});
  }, [runId]);

  if (!cmp || !cmp.has_previous) return null;

  const pd = cmp.posture_delta ?? 0;
  const improved = pd > 0 && !cmp.regression;

  return (
    <div
      className={
        "glass rounded-2xl p-5 mb-6 border " +
        (cmp.regression ? "border-danger/40" : improved ? "border-cyan/40" : "border-line")
      }
    >
      <div className="flex items-center gap-2 mb-3">
        {cmp.regression ? (
          <TriangleAlert className="h-4 w-4 text-danger" />
        ) : (
          <TrendingUp className="h-4 w-4 text-cyan" />
        )}
        <span className="font-semibold text-sm">
          {cmp.regression ? "Regression vs previous run" : "Compared to previous run"}
        </span>
        {cmp.previous_run_id && (
          <Link
            href={`/reports/${cmp.previous_run_id}`}
            className="mono text-[10px] text-muted hover:text-cyan ml-auto"
          >
            ← previous run
          </Link>
        )}
      </div>

      <p className="text-sm text-muted mb-4">{cmp.summary}</p>

      <div className="grid grid-cols-2 gap-3">
        <Delta
          label="Posture"
          value={cmp.posture}
          prev={cmp.previous_posture}
          delta={cmp.posture_delta}
          higherIsBetter
        />
        <Delta
          label="Attack-success rate"
          value={Math.round(cmp.asr * 100)}
          prev={cmp.previous_asr === null ? null : Math.round(cmp.previous_asr * 100)}
          delta={cmp.asr_delta === null ? null : Math.round(cmp.asr_delta * 100)}
          suffix="%"
          higherIsBetter={false}
        />
      </div>

      {(cmp.regressed_categories.length > 0 || cmp.fixed_categories.length > 0) && (
        <div className="flex flex-wrap gap-2 mt-4">
          {cmp.regressed_categories.map((c) => (
            <span
              key={c}
              className="mono text-[10px] px-2 py-1 rounded bg-danger/10 text-danger"
            >
              ▼ now failing: {catLabel(c)}
            </span>
          ))}
          {cmp.fixed_categories.map((c) => (
            <span
              key={c}
              className="mono text-[10px] px-2 py-1 rounded bg-cyan/10 text-cyan"
            >
              ▲ fixed: {catLabel(c)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function Delta({
  label,
  value,
  prev,
  delta,
  suffix = "",
  higherIsBetter,
}: {
  label: string;
  value: number;
  prev: number | null;
  delta: number | null;
  suffix?: string;
  higherIsBetter: boolean;
}) {
  const good = delta === null || delta === 0 ? null : higherIsBetter ? delta > 0 : delta < 0;
  const Icon = delta === null || delta === 0 ? Minus : delta > 0 ? ArrowUpRight : ArrowDownRight;
  const color =
    good === null ? "text-muted" : good ? "text-cyan" : "text-danger";
  return (
    <div className="rounded-xl bg-base/50 border border-line/60 p-3">
      <div className="text-[10px] uppercase tracking-widest text-muted mb-1">{label}</div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold">
          {value}
          {suffix}
        </span>
        {prev !== null && (
          <span className={`mono text-xs inline-flex items-center gap-0.5 ${color}`}>
            <Icon className="h-3 w-3" />
            {delta !== null ? `${delta > 0 ? "+" : ""}${delta}${suffix}` : "—"}
          </span>
        )}
      </div>
      {prev !== null && (
        <div className="mono text-[10px] text-muted mt-0.5">
          was {prev}
          {suffix}
        </div>
      )}
    </div>
  );
}
