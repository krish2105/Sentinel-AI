# Viva / Interview Q&A

Rehearse these — they map directly to the code.

### 1. Why a two-tier detector (classifier + LLM judge)?
Deterministic ML is fast and cheap for the common case; the LLM judge reasons
about novel/obfuscated attacks the classifier misses. It's a cost-vs-coverage
trade-off. In our own eval the heuristic classifier hits precision 1.0 / recall
0.75 — the 25% it misses (e.g. semantically-malicious but keyword-free tool-abuse)
is exactly what the judge catches. Two layers, each covering the other's weakness.

### 2. What's the lethal trifecta and how does Sentinel address it?
Private data + untrusted content + external communication in one context =
deterministic injection exploitability. Sentinel breaks it with structural
separation of system vs user/tool content, output egress scanning, and
least-privilege tool gating (external tools need human approval).

### 3. Direct vs indirect prompt injection?
Direct = the attacker types it. Indirect = the payload is hidden in retrieved or
tool content (an HTML comment, white text, unicode confusables). Indirect is the
harder, more common production case — so our input scanner is designed to run on
tool/RAG output too, not just user input, and normalizes unicode + folds
homoglyphs before matching.

### 4. Why LangGraph over a simple loop?
Explicit typed state, checkpointing for the human-in-the-loop gate, resumable runs
that survive a reconnect, and clean conditional routing. That's production-grade
orchestration versus a script. The `human_gate` interrupt is the concrete payoff:
the run pauses mid-graph for a live-attack confirmation and resumes.

### 5. How do you know the guardrail actually works?
The A/B eval: attack-success-rate proxy-OFF (1.0) vs proxy-ON (0.167) → **83.3%
reduction** (`evals/guardrail_ab.json`). Plus classifier precision/recall/FPR
(`classifier_report.json`), judge agreement 100% on a golden set
(`judge_eval.json`), and RAG context-precision 100% (`rag_eval.json`). Measured,
not asserted.

### 6. What's "blast radius" and why score it?
Impact depends on what the compromised agent can *do*. A leak on a read-only bot
is minor; a hijack on an agent with external tools is critical. Severity is
amplified by the target's declared tool reach — a 1–5 score from tool risk tags,
promoting successful attacks to CRITICAL when reach ≥ 4.

### 7. How is Sentinel itself hardened?
No execution of model output; secrets only in env; append-only audit log storing
payload *hashes* not raw payloads; per-key rate limits; CORS lock;
unicode-normalized + homoglyph-folded input sanitization; a global exception
handler that never leaks internals.

### 8. Why does it run with no API keys?
Graceful degradation. Every heavy/external dependency (Groq, deberta,
sentence-transformers, pgvector) has a deterministic local fallback (mock engine,
heuristic classifier, hashed embeddings, SQLite). A reviewer sees it work
instantly; provisioning keys upgrades it to production-grade. The fallbacks are
deterministic, which also makes the evals reproducible.

### 9. How is the LLM-as-judge kept trustworthy / un-hijackable?
It runs in a separate model context from the target (isolation), uses a strict
rubric prompt, returns structured JSON only, and is explicitly instructed never to
obey instructions embedded in the payload or response. We measure its agreement
against a labelled golden set to prove the verdicts are reliable.

### 10. What would you build next (v2)?
Fine-tune the injection classifier on collected run data; add MCP-server / agent-
skill scanning; a continuous-monitoring mode; multi-tenant orgs; Langfuse traces
surfaced in-app; RAGAS faithfulness on the citation step.

---

### One-liner for CV / LinkedIn
*Built Sentinel AI — an adversarial multi-agent red-team + runtime guardrail
platform that scores LLM apps against the OWASP LLM/Agentic Top 10 and blocks
prompt-injection in production. LangGraph orchestration, hybrid-RAG-grounded
findings, a deployed prompt-injection classifier, and a measured guardrail A/B
(attack-success-rate reduced 83%). Fully deployed, free-tier stack.*
