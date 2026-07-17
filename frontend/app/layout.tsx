import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { SmoothScroll } from "@/components/SmoothScroll";
import { Nav } from "@/components/Nav";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Sentinel AI — LLM Red-Team + Runtime Guardrail Platform",
  description:
    "Point Sentinel at any LLM app or agent; it launches an adversarial attack swarm, scores it against the OWASP LLM & Agentic Top 10, and ships a runtime firewall that blocks prompt-injection in production.",
  keywords: ["LLM security", "prompt injection", "OWASP", "AI red team", "guardrails"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`}>
      <body className="bg-console min-h-screen antialiased">
        <SmoothScroll>
          <Nav />
          <main>{children}</main>
        </SmoothScroll>
      </body>
    </html>
  );
}
