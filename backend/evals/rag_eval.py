"""RAG retrieval eval — context precision for OWASP mapping.

For each attack category we check whether the retriever surfaces the correct
OWASP/ATLAS entry in its top-k, so reported citations are grounded. A lightweight
stand-in for RAGAS context-precision that runs with zero heavy deps. Writes
``evals/rag_eval.json``. Run: ``python -m evals.rag_eval``.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.core.attack_library import CATEGORIES
from app.db.session import init_db
from app.rag.ingest import ingest
from app.rag.retriever import retrieve
from app.db.session import SessionLocal
from sqlalchemy import func, select
from app.db.models import ThreatChunk


async def evaluate() -> dict:
    await init_db()
    async with SessionLocal() as db:
        count = (await db.execute(select(func.count()).select_from(ThreatChunk))).scalar()
    if not count:
        await ingest()

    hits = 0
    per_category = []
    async with SessionLocal() as db:
        for key, cat in CATEGORIES.items():
            chunks = await retrieve(db, cat.generation_hint, category=key, k=3)
            top_refs = [c.ref_id for c in chunks]
            # Correct if the canonical OWASP ref appears in the top-k.
            hit = cat.owasp_ref in top_refs
            hits += 1 if hit else 0
            per_category.append(
                {
                    "category": key,
                    "expected_ref": cat.owasp_ref,
                    "retrieved": top_refs,
                    "hit": hit,
                }
            )

    precision = round(hits / len(CATEGORIES), 4)
    return {
        "n": len(CATEGORIES),
        "context_precision_at_3": precision,
        "hits": hits,
        "per_category": per_category,
    }


def main() -> None:
    report = asyncio.run(evaluate())
    out = Path(__file__).resolve().parent / "rag_eval.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "per_category"}, indent=2))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
