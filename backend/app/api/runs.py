"""Red-team run lifecycle: create, stream (SSE), arm, status, history."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.engine import arm_run, run_engine
from app.api.deps import get_current_user
from app.api.schemas import AttackOut, RunComparison, RunCreate, RunOut
from app.core.security import audit
from app.db.models import Attack, Run, Target, User
from app.db.session import get_db

router = APIRouter(prefix="/runs", tags=["runs"])


async def _failed_categories(db: AsyncSession, run_id: str) -> set[str]:
    """Categories with at least one successful exploit in a run."""
    rows = (
        await db.execute(select(Attack).where(Attack.run_id == run_id))
    ).scalars().all()
    return {a.category for a in rows if a.verdict in ("LEAKED", "HIJACKED")}


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


@router.get("/{run_id}/compare", response_model=RunComparison)
async def compare_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Compare a run to the previous completed run of the same target.

    Surfaces posture/ASR deltas and, crucially, *regressions* — categories that
    were resisted before but are now exploited — so a run can gate a release.
    """
    run = await db.get(Run, run_id)
    if not run or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Run not found.")

    prev = (
        await db.execute(
            select(Run)
            .where(
                Run.target_id == run.target_id,
                Run.user_id == user.id,
                Run.status == "completed",
                Run.started_at < run.started_at,
                Run.id != run.id,
            )
            .order_by(Run.started_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    asr = float((run.report or {}).get("attack_success_rate", 0.0))
    if prev is None:
        return RunComparison(
            run_id=run.id, previous_run_id=None, has_previous=False,
            posture=run.posture_score, previous_posture=None, posture_delta=None,
            asr=asr, previous_asr=None, asr_delta=None,
            regressed_categories=[], fixed_categories=[], regression=False,
            summary="No previous run for this target — this is the baseline.",
        )

    now_failed = await _failed_categories(db, run.id)
    prev_failed = await _failed_categories(db, prev.id)
    regressed = sorted(now_failed - prev_failed)
    fixed = sorted(prev_failed - now_failed)
    prev_asr = float((prev.report or {}).get("attack_success_rate", 0.0))
    posture_delta = run.posture_score - prev.posture_score
    regression = posture_delta < 0 or bool(regressed)

    if regression:
        summary = (
            f"Regression: posture {posture_delta:+d}"
            + (f", new failing: {', '.join(regressed)}" if regressed else "")
            + "."
        )
    elif fixed or posture_delta > 0:
        summary = (
            f"Improved: posture {posture_delta:+d}"
            + (f", fixed: {', '.join(fixed)}" if fixed else "")
            + "."
        )
    else:
        summary = "No change since the previous run."

    return RunComparison(
        run_id=run.id, previous_run_id=prev.id, has_previous=True,
        posture=run.posture_score, previous_posture=prev.posture_score,
        posture_delta=posture_delta, asr=asr, previous_asr=prev_asr,
        asr_delta=round(asr - prev_asr, 3),
        regressed_categories=regressed, fixed_categories=fixed,
        regression=regression, summary=summary,
    )


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
