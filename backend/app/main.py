"""Sentinel AI — FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, dashboard, evals, proxy, reports, runs, targets
from app.config import settings
from app.db.session import init_db
from app.llm.client import get_llm

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
)
logger = logging.getLogger("sentinel")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Best-effort: ensure the threat catalog is present for grounding.
    try:
        from sqlalchemy import func, select
        from app.db.models import ThreatChunk
        from app.db.session import SessionLocal
        from app.rag.ingest import ingest

        async with SessionLocal() as db:
            count = (await db.execute(select(func.count()).select_from(ThreatChunk))).scalar()
        if not count:
            await ingest()
    except Exception as exc:  # pragma: no cover
        logger.warning(f"threat catalog ingest skipped: {exc}")

    logger.info(f"Sentinel AI started (LLM provider: {get_llm().provider})")
    yield
    logger.info("Sentinel AI shutting down")


app = FastAPI(
    title="Sentinel AI",
    description="LLM & AI-Agent Security Red-Team + Runtime Guardrail Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Never leak internals to the client."""
    logger.error(f"unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
    )


@app.get("/health", tags=["meta"])
async def health():
    from app.observability.tracing import enabled as tracing_enabled

    return {
        "status": "ok",
        "service": settings.app_name,
        "llm_provider": get_llm().provider,
        "heavy_ml": settings.enable_heavy_ml,
        "database": "postgres" if settings.is_postgres else "sqlite",
        "tracing": tracing_enabled(),
    }


@app.get("/", tags=["meta"])
async def root():
    return {
        "name": "Sentinel AI",
        "pitch": "Point Sentinel at any LLM app; it red-teams the target against "
                 "the OWASP LLM/Agentic Top 10 and ships a runtime guardrail firewall.",
        "docs": "/docs",
        "health": "/health",
    }


for r in (
    auth.router,
    targets.router,
    runs.router,
    proxy.router,
    reports.router,
    dashboard.router,
    evals.router,
):
    app.include_router(r)
