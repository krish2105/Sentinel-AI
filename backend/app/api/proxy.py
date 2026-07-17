"""Guardrail Proxy: input scan -> target -> output scan, with activity feed.

This is the runtime firewall. The same endpoint powers the before/after demo:
call with ``guardrails=false`` to see an attack leak, ``guardrails=true`` to see
it blocked.
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, rate_limit
from app.api.schemas import (
    ProxyABResponse,
    ProxyChatRequest,
    ProxyChatResponse,
)
from app.core.security import audit, payload_hash
from app.db.models import ProxyEvent, User
from app.db.session import get_db
from app.guardrails.input_scanner import scan_input
from app.guardrails.output_scanner import scan_output
from app.llm.client import get_llm

router = APIRouter(prefix="/proxy", tags=["proxy"])

# In-process pub/sub for the live firewall activity feed.
_subscribers: list[asyncio.Queue] = []


async def _publish(event: dict) -> None:
    for q in list(_subscribers):
        try:
            q.put_nowait(event)
        except Exception:
            pass


@router.post("/chat", response_model=ProxyChatResponse, dependencies=[Depends(rate_limit)])
async def proxy_chat(
    body: ProxyChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await _run_proxy(body, db, user)


@router.post("/ab", response_model=ProxyABResponse, dependencies=[Depends(rate_limit)])
async def proxy_ab(
    body: ProxyChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Run the SAME attack twice — guardrails OFF then ON — and return both.

    This is the marquee before/after demo the eval script only proved offline:
    the contrast (leaked vs blocked) is now a first-class product surface.
    """
    off = await _run_proxy(
        body.model_copy(update={"guardrails": False}), db, user
    )
    on = await _run_proxy(
        body.model_copy(update={"guardrails": True}), db, user
    )
    # "Neutralized" = the attack got through unguarded but was stopped when armed.
    neutralized = (not off.blocked) and (on.blocked or on.action == "REDACT")
    return ProxyABResponse(
        message=body.message,
        without_guardrails=off,
        with_guardrails=on,
        neutralized=neutralized,
        owasp_ref=on.owasp_ref or off.owasp_ref,
    )


async def _run_proxy(
    body: ProxyChatRequest, db: AsyncSession, user: User
) -> ProxyChatResponse:
    start = time.time()
    llm = get_llm()

    input_scan = {"action": "PASS", "reason": "guardrails disabled", "owasp_ref": "",
                  "classifier_score": 0.0, "layer": "off", "signals": []}
    output_scan = {"action": "PASS", "reason": "guardrails disabled", "owasp_ref": "",
                   "findings": []}

    # [2] INPUT SCAN
    if body.guardrails:
        result = await scan_input(body.message)
        input_scan = {
            "action": result.action, "reason": result.reason,
            "owasp_ref": result.owasp_ref, "classifier_score": result.classifier_score,
            "layer": result.layer, "signals": result.signals,
        }
        if result.action == "BLOCK":
            await _log_event(db, user, "input", "BLOCK", result.reason,
                             result.owasp_ref, body.message)
            await _publish({"direction": "input", "action": "BLOCK",
                            "owasp_ref": result.owasp_ref, "reason": result.reason})
            return ProxyChatResponse(
                blocked=True, stage="input", action="BLOCK", reason=result.reason,
                owasp_ref=result.owasp_ref,
                response="🛡️ BLOCKED at input by Sentinel guardrail.",
                classifier_score=result.classifier_score,
                input_scan=input_scan, output_scan=output_scan,
                latency_ms=int((time.time() - start) * 1000),
            )

    # [3] TARGET call
    raw = await llm.complete(
        [
            {"role": "system", "content": body.system_prompt},
            {"role": "user", "content": body.message},
        ],
        purpose="target",
    )

    final = raw
    stage = "none"
    action = "PASS"
    reason = "clear"
    owasp_ref = ""

    # [4] OUTPUT SCAN
    if body.guardrails:
        out = scan_output(raw, system_prompt=body.system_prompt)
        output_scan = {"action": out.action, "reason": out.reason,
                       "owasp_ref": out.owasp_ref, "findings": out.findings}
        final = out.redacted
        if out.action in ("BLOCK", "REDACT"):
            stage, action, reason, owasp_ref = "output", out.action, out.reason, out.owasp_ref
            await _log_event(db, user, "output", out.action, out.reason, out.owasp_ref, raw)
            await _publish({"direction": "output", "action": out.action,
                            "owasp_ref": out.owasp_ref, "reason": out.reason})

    blocked = action == "BLOCK"
    return ProxyChatResponse(
        blocked=blocked, stage=stage, action=action, reason=reason, owasp_ref=owasp_ref,
        response=final, classifier_score=input_scan["classifier_score"],
        input_scan=input_scan, output_scan=output_scan,
        latency_ms=int((time.time() - start) * 1000),
    )


async def _log_event(db, user, direction, action, reason, owasp_ref, payload):
    event = ProxyEvent(
        user_id=user.id, direction=direction, action=action, reason=reason,
        owasp_ref=owasp_ref, payload_hash=payload_hash(payload),
    )
    db.add(event)
    await db.commit()
    await audit(db, actor=user.email, action=f"proxy.{action.lower()}",
                meta={"direction": direction, "owasp_ref": owasp_ref})


@router.get("/activity/stream")
async def activity_stream():
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.append(q)

    async def gen() -> AsyncGenerator[dict, None]:
        try:
            yield {"event": "connected", "data": json.dumps({"ok": True})}
            while True:
                event = await q.get()
                yield {"event": "firewall_event", "data": json.dumps(event)}
        finally:
            if q in _subscribers:
                _subscribers.remove(q)

    return EventSourceResponse(gen())
