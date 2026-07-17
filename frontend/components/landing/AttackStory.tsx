"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform, type MotionValue } from "motion/react";
import { Brain, Wrench, Network, ShieldCheck } from "lucide-react";

type Stage = { icon: any; title: string; body: string; color: string };

function StageCard({
  stage,
  index,
  progress,
}: {
  stage: Stage;
  index: number;
  progress: MotionValue<number>;
}) {
  const total = 4;
  const start = index / total;
  const end = (index + 1) / total;
  // Scroll-linked transforms are accelerated via the WAAPI ScrollTimeline, whose
  // keyframe offsets MUST stay within [0,1]. Values outside that range (e.g. a
  // negative lead-in on the first card, or >1 tail on the last) throw
  // "Offsets must be monotonically non-decreasing" and crash the page — so clamp.
  const clamp01 = (n: number) => Math.min(1, Math.max(0, n));
  const opacity = useTransform(
    progress,
    [clamp01(start - 0.12), start, clamp01(end - 0.05), clamp01(end + 0.05)],
    [0.25, 1, 1, 0.25]
  );
  const scale = useTransform(
    progress,
    [clamp01(start - 0.1), start, end],
    [0.95, 1, 0.98]
  );
  const Icon = stage.icon;
  return (
    <motion.div
      style={{ opacity, scale }}
      className={`glass rounded-2xl p-6 flex items-start gap-4 ${
        index % 2 === 0 ? "mr-auto ml-0 md:mr-[52%]" : "ml-auto mr-0 md:ml-[52%]"
      } max-w-md`}
    >
      <span
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl"
        style={{ background: `${stage.color}1a`, color: stage.color }}
      >
        <Icon className="h-5 w-5" />
      </span>
      <div>
        <div className="mono text-[10px] tracking-widest text-muted mb-1">
          STAGE {index + 1}
        </div>
        <h3 className="font-semibold text-lg" style={{ color: stage.color }}>
          {stage.title}
        </h3>
        <p className="text-sm text-muted mt-1 leading-relaxed">{stage.body}</p>
      </div>
    </motion.div>
  );
}

const STAGES = [
  {
    icon: Brain,
    title: "Compromised intent",
    body: "A prompt-injection payload — often hidden in a retrieved document or tool output — overrides the model's instructions.",
    color: "#FF4D5E",
  },
  {
    icon: Wrench,
    title: "Tool power",
    body: "The hijacked model still holds its tools, memory, and credentials. Language manipulation becomes real-world capability.",
    color: "#FF7A45",
  },
  {
    icon: Network,
    title: "Propagation",
    body: "The lethal trifecta — private data + untrusted content + external comms — lets a single injection exfiltrate or act system-wide.",
    color: "#FFB020",
  },
  {
    icon: ShieldCheck,
    title: "Containment",
    body: "Sentinel breaks the chain: structural separation, egress scanning, least-privilege tool gating, and human approval on high-risk actions.",
    color: "#22E9D3",
  },
];

export function AttackStory() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end end"],
  });

  return (
    <section ref={ref} className="relative h-[320vh]">
      <div className="sticky top-0 h-screen flex flex-col items-center justify-center overflow-hidden px-6">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-fluid-sm font-bold text-center mb-3"
        >
          How an attack becomes a <span className="text-danger">breach</span>
        </motion.h2>
        <p className="text-muted text-center mb-12 max-w-lg">
          Scroll to watch a language-layer manipulation escalate into a system-wide
          compromise — and how Sentinel contains it.
        </p>

        <div className="relative w-full max-w-4xl">
          {/* progress rail */}
          <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-line">
            <motion.div
              className="absolute top-0 left-0 w-full bg-cyan origin-top"
              style={{ scaleY: scrollYProgress, height: "100%" }}
            />
          </div>

          <div className="grid grid-cols-1 gap-6">
            {STAGES.map((s, i) => (
              <StageCard key={i} stage={s} index={i} progress={scrollYProgress} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
