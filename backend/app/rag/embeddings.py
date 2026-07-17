"""Local embeddings with a deterministic fallback.

Primary: ``sentence-transformers`` (``BAAI/bge-small-en-v1.5``) — local, no key.
Fallback (when heavy ML is disabled/unavailable): a deterministic hashing
embedding (feature-hashed token n-grams into 384 dims, L2-normalized). The
fallback is not as semantically rich but is fully offline, dependency-free, and
sufficient for the small, well-separated threat corpus — so retrieval works
everywhere.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import List, Optional

from app.config import settings

_DIM = settings.embedding_dim
_model = None
_use_st: Optional[bool] = None


def _load_st():
    global _model, _use_st
    if _use_st is not None:
        return
    if not settings.enable_heavy_ml:
        _use_st = False
        return
    try:  # pragma: no cover - heavy dependency
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.embedding_model)
        _use_st = True
    except Exception:
        _use_st = False


def _tokens(text: str) -> List[str]:
    text = text.lower()
    words = re.findall(r"[a-z0-9]+", text)
    grams = list(words)
    grams += [f"{a}_{b}" for a, b in zip(words, words[1:])]  # bigrams
    return grams


def _hash_embed(text: str) -> List[float]:
    vec = [0.0] * _DIM
    for tok in _tokens(text):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        idx = h % _DIM
        sign = 1.0 if (h >> 8) & 1 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed_one(text: str) -> List[float]:
    _load_st()
    if _use_st and _model is not None:  # pragma: no cover
        return _model.encode(text, normalize_embeddings=True).tolist()
    return _hash_embed(text)


def embed_many(texts: List[str]) -> List[List[float]]:
    _load_st()
    if _use_st and _model is not None:  # pragma: no cover
        return [v.tolist() for v in _model.encode(texts, normalize_embeddings=True)]
    return [_hash_embed(t) for t in texts]


def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    return dot  # vectors are L2-normalized
