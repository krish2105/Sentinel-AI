.PHONY: help dev backend frontend db test eval ingest build clean install

help:
	@echo "Sentinel AI — make targets:"
	@echo "  make install   Install backend + frontend deps"
	@echo "  make db        Start Postgres+pgvector (docker compose)"
	@echo "  make backend   Run FastAPI (reload)"
	@echo "  make frontend  Run Next.js dev server"
	@echo "  make dev       db + backend + frontend info"
	@echo "  make ingest    Load the threat catalog into pgvector"
	@echo "  make test      Run backend pytest suite"
	@echo "  make eval      Run classifier + guardrail A/B + judge evals"
	@echo "  make build     Production build (frontend)"

install:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

db:
	docker compose up -d db

ingest:
	cd backend && python -m app.rag.ingest

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev: db
	@echo "DB up. Now run 'make backend' and 'make frontend' in separate shells."

test:
	cd backend && python -m pytest -q

eval:
	cd backend && python -m app.ml.eval_classifier && python -m evals.guardrail_ab && python -m evals.judge_eval

build:
	cd frontend && npm run build

clean:
	rm -f backend/sentinel.db backend/test_sentinel.db
	docker compose down -v
