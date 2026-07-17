"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut, Shield } from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/ThemeProvider";
import { useAuth } from "@/components/AuthProvider";

const LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/targets", label: "Targets" },
  { href: "/proxy", label: "Firewall" },
  { href: "/model-card", label: "Evals" },
];

export function Nav() {
  const path = usePathname();
  const { authenticated, email, logout } = useAuth();
  return (
    <header className="fixed top-0 inset-x-0 z-50 flex justify-center px-4 pt-4">
      <nav className="glass rounded-full px-3 py-2 flex items-center gap-1 w-full max-w-3xl">
        <Link
          href="/"
          aria-label="Sentinel AI home"
          className="flex items-center gap-2 px-3 py-1.5 group"
        >
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
                "px-3.5 py-1.5 rounded-full text-sm transition-colors hidden md:block",
                active ? "bg-cyan/15 text-cyan" : "text-muted hover:text-fg"
              )}
            >
              {l.label}
            </Link>
          );
        })}
        <ThemeToggle />
        {authenticated ? (
          <button
            onClick={logout}
            title={email ? `Signed in as ${email} — sign out` : "Sign out"}
            className="ml-1 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm text-muted hover:text-fg transition-colors"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span className="hidden sm:block">Sign out</span>
          </button>
        ) : (
          <Link
            href="/auth"
            className={cn(
              "ml-1 px-3.5 py-1.5 rounded-full text-sm transition-colors",
              path === "/auth" ? "bg-cyan/15 text-cyan" : "text-muted hover:text-fg"
            )}
          >
            Sign in
          </Link>
        )}
        <Link
          href="/targets"
          className="ml-1 px-4 py-1.5 rounded-full text-sm font-medium bg-cyan text-accent-fg hover:shadow-glow transition-shadow"
        >
          Launch
        </Link>
      </nav>
    </header>
  );
}
