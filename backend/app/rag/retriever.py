"""Hybrid retrieval + rerank over the threat catalog.

Pipeline:
  1. Dense retrieval — cosine over local embeddings.
  2. Lexical retrieval — token-overlap (BM25-ish) scoring.
  3. Fuse with Reciprocal Rank Fusion (RRF).
  4. Optional metadata filter by ``category`` so injection findings retrieve
     injection guidance.
  5. Rerank top-K with a local cross-encoder when heavy ML is enabled, else a
     deterministic lexical rerank.

Exposes ``retrieve(query, category, k)`` consumed by ``reporter`` and
``attacker``. Corpus is tiny (dozens of chunks), so in-process scoring is fast
and avoids any external vector-DB dependency at query time.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import ThreatChunk
from app.rag.embeddings import cosine, embed_one


@dataclass
class Chunk:
    ref_id: str
    catalog: str
    category: str
    title: str
    content: str
    score: float


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _lexical_score(query_tokens: Counter, doc_tokens: Counter) -> float:
    # Simple overlap-weighted score (BM25-lite): sum of min term freqs, length-normalized.
    common = query_tokens & doc_tokens
    if not common:
        return 0.0
    overlap = sum(common.values())
    return overlap / (1 + math.log(1 + sum(doc_tokens.values())))


_reranker = None
_use_reranker: Optional[bool] = None


def _load_reranker():
    global _reranker, _use_reranker
    if _use_reranker is not None:
        return
    if not settings.enable_heavy_ml:
        _use_reranker = False
        return
    try:  # pragma: no cover - heavy dependency
        from sentence_transformers import CrossEncoder

        _reranker = CrossEncoder(settings.reranker_model)
        _use_reranker = True
    except Exception:
        _use_reranker = False


async def retrieve(
    db: AsyncSession, query: str, category: Optional[str] = None, k: int = 4
) -> List[Chunk]:
    rows = (await db.execute(select(ThreatChunk))).scalars().all()
    if not rows:
        return []

    q_emb = embed_one(query)
    q_tokens = Counter(_tokenize(query))

    dense: List[tuple[float, ThreatChunk]] = []
    lexical: List[tuple[float, ThreatChunk]] = []
    for row in rows:
        d = cosine(q_emb, row.embedding) if row.embedding else 0.0
        l = _lexical_score(q_tokens, Counter(_tokenize(row.content)))
        dense.append((d, row))
        lexical.append((l, row))

    dense.sort(key=lambda x: x[0], reverse=True)
    lexical.sort(key=lambda x: x[0], reverse=True)

    # Reciprocal Rank Fusion
    rrf_k = 60
    fused: dict[str, float] = {}
    by_id: dict[str, ThreatChunk] = {}
    for rank, (_, row) in enumerate(dense):
        fused[row.id] = fused.get(row.id, 0) + 1 / (rrf_k + rank)
        by_id[row.id] = row
    for rank, (_, row) in enumerate(lexical):
        fused[row.id] = fused.get(row.id, 0) + 1 / (rrf_k + rank)
        by_id[row.id] = row

    # Metadata filter: prefer matching category, but keep others as backfill.
    ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)
    if category:
        matching = [(cid, s) for cid, s in ranked if by_id[cid].category == category]
        other = [(cid, s) for cid, s in ranked if by_id[cid].category != category]
        ranked = matching + other

    top = ranked[: max(k * 2, k)]

    # Rerank top candidates
    _load_reranker()
    candidates = [by_id[cid] for cid, _ in top]
    if _use_reranker and _reranker is not None and candidates:  # pragma: no cover
        pairs = [[query, c.content] for c in candidates]
        scores = _reranker.predict(pairs)
        order = sorted(range(len(candidates)), key=lambda i: scores[i], reverse=True)
        candidates = [candidates[i] for i in order]

    results = [
        Chunk(
            ref_id=c.ref_id,
            catalog=c.catalog,
            category=c.category,
            title=c.title,
            content=c.content,
            score=round(float(dict(top).get(c.id, 0.0)), 5),
        )
        for c in candidates[:k]
    ]
    return results


def first_citation(chunks: List[Chunk]) -> str:
    if not chunks:
        return ""
    c = chunks[0]
    snippet = " ".join(c.content.split())[:280]
    return f"[{c.catalog} {c.ref_id}] {snippet}"
