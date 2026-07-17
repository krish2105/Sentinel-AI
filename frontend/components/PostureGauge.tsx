"use client";

import { useEffect, useState } from "react";
import { motion, useMotionValue, useTransform, animate } from "motion/react";
import { scoreColor } from "@/lib/utils";

export function PostureGauge({ score, size = 220 }: { score: number; size?: number }) {
  const radius = size / 2 - 18;
  const circ = 2 * Math.PI * radius;
  const color = scoreColor(score);

  const progress = useMotionValue(0);
  const [display, setDisplay] = useState(0);
  const dash = useTransform(progress, (p) => `${(p / 100) * circ} ${circ}`);

  useEffect(() => {
    const controls = animate(progress, score, {
      duration: 1.4,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => setDisplay(Math.round(v)),
    });
    return controls.stop;
  }, [score, progress]);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#232838"
          strokeWidth={12}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={12}
          strokeLinecap="round"
          style={{ strokeDasharray: dash, filter: `drop-shadow(0 0 8px ${color}88)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-5xl font-bold tabular-nums" style={{ color }}>
          {display}
        </span>
        <span className="text-[11px] uppercase tracking-widest text-muted mt-1">
          Posture Score
        </span>
        <span className="text-[10px] text-muted mt-0.5">out of 100</span>
      </div>
    </div>
  );
}
