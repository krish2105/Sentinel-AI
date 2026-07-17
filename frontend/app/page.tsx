import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Hero } from "@/components/hero/Hero";
import { Features } from "@/components/landing/Features";
import { AttackStory } from "@/components/landing/AttackStory";

export default function LandingPage() {
  return (
    <>
      <Hero />
      <Features />
      <AttackStory />

      {/* CTA */}
      <section className="max-w-4xl mx-auto px-6 py-28 text-center">
        <div className="glass rounded-3xl p-12 relative overflow-hidden">
          <div className="absolute inset-0 bg-grid-fade pointer-events-none" />
          <h2 className="text-fluid-sm font-bold relative">
            Find the holes before attackers do.
          </h2>
          <p className="text-muted mt-4 max-w-lg mx-auto relative">
            Register a target, launch an adversarial run, and watch attacks get blocked
            in real time — then export an OWASP-mapped report.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3 relative">
            <Link
              href="/targets"
              className="group inline-flex items-center gap-2 rounded-full bg-cyan px-6 py-3 font-medium text-base hover:shadow-glow transition-shadow"
            >
              Get started
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-full border border-line px-6 py-3 font-medium text-white/80 hover:border-cyan/50 transition-colors"
            >
              View dashboard
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-line py-10 text-center text-sm text-muted">
        <p>
          Sentinel AI — LLM & AI-Agent Security Platform · Free-tier native · Built on
          FastAPI + LangGraph + Next.js
        </p>
      </footer>
    </>
  );
}
