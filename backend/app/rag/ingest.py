"""Ingest the curated threat catalog into the ``threat_chunks`` table.

Chunks by risk-entry (each ``## REF | Title | category: X`` heading becomes one
chunk with metadata), embeds locally, and upserts. Idempotent: clears existing
chunks and re-inserts, so re-running is safe.

Run: ``python -m app.rag.ingest``
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import List

from sqlalchemy import delete

from app.db.models import ThreatChunk
from app.db.session import SessionLocal, init_db
from app.rag.embeddings import embed_many

SOURCES_DIR = Path(__file__).parent / "sources"

_HEADING = re.compile(r"^##\s+(?P<ref>[\w.\-]+)\s*\|\s*(?P<title>[^|]+?)\s*\|\s*category:\s*(?P<category>[\w_]+)\s*$")


def parse_markdown(path: Path, catalog: str) -> List[dict]:
    chunks: List[dict] = []
    current = None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _HEADING.match(line.strip())
        if m:
            if current:
                chunks.append(current)
            current = {
                "catalog": catalog,
                "ref_id": m.group("ref").strip(),
                "title": m.group("title").strip(),
                "category": m.group("category").strip(),
                "content": "",
            }
        elif current is not None:
            current["content"] += line + "\n"
    if current:
        chunks.append(current)
    # attach title into content for retrieval richness
    for c in chunks:
        c["content"] = f"{c['ref_id']} {c['title']}\n{c['content'].strip()}"
    return chunks


def collect_chunks() -> List[dict]:
    mapping = {
        "owasp_llm.md": "OWASP-LLM",
        "owasp_asi.md": "OWASP-ASI",
        "mitre_atlas.md": "MITRE-ATLAS",
    }
    all_chunks: List[dict] = []
    for filename, catalog in mapping.items():
        path = SOURCES_DIR / filename
        if path.exists():
            all_chunks.extend(parse_markdown(path, catalog))
    return all_chunks


async def ingest() -> int:
    await init_db()
    chunks = collect_chunks()
    if not chunks:
        print("No source chunks found.")
        return 0
    embeddings = embed_many([c["content"] for c in chunks])
    async with SessionLocal() as db:
        await db.execute(delete(ThreatChunk))
        for c, emb in zip(chunks, embeddings):
            db.add(
                ThreatChunk(
                    catalog=c["catalog"],
                    ref_id=c["ref_id"],
                    category=c["category"],
                    title=c["title"],
                    content=c["content"],
                    embedding=emb,
                )
            )
        await db.commit()
    print(f"Ingested {len(chunks)} threat chunks from {SOURCES_DIR}")
    return len(chunks)


if __name__ == "__main__":
    asyncio.run(ingest())
