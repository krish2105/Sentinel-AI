"""Red-team run lifecycle: create, stream (SSE), arm, status, history."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.engine import arm_run, run_engine
from app.api.deps import get_current_user
from app.api.schemas import AttackOut, RunCreate, RunOut
from app.core.security import audit
from app.db.models import Attack, Run, Target, User
from app.db.session import get_db

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunOut, status_code=201)
async def create_run(
    body: RunCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    target = await db.get(Target, body.target_id)
    if not target or target.user_id != user.id:
        raise HTTPException(status_code=404, detail="Target not found.")
    run = Run(
        user_id=user.id,
        target_id=target.id,
        status="queued",
        live_armed=body.live_armed,
        selected_categories=body.selected_categories,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    await audit(db, actor=user.email, action="run.create",
                meta={"run_id": run.id, "categories": body.selected_categories})
    return run


@router.get("/{run_id}/stream")
async def stream_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")

    async def event_generator():
        async for chunk in run_engine(run_id):
            # sse-starlette expects dict or str; we pre-format, so strip prefix.
            # chunk is "event: X\ndata: Y\n\n" -> parse back to fields.
            lines = chunk.strip().split("\n")
            event = "message"
            data = ""
            for line in lines:
                if line.startswith("event:"):
                    event = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    data = line[len("data:"):].strip()
            yield {"event": event, "data": data}

    return EventSourceResponse(event_generator())


@router.post("/{run_id}/arm", response_model=RunOut)
async def arm(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = await db.get(Run, run_id)
    if not run or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Run not found.")
    run.live_armed = True
    await db.commit()
    arm_run(run_id)
    await audit(db, actor=user.email, action="run.arm_live", meta={"run_id": run_id})
    await db.refresh(run)
    return run


@router.get("/{run_id}", response_model=RunOut)
async def get_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = await db.get(Run, run_id)
    if not run or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Run not found.")
    return run


@router.get("/{run_id}/attacks", response_model=list[AttackOut])
async def get_run_attacks(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = await db.get(Run, run_id)
    if not run or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Run not found.")
    rows = (
        await db.execute(select(Attack).where(Attack.run_id == run_id).order_by(Attack.created_at))
    ).scalars().all()
    return rows


@router.get("", response_model=list[RunOut])
async def list_runs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = (
        await db.execute(
            select(Run).where(Run.user_id == user.id).order_by(Run.started_at.desc()).limit(50)
        )
    ).scalars().all()
    return rows
