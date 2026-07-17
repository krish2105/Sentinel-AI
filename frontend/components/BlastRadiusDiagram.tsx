"use client";

import { motion } from "motion/react";
import { Cpu, Database, Globe, PenLine } from "lucide-react";
import type { Tool } from "@/lib/api";

const RISK_META: Record<string, { color: string; Icon: any }> = {
  read: { color: "#22E9D3", Icon: Database },
  write: { color: "#FFB020", Icon: PenLine },
  external: { color: "#FF4D5E", Icon: Globe },
};

export function BlastRadiusDiagram({
  tools,
  compromised,
}: {
  tools: Tool[];
  compromised: boolean;
}) {
  const width = 460;
  const height = 260;
  const cx = 90;
  const cy = height / 2;
  const list = tools.length ? tools : [{ name: "no tools declared", risk: "read" as const }];

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full max-w-[460px]">
        {list.map((t, i) => {
          const y = 30 + (i * (height - 60)) / Math.max(1, list.length - 1 || 1);
          const meta = RISK_META[t.risk] ?? RISK_META.read;
          const dangerous = compromised && (t.risk === "write" || t.risk === "external");
          return (
            <g key={i}>
              <motion.path
                d={`M ${cx + 26} ${cy} C 200 ${cy}, 240 ${y}, ${340} ${y}`}
                fill="none"
                stroke={dangerous ? "#FF4D5E" : "#232838"}
                strokeWidth={dangerous ? 2 : 1.2}
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.8, delay: i * 0.12 }}
                style={dangerous ? { filter: "drop-shadow(0 0 4px #FF4D5E)" } : undefined}
              />
              {dangerous && (
                <motion.circle
                  r={3}
                  fill="#FF4D5E"
                  initial={{ offsetDistance: "0%" }}
                >
                  <animateMotion
                    dur="1.6s"
                    repeatCount="indefinite"
                    path={`M ${cx + 26} ${cy} C 200 ${cy}, 240 ${y}, ${340} ${y}`}
                  />
                </motion.circle>
              )}
              <motion.g
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.12 }}
              >
                <rect
                  x={344}
                  y={y - 16}
                  rx={8}
                  width={108}
                  height={32}
                  fill={dangerous ? "rgba(255,77,94,0.12)" : "rgba(18,20,28,0.9)"}
                  stroke={dangerous ? "#FF4D5E66" : meta.color + "44"}
                />
                <text x={360} y={y + 4} fontSize={10} fill={meta.color} className="mono">
                  {t.name.slice(0, 12)}
                </text>
                <text x={360} y={y - 20} fontSize={7} fill="#8A93A6" className="mono">
                  {t.risk.toUpperCase()}
                </text>
              </motion.g>
            </g>
          );
        })}

        {/* Central target node */}
        <circle
          cx={cx}
          cy={cy}
          r={30}
          fill="rgba(34,233,211,0.08)"
          stroke={compromised ? "#FF4D5E" : "#22E9D3"}
          strokeWidth={2}
          style={{
            filter: `drop-shadow(0 0 10px ${compromised ? "#FF4D5E88" : "#22E9D388"})`,
          }}
        />
        <foreignObject x={cx - 14} y={cy - 14} width={28} height={28}>
          <div className="flex items-center justify-center h-full">
            <Cpu
              className="h-5 w-5"
              style={{ color: compromised ? "#FF4D5E" : "#22E9D3" }}
            />
          </div>
        </foreignObject>
        <text x={cx} y={cy + 48} fontSize={9} fill="#8A93A6" textAnchor="middle" className="mono">
          AGENT
        </text>
      </svg>
    </div>
  );
}
