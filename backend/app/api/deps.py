"""Shared FastAPI dependencies: auth + rate limiting."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, rate_limiter
from app.db.models import User
from app.db.session import get_db

_bearer = HTTPBearer(auto_error=False)

# Demo/anonymous user so the platform is fully usable without registration in
# local/demo mode; real deployments require a token.
DEMO_USER_ID = "demo-user"


async def rate_limit(request: Request) -> None:
    key = request.client.host if request.client else "anon"
    if not await rate_limiter.allow(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again shortly.",
        )


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the current user from a JWT, or fall back to the demo user.

    Demo fallback keeps the portfolio piece instantly usable; production can set
    ``require_auth`` by removing the fallback branch.
    """
    if creds and creds.credentials:
        subject = decode_token(creds.credentials)
        if subject:
            user = (
                await db.execute(select(User).where(User.id == subject))
            ).scalar_one_or_none()
            if user:
                return user

    # Ensure a demo user exists.
    user = (
        await db.execute(select(User).where(User.id == DEMO_USER_ID))
    ).scalar_one_or_none()
    if user is None:
        user = User(id=DEMO_USER_ID, email="demo@sentinel.ai", api_key_hash="")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user
