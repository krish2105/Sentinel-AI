"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE } from "@/lib/api";

export type StreamEvent = {
  type: string;
  data: any;
};

const EVENT_TYPES = [
  "run_started",
  "human_gate",
  "armed",
  "gate_timeout",
  "attack_planned",
  "payload_generated",
  "classified",
  "target_responded",
  "verdict",
  "run_completed",
  "error",
];

export function useRunStream(runId: string | null, autostart = true) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [status, setStatus] = useState<"idle" | "connecting" | "streaming" | "done" | "error">(
    "idle"
  );
  const [progress, setProgress] = useState(0);
  const esRef = useRef<EventSource | null>(null);

  const start = useCallback(() => {
    if (!runId || esRef.current) return;
    setStatus("connecting");
    setEvents([]);
    const es = new EventSource(`${API_BASE}/runs/${runId}/stream`);
    esRef.current = es;

    const push = (type: string) => (e: MessageEvent) => {
      let data: any = {};
      try {
        data = JSON.parse(e.data);
      } catch {}
      setEvents((prev) => [...prev, { type, data }]);
      if (type === "run_started") setStatus("streaming");
      if (type === "verdict" && typeof data.progress === "number")
        setProgress(data.progress);
      if (type === "run_completed") {
        setStatus("done");
        setProgress(1);
        es.close();
        esRef.current = null;
      }
    };

    EVENT_TYPES.forEach((t) => es.addEventListener(t, push(t)));
    es.onerror = () => {
      setStatus((s) => (s === "done" ? s : "error"));
      es.close();
      esRef.current = null;
    };
  }, [runId]);

  const stop = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
  }, []);

  useEffect(() => {
    if (autostart && runId) start();
    return () => stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]);

  return { events, status, progress, start, stop };
}
