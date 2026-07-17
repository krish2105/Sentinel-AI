"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Activity, Ban, ShieldAlert } from "lucide-react";
import { API_BASE } from "@/lib/api";

type FeedEvent = {
  id: number;
  direction: string;
  action: string;
  owasp_ref: string;
  reason: string;
};

/**
 * Live firewall activity feed — consumes the /proxy/activity/stream SSE endpoint
 * that previously had no consumer. Every block fired anywhere in the proxy shows
 * up here in real time.
 */
export function FirewallFeed({ max = 8 }: { max?: number }) {
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const idRef = useRef(0);

  useEffect(() => {
    // Relative URL routes through the Next rewrite → backend (no CORS).
    const url = `${API_BASE}/proxy/activity/stream`;
    let es: EventSource | null = null;
    try {
      es = new EventSource(url);
    } catch {
      return;
    }
    es.addEventListener("open", () => setConnected(true));
    es.addEventListener("connected", () => setConnected(true));
    es.addEventListener("firewall_event", (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setEvents((prev) =>
          [{ id: ++idRef.current, ...data }, ...prev].slice(0, max)
        );
      } catch {
        /* ignore malformed frame */
      }
    });
    es.addEventListener("error", () => setConnected(false));
    return () => es?.close();
  }, [max]);

  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="h-4 w-4 text-cyan" />
        <span className="font-semibold text-sm">Live firewall feed</span>
        <span
          className={
            "ml-auto flex items-center gap-1.5 mono text-[10px] " +
            (connected ? "text-cyan" : "text-muted")
          }
        >
          <span
            className={
              "h-1.5 w-1.5 rounded-full " +
              (connected ? "bg-cyan animate-pulse" : "bg-muted")
            }
          />
          {connected ? "streaming" : "connecting…"}
        </span>
      </div>

      {events.length === 0 ? (
        <p className="text-xs text-muted py-6 text-center">
          No firewall events yet. Run an attack through the proxy above and blocks
          will stream in here live.
        </p>
      ) : (
        <div className="space-y-2">
          <AnimatePresence initial={false}>
            {events.map((ev) => {
              const blocked = ev.action === "BLOCK";
              return (
                <motion.div
                  key={ev.id}
                  layout
                  initial={{ opacity: 0, x: -16 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ type: "spring", stiffness: 400, damping: 32 }}
                  className="flex items-center gap-3 rounded-lg bg-base/50 border border-line/60 px-3 py-2"
                >
                  {blocked ? (
                    <Ban className="h-3.5 w-3.5 text-danger shrink-0" />
                  ) : (
                    <ShieldAlert className="h-3.5 w-3.5 text-warning shrink-0" />
                  )}
                  <span
                    className={
                      "mono text-[10px] px-1.5 py-0.5 rounded shrink-0 " +
                      (blocked ? "text-danger bg-danger/10" : "text-warning bg-warning/10")
                    }
                  >
                    {ev.action}
                  </span>
                  <span className="mono text-[10px] text-muted shrink-0">
                    {ev.direction}
                  </span>
                  <span className="text-xs text-muted truncate flex-1">{ev.reason}</span>
                  {ev.owasp_ref && (
                    <span className="mono text-[10px] text-cyan shrink-0">
                      {ev.owasp_ref}
                    </span>
                  )}
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
