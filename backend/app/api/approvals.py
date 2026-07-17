"""Shadow-mode approval queue for privileged (write/external) tool calls.

The guardrail policy (``evaluate_tool_call``) decides whether a tool call is on
the target's allow-list and whether it needs human approval. Instead of letting
a write/external call execute, we park it here as ``pending`` and surface it for
a human to approve or deny — the interactive half of least-privilege (LLM06).
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, rate_limit
from app.api.schemas import (
    ApprovalDecision,
    ApprovalOut,
    ToolCallRequest,
    ToolCallResponse,
)
from app.core.security import audit
from app.db.models import Target, ToolApproval, User
from app.db.session import get_db
from app.guardrails.policy import evaluate_tool_call

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("/tool-call", response_model=ToolCallResponse, dependencies=[Depends(rate_limit)])
async def submit_tool_call(
    body: ToolCallRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit an agent tool call to the guardrail policy.

    - not on allow-list  -> denied
    - write/external + shadow_mode -> parked pending human approval
    - otherwise -> executed (simulated)
    """
    declared = [t.model_dump() for t in body.tools]
    target_name = ""
    target_id = body.target_id

    # If a registered target is referenced, use ITS declared tools as the truth.
    if target_id:
        target = await db.get(Target, target_id)
        if not target or target.user_id != user.id:
            raise HTTPException(status_code=404, detail="Target not found.")
        declared = target.tools or []
        target_name = target.name

    decision = evaluate_tool_call(body.tool_name, declared, body.shadow_mode)

    # Publish to the live firewall feed (best-effort).
    from app.api.proxy import _publish

    if not decision.allowed and not decision.requires_approval:
        await _publish({
            "direction": "tool", "action": "DENY",
            "owasp_ref": decision.owasp_ref, "reason": decision.reason,
        })
        await audit(db, actor=user.email, action="tool.deny",
                    meta={"tool": body.tool_name, "reason": decision.reason})
        return ToolCallResponse(
            status="denied", allowed=False, requires_approval=False,
            reason=decision.reason, owasp_ref=decision.owasp_ref,
        )

    if decision.requires_approval:
        risk = next(
            (t.get("risk", "write") for t in declared if t.get("name") == body.tool_name),
            "write",
        )
        approval = ToolApproval(
            user_id=user.id, target_id=target_id, target_name=target_name,
            tool_name=body.tool_name, risk=risk, arguments=body.arguments,
            reason=decision.reason, owasp_ref=decision.owasp_ref, status="pending",
        )
        db.add(approval)
        await db.commit()
        await db.refresh(approval)
        await _publish({
            "direction": "tool", "action": "HELD",
            "owasp_ref": decision.owasp_ref,
            "reason": f"{body.tool_name} held for approval",
        })
        await audit(db, actor=user.email, action="tool.hold",
                    meta={"tool": body.tool_name, "approval_id": approval.id})
        return ToolCallResponse(
            status="pending_approval", allowed=False, requires_approval=True,
            reason=decision.reason, owasp_ref=decision.owasp_ref,
            approval_id=approval.id,
        )

    await audit(db, actor=user.email, action="tool.execute",
                meta={"tool": body.tool_name})
    return ToolCallResponse(
        status="executed", allowed=True, requires_approval=False,
        reason=decision.reason, owasp_ref=decision.owasp_ref,
    )


@router.get("", response_model=list[ApprovalOut])
async def list_approvals(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(ToolApproval).where(ToolApproval.user_id == user.id)
    if status:
        q = q.where(ToolApproval.status == status)
    q = q.order_by(ToolApproval.created_at.desc()).limit(100)
    rows = (await db.execute(q)).scalars().all()
    return rows


@router.post("/{approval_id}/decision", response_model=ApprovalOut)
async def decide(
    approval_id: str,
    body: ApprovalDecision,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    approval = await db.get(ToolApproval, approval_id)
    if not approval or approval.user_id != user.id:
        raise HTTPException(status_code=404, detail="Approval not found.")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail="Already decided.")

    from datetime import datetime, timezone

    approval.status = "approved" if body.decision == "approve" else "denied"
    approval.decided_by = user.email
    approval.decided_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(approval)

    from app.api.proxy import _publish

    await _publish({
        "direction": "tool", "action": approval.status.upper(),
        "owasp_ref": approval.owasp_ref,
        "reason": f"{approval.tool_name} {approval.status} by human",
    })
    await audit(db, actor=user.email, action=f"tool.{approval.status}",
                meta={"approval_id": approval_id, "tool": approval.tool_name})
    return approval
