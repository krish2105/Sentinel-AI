import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const VERDICT_STYLES: Record<
  string,
  { color: string; bg: string; label: string; glow: string }
> = {
  SAFE: { color: "#22E9D3", bg: "rgba(34,233,211,0.12)", label: "SAFE", glow: "shadow-glow" },
  BLOCKED: { color: "#22E9D3", bg: "rgba(34,233,211,0.12)", label: "BLOCKED", glow: "shadow-glow" },
  LEAKED: { color: "#FFB020", bg: "rgba(255,176,32,0.12)", label: "LEAKED", glow: "" },
  HIJACKED: { color: "#FF4D5E", bg: "rgba(255,77,94,0.14)", label: "HIJACKED", glow: "shadow-glow-danger" },
};

export const SEVERITY_STYLES: Record<string, { color: string; bg: string }> = {
  CRITICAL: { color: "#FF4D5E", bg: "rgba(255,77,94,0.15)" },
  HIGH: { color: "#FF7A45", bg: "rgba(255,122,69,0.15)" },
  MEDIUM: { color: "#FFB020", bg: "rgba(255,176,32,0.15)" },
  LOW: { color: "#8A93A6", bg: "rgba(138,147,166,0.12)" },
};

export function scoreColor(score: number): string {
  if (score >= 80) return "#22E9D3";
  if (score >= 55) return "#FFB020";
  return "#FF4D5E";
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}
