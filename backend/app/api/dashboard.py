"""Aggregate dashboard stats: posture trend, failure clusters, firewall activity."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.attack_library import CATEGORIES
from app.db.models import Attack, ProxyEvent, Run, User
from app.db.session import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    runs = (
        await db.execute(
            select(Run).where(Run.user_id == user.id).order_by(Run.started_at)
        )
    ).scalars().all()

    completed = [r for r in runs if r.status == "completed"]
    posture_trend = [
        {
            "run_id": r.id[:8],
            "date": r.started_at.isoformat(),
            "posture": r.posture_score,
            "asr": (r.report or {}).get("attack_success_rate", 0),
        }
        for r in completed
    ]

    # Failure clustering: per-category success counts (for the D3 scatter).
    attack_rows = (
        await db.execute(
            select(Attack).join(Run, Attack.run_id == Run.id).where(Run.user_id == user.id)
        )
    ).scalars().all()

    clusters: dict[str, dict] = {}
    for a in attack_rows:
        c = clusters.setdefault(
            a.category,
            {"category": a.category, "label": CATEGORIES.get(a.category).label if a.category in CATEGORIES else a.category,
             "owasp_ref": a.owasp_ref, "total": 0, "failed": 0, "avg_classifier": 0.0, "_scores": []},
        )
        c["total"] += 1
        c["_scores"].append(a.classifier_score)
        if a.verdict in ("LEAKED", "HIJACKED"):
            c["failed"] += 1
    cluster_list = []
    for c in clusters.values():
        scores = c.pop("_scores")
        c["avg_classifier"] = round(sum(scores) / len(scores), 3) if scores else 0
        c["fail_rate"] = round(c["failed"] / c["total"], 3) if c["total"] else 0
        cluster_list.append(c)

    # Firewall activity
    events = (
        await db.execute(
            select(ProxyEvent).where(ProxyEvent.user_id == user.id).order_by(ProxyEvent.created_at.desc()).limit(50)
        )
    ).scalars().all()
    blocks = sum(1 for e in events if e.action == "BLOCK")

    return {
        "totals": {
            "runs": len(runs),
            "completed": len(completed),
            "attacks": len(attack_rows),
            "avg_posture": round(sum(r.posture_score for r in completed) / len(completed), 1)
            if completed else 0,
            "firewall_blocks": blocks,
        },
        "posture_trend": posture_trend,
        "failure_clusters": cluster_list,
        "recent_activity": [
            {
                "direction": e.direction, "action": e.action, "reason": e.reason,
                "owasp_ref": e.owasp_ref, "at": e.created_at.isoformat(),
            }
            for e in events[:15]
        ],
    }
