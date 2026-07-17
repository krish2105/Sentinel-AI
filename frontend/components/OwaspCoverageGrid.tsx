"use client";

import { motion } from "motion/react";
import { OWASP_CELLS, type Attack } from "@/lib/api";

// coverage: map of owasp_ref -> {total, failed}
export function OwaspCoverageGrid({ attacks }: { attacks: Attack[] }) {
  const coverage: Record<string, { total: number; failed: number }> = {};
  for (const a of attacks) {
    const c = (coverage[a.owasp_ref] ??= { total: 0, failed: 0 });
    c.total += 1;
    if (a.verdict === "LEAKED" || a.verdict === "HIJACKED") c.failed += 1;
  }

  return (
    <div>
      <div className="grid grid-cols-5 gap-2">
        {OWASP_CELLS.map((cell, i) => {
          const cov = coverage[cell.ref];
          const tested = !!cov;
          const failed = cov && cov.failed > 0;
          const bg = failed
            ? "rgba(255,77,94,0.16)"
            : tested
            ? "rgba(34,233,211,0.14)"
            : "rgba(35,40,56,0.35)";
          const border = failed ? "#FF4D5E66" : tested ? "#22E9D366" : "#232838";
          const color = failed ? "#FF4D5E" : tested ? "#22E9D3" : "#8A93A6";
          return (
            <motion.div
              key={cell.ref}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.04 }}
              className="relative rounded-lg p-2.5 aspect-square flex flex-col justify-between overflow-hidden"
              style={{ background: bg, border: `1px solid ${border}` }}
              title={`${cell.ref} — ${cell.name}${cov ? ` · ${cov.failed}/${cov.total} exploited` : " · not tested"}`}
            >
              {failed && (
                <motion.span
                  className="absolute inset-0"
                  style={{ background: "radial-gradient(circle,#FF4D5E22,transparent 70%)" }}
                  animate={{ opacity: [0.3, 0.7, 0.3] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              )}
              <span className="mono text-[11px] font-bold" style={{ color }}>
                {cell.ref}
              </span>
              <span className="text-[9px] leading-tight text-muted line-clamp-2">
                {cell.name}
              </span>
              {cov && (
                <span className="mono text-[9px]" style={{ color }}>
                  {cov.failed}/{cov.total}
                </span>
              )}
            </motion.div>
          );
        })}
      </div>
      <div className="flex gap-4 mt-3 text-[10px] text-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-sm bg-cyan/60" /> Tested · resisted
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-sm bg-danger/60" /> Exploited
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-sm bg-line" /> Not covered
        </span>
      </div>
    </div>
  );
}
