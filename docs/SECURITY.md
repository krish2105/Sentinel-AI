# Security Model & OWASP Mapping

Sentinel is both a security *product* and a security-*hardened* application. This
document covers (1) the controls Sentinel enforces on targets, and (2) how
Sentinel protects itself.

## The Guardrail Proxy pipeline (`/proxy/chat`)

```
request → [1] rate limit + auth
        → [2] INPUT SCAN
              • deberta injection classifier (score > threshold → BLOCK)   [LLM01]
              • semantic firewall: isolated, constrained LLM judges intent [LLM01]
              • policy rules: deny known exfil/egress patterns             [LLM02]
        → [3] TARGET call (sim or live)
        → [4] OUTPUT SCAN
              • PII / secret detection (regex, presidio-style) → REDACT    [LLM02]
              • system-prompt-leak detection (similarity to stored prompt) [LLM07]
              • toxicity / unsafe-content check → BLOCK                    [LLM05]
        → [5] tool-call gate: write/external tools → shadow-mode approval  [LLM06]
        → response  (or BLOCKED + reason + owasp_ref)
```

The same endpoint powers the before/after demo: `guardrails=false` lets an attack
leak; `guardrails=true` blocks it. Measured reduction: **83.3%** attack-success-rate
(`evals/guardrail_ab.json`).

## OWASP LLM & Agentic control mapping

| OWASP | Risk | Control in Sentinel | Where |
|---|---|---|---|
| **LLM01** | Prompt injection | Two-tier input scan (classifier + semantic firewall); structural separation of system vs user content; the input filter also runs on tool/RAG content (indirect injection). | `guardrails/input_scanner.py`, `ml/injection_model.py` |
| **LLM02** | Sensitive info disclosure | Output PII/secret scanner + redaction; exfil deny-list; secrets never echoed. | `guardrails/output_scanner.py`, `guardrails/policy.py` |
| **LLM05** | Improper output handling | Structured/validated outputs; model text is never `eval`'d; JSON parsing only. | `llm/client.py` (`complete_json`) |
| **LLM06** | Excessive agency | Tool allow-list + least privilege; `write`/`external` tools require shadow-mode human approval. | `guardrails/policy.py` |
| **LLM07** | System-prompt leakage | Output leak detector (similarity to stored system prompt); prompt never in a retrievable store; extraction attempts flagged. | `guardrails/output_scanner.py` |
| **LLM08** | Vector/embedding weakness | RAG sources are trusted-only; ingested docs are integrity-controlled; poisoning simulation is sandboxed. | `rag/ingest.py` |
| **ASI01** | Agent goal hijacking | Judge verifies the outcome vs the declared objective; human gate on redirection. | `agents/nodes.py` (judge) |
| **ASI05** | Memory/context poisoning | Poisoning simulation is sandboxed; memory writes are treated as untrusted. | `core/attack_library.py`, judge |

## Blast-radius scoring

Impact depends on what a compromised agent can *do*. Severity is amplified by the
target's declared tool reach: a leak on a read-only bot is minor; a hijack on an
agent with `external` tools is critical. `blast_radius()` scores 1–5 from tool
risk tags and count; the judge promotes `LEAKED`/`HIJACKED` findings to `CRITICAL`
when reach ≥ 4. (`guardrails/policy.py`)

## The lethal trifecta

Private data + untrusted content + external communication in one context =
deterministic injection exploitability. Sentinel breaks it with:
- **Structural separation** of system vs user/tool content.
- **Egress/output scanning** (block data leaving via the response).
- **Least-privilege tool gating** (external tools need approval).

## Protecting Sentinel itself (defense-in-depth)

- **Auth** — per-user API keys hashed with bcrypt; JWT sessions; per-client rate limiting (sliding window).
- **Least privilege** — the platform never executes arbitrary code from model output; live-target execution is opt-in + consent-gated + rate-limited.
- **Audit trail** — append-only `audit_log` of every run, armed live attack, and proxy block (actor, timestamp, payload *hash* — never the raw payload).
- **Secrets** — provider keys in env vars only; never logged, never returned; `.env` git-ignored; `.env.example` documents shape only.
- **Input hardening** — request size limits; upload sanitization (strip active content); **unicode NFKC normalization + homoglyph folding** to defeat hidden-character / confusable attacks; CORS locked to the frontend origin.
- **No internal leakage** — a global exception handler returns a generic 500; internals are logged, never sent to the client.

## Responsible-use guardrails

Attacking a live third-party endpoint requires: a per-target **consent** flag, an
explicit **"Arm live attacks"** confirmation (LangGraph human gate), and rate
limits. Sentinel is a defensive tool — test only what you are authorized to test.
