"use client";

import { motion } from "motion/react";
import { Bot, Radar, ScanLine, Network, FileCheck2, Boxes } from "lucide-react";

const FEATURES = [
  {
    icon: Bot,
    title: "Adversarial agent swarm",
    body: "A LangGraph multi-agent system: orchestrator, attacker, target harness, and an isolated LLM-as-judge, with a human-in-the-loop gate for live attacks.",
  },
  {
    icon: ScanLine,
    title: "Two-tier detection",
    body: "A deterministic prompt-injection classifier as the fast first layer, an LLM judge as the reasoning second layer — cost vs. coverage, done right.",
  },
  {
    icon: FileCheck2,
    title: "Grounded findings",
    body: "Every vulnerability cites a real OWASP / MITRE ATLAS entry retrieved via hybrid RAG. No hand-wavy 'the AI thinks it's bad'.",
  },
  {
    icon: Radar,
    title: "Runtime guardrail proxy",
    body: "A drop-in firewall: input scan → target → output scan, with PII redaction, prompt-leak detection, and least-privilege tool gating.",
  },
  {
    icon: Network,
    title: "Blast-radius scoring",
    body: "Severity is amplified by the target's declared tool reach. A leak on a read-only bot ≠ a hijack on an agent with external tools.",
  },
  {
    icon: Boxes,
    title: "Measured, not asserted",
    body: "Classifier precision/recall/FPR and a proxy-OFF vs proxy-ON A/B: attack-success-rate reduced 83%. Evals you can point to.",
  },
];

export function Features() {
  return (
    <section className="max-w-6xl mx-auto px-6 py-28">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="mb-14"
      >
        <span className="mono text-xs text-cyan tracking-widest">DEFENSE-IN-DEPTH</span>
        <h2 className="text-fluid-sm font-bold mt-2">
          Not a single filter. A layered platform.
        </h2>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {FEATURES.map((f, i) => (
          <motion.div
            key={f.title}
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ delay: (i % 3) * 0.08 }}
            className="gradient-border rounded-2xl p-6 group"
          >
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan/10 text-cyan mb-4 group-hover:shadow-glow transition-shadow">
              <f.icon className="h-5 w-5" />
            </span>
            <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
            <p className="text-sm text-muted leading-relaxed">{f.body}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
