# Architecture

## System overview

```
┌────────────────────────────────────────────────────────────────────┐
│  Frontend — Next.js 14 (Vercel)                                     │
│  landing · dashboard · targets · runs/[id] · reports/[id] · proxy   │
└───────────────┬────────────────────────────────────────────────────┘
                │  REST + Server-Sent Events (via Next rewrite /api → backend)
┌───────────────▼────────────────────────────────────────────────────┐
│  Backend — FastAPI (Render free)                                    │
│                                                                     │
│  /targets  CRUD                                                     │
│  /runs     ──► LangGraph engine ──► LLM client (Groq / Ollama / mock)│
│                    │                                                 │
│                    ├── hybrid RAG retriever ──► pgvector catalog     │
│                    └── deberta injection classifier (local)         │
│  /proxy    ──► Guardrail pipeline (input scan → target → output scan)│
│  /reports  scored report + PDF/JSON export                          │
│  /dashboard aggregate stats                                         │
│                                                                     │
│  core: auth (JWT + hashed API keys) · rate limit · append-only audit│
└───────────────┬────────────────────────────────────────────────────┘
                │
┌───────────────▼─────────────┐
│  Postgres + pgvector         │  users · targets · runs · attacks
│  (Supabase / Render / local) │  proxy_events · audit_log · threat_chunks
└──────────────────────────────┘
```

## The agent graph (LangGraph)

An **adversarial multi-agent system** built as a `StateGraph`. State accumulates a
list of `Attack` records; nodes are pure async functions shared between the
canonical graph (`agents/graph.py`) and the streaming engine (`agents/engine.py`).

```
START → orchestrator
orchestrator ─┬─(live & not armed)─► human_gate ──► orchestrator
              ├─(attacks remain)───► attacker
              └─(queue empty)──────► reporter ──► END

attacker → classifier_node → target_harness → judge → orchestrator   (loop)
```

| Node | Role |
|---|---|
| **orchestrator** | Builds the attack queue from `attack_library.py`; routes to human-gate / attacker / reporter. |
| **attacker** | Generates a concrete adversarial payload per category (LLM + templates + obfuscation variants), grounded by RAG retrieval of the real vulnerability class. |
| **classifier_node** | Deterministic ML gate — runs the payload through the injection classifier (no LLM). |
| **target_harness** | Runs the payload against the sim target (LLM + system prompt) or a live endpoint (consent + rate-limited). |
| **judge** | Isolated LLM-as-judge; strict rubric → structured JSON verdict + severity, amplified by blast radius. |
| **reporter** | Maps findings to OWASP refs via RAG, attaches citations + mitigations, computes the weighted posture score. |

**Human-in-the-loop.** The graph uses a LangGraph `interrupt_before` checkpoint on
`human_gate`. The streaming engine mirrors this with an `asyncio.Event` released by
`POST /runs/{id}/arm`, so a run pauses for the frontend “Arm live attacks”
confirmation and then resumes.

**Streaming.** Every node transition (planned → payload → classified → responded →
judged) is emitted over SSE, which is what makes the live console feel alive.

## Two-tier detection

1. **Deterministic ML classifier** (fast, cheap first layer) — `deberta-v3-prompt-injection-v2`, or a transparent heuristic detector (documented injection signatures + NFKC + homoglyph folding) when heavy ML is disabled.
2. **LLM-as-judge** (reasoning second layer) — reasons about novel/obfuscated attacks the classifier misses. Runs in an isolated context that never obeys instructions inside the payload.

This trades cost for coverage: the classifier handles the common case at ~0 cost; the judge covers the long tail.

## RAG & threat knowledge

- **Corpus** — curated original markdown summaries of OWASP LLM Top 10, OWASP Agentic (ASI) Top 10, and MITRE ATLAS, in `backend/app/rag/sources/`.
- **Chunk** by risk entry with `{catalog, ref_id, category}` metadata.
- **Embed** locally (`bge-small`, or feature-hashed fallback).
- **Retrieve** hybrid: dense cosine + lexical, fused with **Reciprocal Rank Fusion**, filtered by category, reranked (cross-encoder or lexical).
- Consumed by both `attacker` (to target the real vuln class) and `reporter` (to cite it).

## Data model

`users · targets · runs · attacks · proxy_events · audit_log · threat_chunks`
(see `backend/app/db/models.py`). Alembic migrations under
`backend/app/db/migrations/`. Portable across SQLite and Postgres; embeddings are
stored as JSON arrays so one schema runs on both.

## Deployment

### Backend → Render (free)
1. Push to GitHub.
2. Render → New → Blueprint → select the repo (uses `render.yaml`).
3. In the created Postgres, run `CREATE EXTENSION IF NOT EXISTS vector;`.
4. Set `CORS_ORIGINS` to your Vercel URL. Optionally set `GROQ_API_KEY`.

### Frontend → Vercel (free)
1. Import the repo, root directory `frontend/`.
2. Set `NEXT_PUBLIC_API_URL` = your Render backend URL.
3. Deploy.

### Local
`docker compose up -d` (Postgres+pgvector + backend) then `cd frontend && npm run dev`.
