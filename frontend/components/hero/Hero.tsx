"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { ArrowRight, Radar } from "lucide-react";

const ShieldScene = dynamic(() => import("./ShieldScene"), {
  ssr: false,
  loading: () => <StaticShield />,
});

// Static SVG fallback (no WebGL / reduced motion) — same composition.
function StaticShield() {
  return (
    <svg viewBox="0 0 400 400" className="w-full h-full opacity-80">
      <defs>
        <radialGradient id="g" cx="50%" cy="50%">
          <stop offset="0%" stopColor="#22E9D3" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#22E9D3" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="200" cy="200" r="150" fill="url(#g)" />
      <circle cx="200" cy="200" r="120" fill="none" stroke="#22E9D3" strokeOpacity="0.5" />
      <circle cx="200" cy="200" r="70" fill="none" stroke="#22E9D3" strokeOpacity="0.7" />
      {Array.from({ length: 24 }).map((_, i) => {
        const a = (i / 24) * Math.PI * 2;
        const breach = i % 6 === 0;
        return (
          <circle
            key={i}
            cx={200 + Math.cos(a) * 160}
            cy={200 + Math.sin(a) * 160}
            r={3}
            fill={breach ? "#FF4D5E" : "#7cf2e4"}
          />
        );
      })}
    </svg>
  );
}

export function Hero() {
  const [webgl, setWebgl] = useState(true);
  const [reduce, setReduce] = useState(false);

  useEffect(() => {
    setReduce(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    try {
      const c = document.createElement("canvas");
      setWebgl(!!(c.getContext("webgl") || c.getContext("experimental-webgl")));
    } catch {
      setWebgl(false);
    }
  }, []);

  return (
    <section className="relative min-h-[92vh] flex items-center overflow-hidden pt-24">
      <div className="absolute inset-0 lg:left-[42%]">
        {webgl && !reduce ? <ShieldScene /> : <StaticShield />}
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-6 w-full">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="max-w-2xl"
        >
          <span className="inline-flex items-center gap-2 rounded-full border border-cyan/30 bg-cyan/5 px-3 py-1 text-xs text-cyan mono mb-6">
            <Radar className="h-3.5 w-3.5" /> OWASP LLM & Agentic Top 10 · 2026
          </span>

          <h1 className="text-fluid font-bold leading-[0.95] tracking-tight">
            <SplitText text="Every AI agent" />
            <br />
            <span className="text-gradient">
              <SplitText text="is an attack surface." delay={0.3} />
            </span>
          </h1>

          <p className="mt-6 text-lg text-muted max-w-xl leading-relaxed">
            Sentinel points an adversarial multi-agent swarm at any LLM app, scores it
            against the OWASP LLM & Agentic Top 10, then ships a runtime firewall that
            blocks prompt-injection in production.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              href="/targets"
              className="group inline-flex items-center gap-2 rounded-full bg-cyan px-6 py-3 font-medium text-base transition-shadow hover:shadow-glow"
            >
              Launch a red-team run
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link
              href="/proxy"
              className="inline-flex items-center gap-2 rounded-full border border-line px-6 py-3 font-medium text-fg/80 hover:border-cyan/50 hover:text-fg transition-colors"
            >
              Try the firewall
            </Link>
          </div>

          <div className="mt-10 flex gap-8 text-sm">
            <Metric value="83%" label="attack-success reduction" />
            <Metric value="8" label="attack categories" />
            <Metric value="2-tier" label="ML + judge defense" />
          </div>
        </motion.div>
      </div>

      <div className="absolute bottom-0 inset-x-0 h-32 bg-gradient-to-t from-base to-transparent pointer-events-none" />
    </section>
  );
}

function Metric({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <div className="text-2xl font-bold text-cyan">{value}</div>
      <div className="text-xs text-muted">{label}</div>
    </div>
  );
}

function SplitText({ text, delay = 0 }: { text: string; delay?: number }) {
  return (
    <span className="inline-block">
      {text.split(" ").map((word, i) => (
        <span key={i} className="inline-block overflow-hidden">
          <motion.span
            className="inline-block"
            initial={{ y: "110%" }}
            animate={{ y: 0 }}
            transition={{ delay: delay + i * 0.08, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            {word}&nbsp;
          </motion.span>
        </span>
      ))}
    </span>
  );
}
