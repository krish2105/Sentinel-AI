"""Security primitives: API-key hashing, JWT, rate limiting, audit, sanitize.

Sentinel protects itself with the same defense-in-depth it enforces on targets:
secrets never logged, append-only audit trail, per-key rate limits, and unicode
normalization to defeat hidden-character attacks.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import unicodedata
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, Optional

import jwt
from cryptography.fernet import Fernet, InvalidToken
from passlib.context import CryptContext

from app.config import settings
from app.db.models import AuditLog
from sqlalchemy.ext.asyncio import AsyncSession

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Secret encryption at rest (Fernet) -------------------------------------
def _fernet() -> Fernet:
    """Build a Fernet cipher from the configured key.

    Uses ``header_encryption_key`` when set; otherwise deterministically derives
    a key from ``jwt_secret`` so the platform still encrypts secrets at rest in
    zero-config local mode. Set a dedicated key in production.
    """
    raw = settings.header_encryption_key or settings.jwt_secret
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> Optional[str]:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        return None


def encrypt_headers(headers: Optional[dict]) -> Optional[str]:
    """Encrypt a headers dict to an opaque token for storage."""
    if not headers:
        return None
    return encrypt_secret(json.dumps(headers))


def decrypt_headers(token: Optional[str]) -> dict:
    """Decrypt a stored headers token back to a dict.

    Tolerates legacy plaintext-JSON rows written before encryption landed, so an
    existing DB keeps working after upgrade.
    """
    if not token:
        return {}
    plain = decrypt_secret(token)
    if plain is None:
        # Legacy fallback: value predates encryption and is raw JSON.
        try:
            return json.loads(token)
        except (json.JSONDecodeError, TypeError):
            return {}
    try:
        return json.loads(plain)
    except (json.JSONDecodeError, TypeError):
        return {}


# --- API keys ---------------------------------------------------------------
def generate_api_key() -> str:
    return "snt_" + secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    return _pwd.hash(api_key)


def verify_api_key(api_key: str, hashed: str) -> bool:
    try:
        return _pwd.verify(api_key, hashed)
    except Exception:
        return False


def payload_hash(text: str) -> str:
    """Non-reversible hash for audit logging payloads without storing them raw."""
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()[:32]


# --- JWT --------------------------------------------------------------------
def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> str | None:
    try:
        data = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return data.get("sub")
    except Exception:
        return None


# --- Rate limiting (sliding window; Redis-backed when configured) -----------
class RateLimiter:
    """Sliding-window limiter.

    Uses Redis (a per-key sorted set of request timestamps) when ``REDIS_URL`` is
    configured, so limits hold across horizontally-scaled instances. Falls back
    to a per-process in-memory window otherwise — the zero-setup default. The
    interface is async so the Redis path never blocks the event loop.
    """

    def __init__(self, per_minute: int, redis_url: str = "") -> None:
        self.per_minute = per_minute
        self.redis_url = redis_url
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._redis = None
        self._redis_failed = False

    async def _client(self):
        if not self.redis_url or self._redis_failed:
            return None
        if self._redis is None:
            try:
                import redis.asyncio as aioredis

                self._redis = aioredis.from_url(
                    self.redis_url, encoding="utf-8", decode_responses=True
                )
            except Exception:
                # Redis unavailable/misconfigured — degrade to in-memory.
                self._redis_failed = True
                return None
        return self._redis

    def _allow_memory(self, key: str, now: float) -> bool:
        window = self._hits[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.per_minute:
            return False
        window.append(now)
        return True

    async def allow(self, key: str) -> bool:
        now = time.time()
        client = await self._client()
        if client is None:
            return self._allow_memory(key, now)
        try:
            redis_key = f"ratelimit:{key}"
            cutoff = now - 60
            async with client.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(redis_key, 0, cutoff)
                pipe.zadd(redis_key, {f"{now}:{secrets.token_hex(4)}": now})
                pipe.zcard(redis_key)
                pipe.expire(redis_key, 60)
                _, _, count, _ = await pipe.execute()
            return count <= self.per_minute
        except Exception:
            # Any Redis error at request time: fail open to in-memory, don't 500.
            self._redis_failed = True
            return self._allow_memory(key, now)


rate_limiter = RateLimiter(settings.rate_limit_per_minute, settings.redis_url)


# --- Input hardening --------------------------------------------------------
def normalize_unicode(text: str) -> str:
    """NFKC-normalize and strip zero-width/format chars (hidden-instruction defense)."""
    text = unicodedata.normalize("NFKC", text)
    return "".join(c for c in text if unicodedata.category(c) != "Cf")


def sanitize_upload(text: str, max_len: int = 200_000) -> str:
    text = normalize_unicode(text)[:max_len]
    # Strip common active-content markers from uploaded documents.
    for marker in ("<script", "javascript:", "data:text/html"):
        text = text.replace(marker, "[stripped]")
    return text


# --- Audit log (append-only) ------------------------------------------------
async def audit(db: AsyncSession, actor: str, action: str, meta: dict) -> None:
    entry = AuditLog(actor=actor, action=action, meta=meta)
    db.add(entry)
    await db.commit()


def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
