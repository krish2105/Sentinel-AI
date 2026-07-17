import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { SmoothScroll } from "@/components/SmoothScroll";
import { Nav } from "@/components/Nav";
import { ThemeProvider, themeBootScript } from "@/components/ThemeProvider";
import { ToastProvider } from "@/components/Toaster";
import { AuthProvider } from "@/components/AuthProvider";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://sentinel-ai.vercel.app";
const DESCRIPTION =
  "Point Sentinel at any LLM app or agent; it launches an adversarial attack swarm, scores it against the OWASP LLM & Agentic Top 10, and ships a runtime firewall that blocks prompt-injection in production.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Sentinel AI — LLM Red-Team + Runtime Guardrail Platform",
    template: "%s · Sentinel AI",
  },
  description: DESCRIPTION,
  keywords: ["LLM security", "prompt injection", "OWASP", "AI red team", "guardrails"],
  authors: [{ name: "Sentinel AI" }],
  openGraph: {
    title: "Sentinel AI — LLM Red-Team + Runtime Guardrail Platform",
    description: DESCRIPTION,
    url: SITE_URL,
    siteName: "Sentinel AI",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Sentinel AI — LLM Red-Team + Runtime Guardrail Platform",
    description: DESCRIPTION,
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${mono.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeBootScript }} />
      </head>
      <body className="bg-console min-h-screen antialiased">
        <ThemeProvider>
          <AuthProvider>
            <ToastProvider>
              <SmoothScroll>
                <Nav />
                <main>{children}</main>
              </SmoothScroll>
            </ToastProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
