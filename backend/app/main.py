"""Sentinel AI — FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import approvals, auth, dashboard, evals, proxy, reports, runs, targets
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

# --- Security hardening middleware -----------------------------------------
# A security product must not ship an unhardened surface: enforce host
# allow-listing, cap request bodies, and set defensive response headers.
if settings.trusted_hosts and settings.trusted_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject oversized request bodies before they reach handlers (DoS guard)."""

    def __init__(self, app, max_bytes: int) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl is not None:
            try:
                if int(cl) > self.max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request body too large."},
                    )
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length."})
        return await call_next(request)


_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    # API returns JSON only; a strict CSP is safe and high-signal here.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach defensive response headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for k, v in _SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        # HSTS only over HTTPS deployments (harmless behind Render/Vercel TLS).
        if settings.environment == "production":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
            )
        return response


if settings.security_headers_enabled:
    app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_request_bytes)


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
    approvals.router,
    reports.router,
    dashboard.router,
    evals.router,
):
    app.include_router(r)
