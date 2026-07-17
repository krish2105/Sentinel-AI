<div align="center">

# 🛡️ Sentinel AI

### Adversarial Red-Team + Runtime Guardrail Platform for LLM & AI-Agent Security

**Point Sentinel at any LLM app or agent. It launches an adversarial attack swarm, scores the target against the OWASP LLM & Agentic Top 10, and ships a runtime firewall that blocks prompt-injection and unsafe actions in production.**

<br/>

![Status](https://img.shields.io/badge/status-MVP%20complete-22E9D3?style=flat-square)
![Free Tier](https://img.shields.io/badge/cost-%240%20free%20tier-22E9D3?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)
![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20LangGraph-009688?style=flat-square)
![Frontend](https://img.shields.io/badge/frontend-Next.js%2014-black?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11-3776AB?style=flat-square)
![Tests](https://img.shields.io/badge/tests-14%20passing-22E9D3?style=flat-square)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Why it matters](#why-it-matters)
- [Measured results](#measured-results)
- [Feature tour](#feature-tour)
- [Architecture](#architecture)
- [Graceful degradation](#graceful-degradation-runs-with-zero-keys)
- [Quickstart](#quickstart)
- [Deployment (free tier)](#deployment-free-tier)
- [Testing & evaluation](#testing--evaluation)
- [Project scorecard](#project-scorecard)
- [Tech stack](#tech-stack)
- [Repository layout](#repository-layout)
- [Responsible use](#responsible-use)

---

## Overview

Enterprises are shipping LLM apps and autonomous agents faster than they can secure them. Prompt injection is the single most actively exploited LLM vulnerability in production — and once a model has tools, memory, and credentials, a small language-layer manipulation can escalate into a system-wide breach.

**Sentinel AI is two products in one platform:**

| | | |
|---|---|---|
| 🎯 | **Red-Team Engine** | A LangGraph adversarial multi-agent system that generates and fires attacks at a target LLM/agent, judges whether each attack succeeded, and produces a scored report mapped to the **OWASP LLM Top 10 (2026)** and **OWASP Agentic Top 10** — with a grounded citation for every finding. |
| 🔥 | **Guardrail Proxy** | A drop-in runtime firewall that screens inputs and outputs with a two-tier detector (deterministic ML classifier + isolated LLM firewall), enforces least-privilege on agent tools, and runs high-risk actions in shadow mode pending human approval. |

---

## Why it matters

- **Prompt injection (OWASP LLM01)** is the most widely exploited LLM vulnerability in production, especially the *indirect* variant hidden in retrieved/tool content.
- The **OWASP Agentic Top 10** extends the LLM Top 10: once a model can *act*, prompt injection becomes goal hijacking, data poisoning becomes persistent memory corruption, and excessive agency becomes privilege escalation.
- The core threat pattern is the **"lethal trifecta"**: private data + untrusted content + external communication in one context = deterministic injection exploitability.

Sentinel breaks the chain with **defense-in-depth** — deterministic ML detection, a constrained LLM judge, allow/deny policy, and human approval gates — and grounds every finding in a real **OWASP / MITRE ATLAS** entry.

---

## Measured results

Every headline number is produced by a reproducible eval harness in [`backend/evals/`](backend/evals) and rendered on the in-app **Model Card** page.

| Metric | Result | Source |
|---|:---:|---|
| Guardrail attack-success-rate reduction (proxy OFF → ON) | **83.3%** | `evals/guardrail_ab.json` |
| Injection classifier — precision / recall / FPR | **1.00 / 0.75 / 0.00** | `evals/classifier_report.json` |
| LLM-as-judge agreement on golden set | **100%** | `evals/judge_eval.json` |
| RAG context precision @3 (OWASP mapping) | **100%** | `evals/rag_eval.json` |

> The classifier's 0.75 recall is intentional and honest: the ~25% of semantically-malicious-but-keyword-free attacks it misses are exactly what the **second-tier LLM judge** is there to catch. That's the two-tier design working as intended.

---

## Feature tour

- **Target Registry** — register a system prompt + optional live endpoint + declared tools (each tagged `read`/`write`/`external`). No endpoint? Sentinel simulates one so you always have something to attack.
- **Live Red-Team Console** — attacks stream in over Server-Sent Events with animated verdict chips, a typing terminal log, a filling OWASP coverage grid, and a posture gauge that counts up on completion.
- **Human-in-the-loop gate** — live-endpoint attacks pause on a LangGraph interrupt until you click **Arm live attacks**.
- **8 attack categories** — direct & indirect injection, system-prompt leak, jailbreak, sensitive-info disclosure, excessive agency, goal hijacking, and data/memory poisoning; jailbreak & goal-hijacking run as **multi-turn "crescendo"** attacks (benign build-up → exploit turn).
- **Scored Report** — per-attack verdict / severity / OWASP citation / payload / target response / mitigation, an aggregate posture score, verdict & severity charts, a **blast-radius diagram**, a **run-to-run comparison** with regression alerts, and **JSON / styled-PDF export**.
- **Firewall Playground** — send a malicious prompt with guardrails **ON** (watch the `BLOCKED` stamp slam in with the OWASP ref) vs **OFF** (watch it leak). The contrast *is* the demo.
- **In-app A/B before/after** — one click runs the *same* attack with guardrails off then on and renders the leaked-vs-blocked contrast side by side (`POST /proxy/ab`). The headline "83% ASR reduction" is now a live product surface, not just an offline eval script.
- **Unified playground** — put the firewall in front of a *registered target* (its system prompt + declared tools) or a free-form prompt, and scan an untrusted *retrieved document* alongside the message (indirect-injection defense).
- **Shadow-mode approval queue** — write/external tool calls are held for human approval instead of executing; approve/deny them from an interactive queue (`/approvals`), the interactive half of least-privilege (LLM06).
- **Truly-indirect injection** — the indirect-injection attack hides its payload inside a retrieved document the target ingests as context (not the user turn); findings are tagged **via document** so the vector is explicit.
- **Live firewall feed** — a real-time stream of every proxy block and held tool call, consuming the `/proxy/activity/stream` SSE endpoint.
- **Langfuse trace deep-links** — when tracing is configured, each run/report shows a **View trace** link straight to the inspectable Langfuse trace.
- **Accounts & API keys** — register for a personal API key, sign in (JWT), and get account-scoped targets/runs/reports; a shared **demo mode** keeps everything usable with zero signup.
- **Light / dark theme** — a first-class, no-flash theme toggle (system-preference aware, persisted) across the whole app.
- **Dashboard** — posture trend over time, per-category failure-cluster scatter, and a live firewall-activity feed.
- **Model Card** — the classifier confusion matrix, guardrail A/B chart, judge golden-set results, and RAG grounding table, live from the eval reports.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Frontend — Next.js 14 (Vercel)                                     │
│  landing · dashboard · targets · runs/[id] · reports/[id] · proxy   │
└───────────────┬─────────────────────────────────────────────────────┘
                │  REST + Server-Sent Events
┌───────────────▼─────────────────────────────────────────────────────┐
│  Backend — FastAPI (Render free)                                    │
│    /runs   → LangGraph agent graph → LLM (Groq free / Ollama / mock) │
│                  ├── hybrid RAG retriever → pgvector threat catalog  │
│                  └── deberta injection classifier (local)           │
│    /proxy  → Guardrail pipeline (input + doc scan → target → output) │
│    /approvals → shadow-mode queue: hold write/external tool calls    │
│    /auth   → register / issue API key · JWT · account-scoped data    │
│    core: JWT + bcrypt API keys · Fernet-encrypted target secrets ·   │
│          security headers + body cap · rate limit · audit log        │
└───────────────┬─────────────────────────────────────────────────────┘
                │
      ┌─────────▼──────────┐
      │  Postgres+pgvector  │  users · targets · runs · attacks
      │  (Supabase/Render)  │  proxy_events · tool_approvals · audit_log
      │                     │  threat_chunks
      └─────────────────────┘
```

**The agent graph (LangGraph):**

```
START → orchestrator ─┬─(live & not armed)─► human_gate ──► orchestrator
                      ├─(attacks remain)───► attacker
                      └─(queue empty)──────► reporter ──► END

attacker → classifier_node → target_harness → judge → orchestrator (loop)
```

Full detail in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · security controls in [`docs/SECURITY.md`](docs/SECURITY.md) · interview prep in [`docs/VIVA.md`](docs/VIVA.md).

---

## Graceful degradation (runs with zero keys)

Every heavy / external dependency has a **deterministic local fallback**, so the whole platform runs with zero setup and zero keys — and upgrades to production-grade when provisioned. This is what makes it a genuine free-tier SaaS *and* an instant demo.

| Component | Full mode | Zero-setup fallback |
|---|---|---|
| LLM inference | Groq free tier / Ollama | Deterministic mock engine |
| Injection classifier | `deberta-v3-prompt-injection-v2` | Heuristic detector (signatures + NFKC + homoglyph folding) |
| Embeddings | `bge-small-en-v1.5` | Feature-hashed embeddings |
| Reranker | `bge-reranker-base` | Lexical rerank |
| Vector + relational DB | Postgres + pgvector | SQLite |

---

## Quickstart

### Fastest path — zero dependencies (SQLite + mock engine)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.rag.ingest            # load the threat catalog
uvicorn app.main:app --reload       # http://localhost:8000  (API docs at /docs)

# Frontend (new shell)
cd frontend
npm install
npm run dev                         # http://localhost:3000
```

Then open http://localhost:3000 → **Targets → New target → "Prefill a sample vulnerable agent" → Red-team**.

### With Postgres + pgvector (docker-compose)

```bash
docker compose up -d                # Postgres+pgvector + backend (auto-ingests)
cd frontend && npm install && npm run dev
```

### Enable real models & real LLM attacks (still free)

```bash
# backend/.env
GROQ_API_KEY=gsk_...                # free key from https://console.groq.com
ENABLE_HEAVY_ML=true                # then: pip install -r requirements-ml.txt
```

---

## Deployment (free tier)

| Layer | Host | How |
|---|---|---|
| Backend | **Render** (free web service + free Postgres) | Push to GitHub → Render → New → **Blueprint** (uses [`render.yaml`](render.yaml)). Enable pgvector with `CREATE EXTENSION vector;`. Set `CORS_ORIGINS` to your Vercel URL. |
| Frontend | **Vercel** (free) | Import the repo, root dir `frontend/`, set `NEXT_PUBLIC_API_URL` to your Render URL. |
| Database | **Supabase / Render Postgres** (free) | The connection string is auto-normalized to the async driver. |

> **Cold-start note:** Render free instances sleep after inactivity; the `/health` endpoint wakes them. Model downloads are cached in the Docker image on first boot.

---

## Testing & evaluation

```bash
make test              # backend pytest — graph, scanners, tool allow-list, proxy A/B, approvals…
make eval              # classifier + guardrail A/B + judge + RAG eval reports
cd frontend && npm test        # Vitest unit tests (utils, api client, primitives)
cd frontend && npm run e2e     # Playwright happy-path (needs the backend running)
```

CI runs three jobs on every push and PR ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)):
**backend** (pytest + all four eval harnesses), **frontend** (typecheck + Vitest unit
tests + production build), and **e2e** (Playwright happy-path against a live backend +
frontend, in headless Chromium).

---

## Project scorecard

An honest self-assessment for a portfolio / applied-AI-security context.

| Dimension | Score | Notes |
|---|:---:|---|
| **Deployment readiness** | **82 / 100** | Docker, `render.yaml`, Vercel config, migrations, health checks, CI, managed-DB URL normalization. Not yet live-verified on public URLs; observability (Langfuse) is scaffolded, not wired. |
| **Real MVP completeness** | **88 / 100** | Every in-scope feature is functional end-to-end. Generative attacks and the real deberta classifier require a free key / heavy-ML flag (mock + heuristic by default). |
| **Free-tier SaaS viability** | **84 / 100** | 100% free stack, no paid keys, multi-tenant data scoping on every query. In-memory rate limiting is single-instance; billing is intentionally out of scope. |
| **Overall** | **85 / 100** | A production-grade, fully-runnable MVP. The path to 95+: live deployment, horizontal-safe rate limiting, enforced auth UI, live tracing, and a demo walkthrough. |

**What would push each dimension higher**
- *Deployment → 90+:* deploy to public Render + Vercel URLs; add Langfuse tracing; blue-green health gating.
- *MVP → 95+:* ship a recorded walkthrough GIF; wire promptfoo/RAGAS in place of the lightweight custom evals; expand pytest coverage.
- *SaaS → 92+:* Redis-backed rate limiting + sessions; enforced auth (remove demo fallback) with an onboarding UI; per-org isolation.

---

## Tech stack

**Backend** — Python 3.11 · FastAPI · SQLAlchemy 2.0 (async) · LangGraph · sentence-transformers · transformers · sse-starlette · Alembic · Redis (optional, for distributed rate limiting)
**Frontend** — Next.js 14 (App Router) · TypeScript · Tailwind · Motion · React Three Fiber · Recharts · Lenis
**Testing** — pytest · Vitest + Testing Library · Playwright (E2E)
**Infra** — Docker · Postgres + pgvector · Render · Vercel — all free tier

---

## Repository layout

```
sentinel-ai/
├── backend/
│   ├── app/
│   │   ├── agents/        LangGraph state, nodes, graph, streaming engine
│   │   ├── api/           targets · runs (SSE) · proxy · reports · dashboard · evals · auth
│   │   ├── guardrails/    input scanner · output scanner · policy
│   │   ├── ml/            injection classifier + evaluation
│   │   ├── rag/           threat catalog · ingest · hybrid retriever
│   │   ├── llm/           provider abstraction (Groq / Ollama / mock)
│   │   ├── core/          security · attack library
│   │   └── db/            SQLAlchemy models · async session · Alembic
│   ├── evals/             guardrail A/B · judge · RAG eval harnesses
│   └── tests/             pytest
├── frontend/
│   ├── app/               landing · dashboard · targets · runs · reports · proxy · model-card
│   ├── components/        hero (3D) · console · charts · finding cards · primitives
│   └── hooks/ · lib/      SSE stream hook · API client
├── docs/                  ARCHITECTURE · SECURITY · VIVA
├── docker-compose.yml · render.yaml · Makefile · .github/workflows/ci.yml
```

---

## Responsible use

⚖️ Sentinel is a **defensive** tool. Attacking a live third-party endpoint requires a per-target **consent** flag, an explicit **"Arm live attacks"** confirmation, and is rate-limited. Only test systems you are authorized to test.

---

<div align="center">

*Built as a production-grade portfolio piece for Applied AI / AI Security engineering.*
**LangGraph orchestration · hybrid-RAG-grounded findings · deployed injection classifier · measured guardrail A/B · fully free-tier.**

</div>
