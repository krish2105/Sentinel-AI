"""Auth endpoints: register (issue API key) + token (JWT)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    RegisterRequest,
    RegisterResponse,
    TokenRequest,
    TokenResponse,
)
from app.core.security import (
    audit,
    create_access_token,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = (
        await db.execute(select(User).where(User.email == body.email))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")
    api_key = generate_api_key()
    user = User(email=body.email, api_key_hash=hash_api_key(api_key))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await audit(db, actor=user.email, action="register", meta={"user_id": user.id})
    return RegisterResponse(user_id=user.id, api_key=api_key)


@router.post("/token", response_model=TokenResponse)
async def token(body: TokenRequest, db: AsyncSession = Depends(get_db)):
    users = (await db.execute(select(User))).scalars().all()
    for user in users:
        if user.api_key_hash and verify_api_key(body.api_key, user.api_key_hash):
            return TokenResponse(access_token=create_access_token(user.id))
    raise HTTPException(status_code=401, detail="Invalid API key.")
