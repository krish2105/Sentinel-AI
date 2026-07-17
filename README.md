<div align="center">

# 🛡️ Sentinel AI

### LLM & AI-Agent Security — Adversarial Red-Team + Runtime Guardrail Platform

*Point Sentinel at any LLM app or agent; it launches an adversarial attack swarm, scores the target against the OWASP LLM & Agentic Top 10, and ships a runtime firewall that blocks prompt-injection and unsafe actions in production.*

**Free-tier native · No paid API keys required · Runs offline**

</div>

---

## What it does

Sentinel AI is two products in one platform:

1. **🎯 Red-Team Engine** — a LangGraph adversarial multi-agent system that generates and fires attacks at a target LLM/agent, judges whether each attack succeeded, and produces a scored report mapped to the OWASP LLM Top 10 (2026) and OWASP Agentic Top 10 — with a grounded citation for every finding.

2. **🔥 Guardrail Proxy** — a drop-in runtime firewall that sits in front of any LLM endpoint: it screens inputs and outputs with a two-tier detector (deterministic ML classifier + isolated LLM firewall), enforces least-privilege on agent tools, and runs high-risk actions in shadow mode pending human approval.

### Headline numbers (measured, not asserted)

| Metric | Result | Source |
|---|---|---|
| Attack-success-rate reduction (proxy OFF → ON) | **83.3%** | `evals/guardrail_ab.json` |
| Injection classifier precision / recall / FPR | **1.00 / 0.75 / 0.00** | `evals/classifier_report.json` |
| LLM-as-judge agreement on golden set | **100%** | `evals/judge_eval.json` |
| RAG context precision @3 (OWASP mapping) | **100%** | `evals/rag_eval.json` |

---

## Architecture at a glance

```
Frontend (Next.js 14 / Vercel)  ── REST + SSE ──►  FastAPI (Render free)
  · 3D hero "Shield & Swarm"                        ├── /runs  → LangGraph graph ──► LLM (Groq free / Ollama / mock)
  · live red-team console (SSE)                     │             ├── hybrid RAG ──► pgvector threat catalog
  · OWASP grid · posture gauge                      │             └── deberta injection classifier
  · blast-radius diagram · charts                   ├── /proxy → guardrail pipeline (input scan → target → output scan)
  · firewall playground                             └── Postgres (runs, findings, audit log)
```

The **agent graph**: `orchestrator → [human_gate] → attacker → classifier → target_harness → judge → orchestrator …→ reporter`.
See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/SECURITY.md`](docs/SECURITY.md).

### Design principle: graceful degradation

Every heavy/external dependency has a deterministic local fallback, so the whole platform runs with **zero setup and zero keys** — and upgrades to production-grade when provisioned:

| Component | Full mode | Zero-setup fallback |
|---|---|---|
| LLM inference | Groq free tier / Ollama | Deterministic mock engine |
| Injection classifier | `deberta-v3-prompt-injection-v2` | Transparent heuristic detector (regex + homoglyph folding) |
| Embeddings | `bge-small-en-v1.5` | Feature-hashed embeddings |
| Reranker | `bge-reranker-base` | Lexical rerank |
| Vector + relational DB | Postgres + pgvector | SQLite |

---

## Quickstart

### Fastest path (zero dependencies, SQLite + mock engine)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.rag.ingest            # load the threat catalog
uvicorn app.main:app --reload       # http://localhost:8000  (docs at /docs)

# Frontend (new shell)
cd frontend
npm install
npm run dev                         # http://localhost:3000
```

Open http://localhost:3000 → **Targets → New target → “Prefill a sample vulnerable agent” → Red-team**.

### With Postgres + pgvector (docker-compose)

```bash
docker compose up -d                 # Postgres+pgvector + backend (auto-ingests)
cd frontend && npm install && npm run dev
```

### Enable real models & real LLM attacks (still free)

```bash
# In backend/.env:
GROQ_API_KEY=gsk_...                 # free key from https://console.groq.com
ENABLE_HEAVY_ML=true                 # then: pip install -r requirements-ml.txt
```

### Tests & evals

```bash
make test    # pytest — graph, scanners, tool allow-list, proxy A/B, API
make eval    # classifier + guardrail A/B + judge + RAG eval reports
```

---

## Feature tour

- **Target Registry** — register a system prompt + optional live endpoint + declared tools (each tagged `read`/`write`/`external`). No endpoint → Sentinel simulates one.
- **Live Red-Team Console** — attacks stream in over SSE with animated verdict chips, a typing terminal log, a filling OWASP grid, and a posture gauge that counts up on completion.
- **Human-in-the-loop gate** — live-endpoint attacks pause on a LangGraph interrupt until you click **Arm live attacks**.
- **Scored Report** — per-attack verdict/severity/OWASP citation/payload/mitigation, an aggregate posture score, verdict & severity charts, a blast-radius diagram, and JSON/PDF export.
- **Firewall Playground** — send a malicious prompt with guardrails ON (watch the `BLOCKED` stamp + OWASP ref) vs OFF (watch it leak). The contrast *is* the demo.
- **Dashboard** — posture trend, per-category failure-cluster scatter, and a live firewall-activity feed.

---

## Deployment (free tier)

- **Backend → Render** — the repo ships a [`render.yaml`](render.yaml) blueprint (free web service + free Postgres). Enable pgvector with `CREATE EXTENSION vector;`.
- **Frontend → Vercel** — import the `frontend/` directory; set `NEXT_PUBLIC_API_URL` to your Render URL.
- Cold-start note: Render free instances sleep; `/health` wakes them.

Full walkthrough in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Tech stack

**Backend** — Python 3.11, FastAPI, SQLAlchemy 2.0 (async), LangGraph, sentence-transformers, transformers, sse-starlette, Alembic.
**Frontend** — Next.js 14 (App Router), TypeScript, Tailwind, Motion, React Three Fiber, Recharts, Lenis.
**Infra** — Docker, Postgres+pgvector, Render, Vercel — all free tier.

---

## Repository layout

```
sentinel-ai/
├── backend/          FastAPI app, LangGraph agents, RAG, ML, guardrails, evals, tests
├── frontend/         Next.js app — landing (3D hero), console, report, proxy, dashboard
├── docs/             ARCHITECTURE · SECURITY (OWASP mapping) · VIVA (interview Q&A)
├── docker-compose.yml · render.yaml · Makefile
```

> ⚖️ **Responsible use.** Sentinel is a *defensive* tool. Attacking third-party systems requires a consent flag + explicit "arm" confirmation, and is rate-limited. Only test systems you are authorized to test.
