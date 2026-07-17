// API client for the Sentinel backend. All calls go through the Next.js
// rewrite proxy (/api -> backend) so there is no CORS friction in the browser.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL && typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_API_URL
    : "/api";

export type Tool = { name: string; risk: "read" | "write" | "external" };

export type Target = {
  id: string;
  name: string;
  system_prompt: string;
  endpoint_url?: string | null;
  tools: Tool[];
  consent: boolean;
  created_at: string;
};

export type Run = {
  id: string;
  target_id: string;
  status: string;
  live_armed: boolean;
  posture_score: number;
  selected_categories: string[];
  started_at: string;
  finished_at?: string | null;
};

export type Verdict = "SAFE" | "BLOCKED" | "LEAKED" | "HIJACKED";
export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type Attack = {
  id: string;
  category: string;
  payload: string;
  target_response: string;
  classifier_score: number;
  verdict: Verdict;
  severity: Severity;
  owasp_ref: string;
  citation: string;
  mitigation: string;
  blast_radius: number;
};

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

export const api = {
  health: () => req<{ status: string; llm_provider: string }>("/health"),

  listTargets: () => req<Target[]>("/targets"),
  getTarget: (id: string) => req<Target>(`/targets/${id}`),
  createTarget: (body: Partial<Target>) =>
    req<Target>("/targets", { method: "POST", body: JSON.stringify(body) }),
  deleteTarget: (id: string) =>
    req<void>(`/targets/${id}`, { method: "DELETE" }),

  listRuns: () => req<Run[]>("/runs"),
  getRun: (id: string) => req<Run>(`/runs/${id}`),
  createRun: (body: { target_id: string; selected_categories: string[]; live_armed?: boolean }) =>
    req<Run>("/runs", { method: "POST", body: JSON.stringify(body) }),
  armRun: (id: string) => req<Run>(`/runs/${id}/arm`, { method: "POST" }),
  getRunAttacks: (id: string) => req<Attack[]>(`/runs/${id}/attacks`),

  getReport: (id: string) =>
    req<{
      run_id: string;
      posture_score: number;
      report: any;
      attacks: Attack[];
      target: { name: string; tools: Tool[] };
    }>(`/reports/${id}`),

  dashboard: () =>
    req<{
      totals: {
        runs: number;
        completed: number;
        attacks: number;
        avg_posture: number;
        firewall_blocks: number;
      };
      posture_trend: { run_id: string; date: string; posture: number; asr: number }[];
      failure_clusters: {
        category: string;
        label: string;
        owasp_ref: string;
        total: number;
        failed: number;
        fail_rate: number;
        avg_classifier: number;
      }[];
      recent_activity: { direction: string; action: string; reason: string; owasp_ref: string; at: string }[];
    }>("/dashboard"),

  evals: () =>
    req<{
      classifier: any;
      guardrail_ab: any;
      judge: any;
      rag: any;
    }>("/evals"),

  proxyChat: (body: {
    message: string;
    system_prompt: string;
    guardrails: boolean;
  }) =>
    req<{
      blocked: boolean;
      stage: string;
      action: string;
      reason: string;
      owasp_ref: string;
      response: string;
      classifier_score: number;
      input_scan: any;
      output_scan: any;
      latency_ms: number;
    }>("/proxy/chat", { method: "POST", body: JSON.stringify(body) }),
};

export const ATTACK_CATEGORIES = [
  { key: "direct_injection", label: "Direct Injection", owasp: "LLM01" },
  { key: "indirect_injection", label: "Indirect Injection", owasp: "LLM01" },
  { key: "system_prompt_leak", label: "System-Prompt Leak", owasp: "LLM07" },
  { key: "jailbreak", label: "Jailbreak", owasp: "LLM01" },
  { key: "sensitive_disclosure", label: "Sensitive Disclosure", owasp: "LLM02" },
  { key: "excessive_agency", label: "Excessive Agency", owasp: "LLM06" },
  { key: "goal_hijacking", label: "Goal Hijacking", owasp: "ASI01" },
  { key: "data_poisoning", label: "Data Poisoning", owasp: "ASI05" },
];

export const OWASP_CELLS = [
  { ref: "LLM01", name: "Prompt Injection" },
  { ref: "LLM02", name: "Sensitive Disclosure" },
  { ref: "LLM03", name: "Supply Chain" },
  { ref: "LLM04", name: "Data Poisoning" },
  { ref: "LLM05", name: "Improper Output" },
  { ref: "LLM06", name: "Excessive Agency" },
  { ref: "LLM07", name: "System-Prompt Leak" },
  { ref: "LLM08", name: "Vector Weakness" },
  { ref: "LLM09", name: "Misinformation" },
  { ref: "LLM10", name: "Unbounded Consumption" },
];
