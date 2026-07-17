"""Target registry CRUD."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import func

from app.api.deps import get_current_user
from app.api.schemas import TargetCreate, TargetOut
from app.core.security import audit, encrypt_headers, normalize_unicode
from app.db.models import Run, Target, User
from app.db.session import get_db

router = APIRouter(prefix="/targets", tags=["targets"])


@router.post("", response_model=TargetOut, status_code=201)
async def create_target(
    body: TargetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Endpoint headers hold live-target API keys — encrypt at rest (Fernet).
    headers_enc = encrypt_headers(body.endpoint_headers)
    target = Target(
        user_id=user.id,
        name=body.name[:120],
        system_prompt=normalize_unicode(body.system_prompt)[:20000],
        endpoint_url=str(body.endpoint_url) if body.endpoint_url else None,
        endpoint_headers_enc=headers_enc,
        tools=[t.model_dump() for t in body.tools],
        consent=body.consent,
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)
    await audit(db, actor=user.email, action="target.create", meta={"target_id": target.id})
    return target


@router.get("", response_model=list[TargetOut])
async def list_targets(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = (
        await db.execute(
            select(Target).where(Target.user_id == user.id).order_by(Target.created_at.desc())
        )
    ).scalars().all()
    return rows


@router.get("/{target_id}", response_model=TargetOut)
async def get_target(
    target_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    target = await db.get(Target, target_id)
    if not target or target.user_id != user.id:
        raise HTTPException(status_code=404, detail="Target not found.")
    return target


@router.delete("/{target_id}", status_code=204)
async def delete_target(
    target_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    target = await db.get(Target, target_id)
    if not target or target.user_id != user.id:
        raise HTTPException(status_code=404, detail="Target not found.")

    # Run.target_id is NOT NULL, and the relationship has no cascade config,
    # so deleting a target with existing runs would otherwise crash mid-commit
    # (SQLAlchemy's default cascade tries to null out target_id on each Run,
    # violating the not-null constraint). Refuse instead — for a security
    # tool, silently orphaning or losing historical run data is the wrong
    # failure mode anyway; the user should delete the runs first if they
    # really want the target gone.
    run_count = (
        await db.execute(select(func.count()).where(Run.target_id == target_id))
    ).scalar_one()
    if run_count:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot delete '{target.name}': {run_count} run(s) reference it. "
                "Delete those runs first if you want to remove this target."
            ),
        )

    await db.delete(target)
    await db.commit()
    await audit(db, actor=user.email, action="target.delete", meta={"target_id": target_id})
    return None
