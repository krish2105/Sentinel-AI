"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield } from "lucide-react";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/targets", label: "Targets" },
  { href: "/proxy", label: "Firewall" },
  { href: "/model-card", label: "Evals" },
];

export function Nav() {
  const path = usePathname();
  return (
    <header className="fixed top-0 inset-x-0 z-50 flex justify-center px-4 pt-4">
      <nav className="glass rounded-full px-3 py-2 flex items-center gap-1 w-full max-w-3xl">
        <Link href="/" className="flex items-center gap-2 px-3 py-1.5 group">
          <span className="relative flex h-7 w-7 items-center justify-center rounded-lg bg-cyan/10">
            <Shield className="h-4 w-4 text-cyan" />
            <span className="absolute inset-0 rounded-lg bg-cyan/20 animate-pulse-ring" />
          </span>
          <span className="font-semibold tracking-tight hidden sm:block">
            Sentinel<span className="text-cyan">AI</span>
          </span>
        </Link>
        <div className="flex-1" />
        {LINKS.map((l) => {
          const active = path === l.href || path.startsWith(l.href + "/");
          return (
            <Link
              key={l.href}
              href={l.href}
              className={cn(
                "px-3.5 py-1.5 rounded-full text-sm transition-colors",
                active ? "bg-cyan/15 text-cyan" : "text-muted hover:text-white"
              )}
            >
              {l.label}
            </Link>
          );
        })}
        <Link
          href="/targets"
          className="ml-1 px-4 py-1.5 rounded-full text-sm font-medium bg-cyan text-base hover:shadow-glow transition-shadow"
        >
          Launch
        </Link>
      </nav>
    </header>
  );
}
