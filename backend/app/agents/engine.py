"""Streaming red-team engine.

Drives the same node functions as the LangGraph assembly but yields an event for
every node transition so the frontend console feels alive, and persists each
finalized attack to the DB as it lands. Supports the human-in-the-loop gate via
an asyncio arming event.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import nodes
from app.agents.state import AgentState
from app.core.attack_library import CATEGORIES, LIVE_SENSITIVE_CATEGORIES, build_queue
from app.db.models import Attack as AttackModel
from app.db.models import Run, Target
from app.db.session import SessionLocal

# In-process registry of live runs so /arm can release the gate.
_ARM_EVENTS: Dict[str, asyncio.Event] = {}


def arm_run(run_id: str) -> bool:
    ev = _ARM_EVENTS.get(run_id)
    if ev:
        ev.set()
        return True
    return False


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def run_engine(run_id: str) -> AsyncGenerator[str, None]:
    """Async generator of SSE-formatted strings for a run."""
    # Load run + target and build initial state.
    async with SessionLocal() as db:
        run = await db.get(Run, run_id)
        if run is None:
            yield _sse("error", {"message": "run not found"})
            return
        target_obj = await db.get(Target, run.target_id)
        if target_obj is None:
            yield _sse("error", {"message": "target not found"})
            return
        target = {
            "system_prompt": target_obj.system_prompt,
            "endpoint_url": target_obj.endpoint_url,
            "tools": target_obj.tools or [],
            "consent": target_obj.consent,
            "name": target_obj.name,
        }
        queue = build_queue(run.selected_categories or ["all"])
        run.status = "running"
        await db.commit()

    state: AgentState = {
        "run_id": run_id,
        "target": target,
        "selected_categories": run.selected_categories or ["all"],
        "live_armed": run.live_armed,
        "queue": queue,
        "attacks": [],
    }

    total = len(queue)
    yield _sse("run_started", {"run_id": run_id, "total": total, "target": target["name"]})

    # Human-in-the-loop gate: if a live endpoint + sensitive attacks and not armed.
    needs_gate = bool(target.get("endpoint_url")) and not state["live_armed"]
    if needs_gate:
        ev = asyncio.Event()
        _ARM_EVENTS[run_id] = ev
        yield _sse("human_gate", {
            "run_id": run_id,
            "message": "Live endpoint detected. Arm live attacks to proceed.",
        })
        try:
            await asyncio.wait_for(ev.wait(), timeout=300)
            state["live_armed"] = True
            async with SessionLocal() as db:
                run = await db.get(Run, run_id)
                run.live_armed = True
                await db.commit()
            yield _sse("armed", {"run_id": run_id})
        except asyncio.TimeoutError:
            yield _sse("gate_timeout", {"run_id": run_id, "message": "Proceeding in sim mode."})
        finally:
            _ARM_EVENTS.pop(run_id, None)

    index = 0
    for item in queue:
        index += 1
        state["current"] = item
        cat = CATEGORIES[item["category"]]

        yield _sse("attack_planned", {
            "index": index, "category": item["category"],
            "label": cat.label, "owasp_ref": item["owasp_ref"],
        })

        async with SessionLocal() as db:
            # attacker
            upd = await nodes.attacker_node(state, db)
            state["current"] = upd["current"]
            yield _sse("payload_generated", {
                "index": index, "category": item["category"],
                "payload": state["current"]["payload"],
            })
            await asyncio.sleep(0.05)

            # classifier
            upd = nodes.classifier_node(state)
            state["current"] = upd["current"]
            yield _sse("classified", {
                "index": index,
                "classifier_score": state["current"]["classifier_score"],
                "signals": state["current"].get("classifier_signals", []),
            })
            await asyncio.sleep(0.05)

            # target
            upd = await nodes.target_harness_node(state, db)
            state["current"] = upd["current"]
            yield _sse("target_responded", {
                "index": index,
                "response": state["current"]["target_response"][:1200],
            })
            await asyncio.sleep(0.05)

            # judge
            upd = await nodes.judge_node(state)
            state["current"] = upd["current"]
            upd = await nodes.enrich_citation(state, db)
            state["current"] = upd["current"]
            attack = state["current"]

            # persist
            model = AttackModel(
                run_id=run_id,
                category=attack["category"],
                payload=attack["payload"],
                target_response=attack["target_response"],
                classifier_score=attack.get("classifier_score", 0.0),
                verdict=attack.get("verdict", "SAFE"),
                severity=attack.get("severity", "LOW"),
                owasp_ref=attack.get("owasp_ref", ""),
                citation=attack.get("citation", ""),
                mitigation=attack.get("mitigation", ""),
                blast_radius=attack.get("blast_radius", 1),
            )
            db.add(model)
            await db.commit()

        state["attacks"].append(attack)
        yield _sse("verdict", {
            "index": index,
            "id": model.id,
            "category": attack["category"],
            "owasp_ref": attack["owasp_ref"],
            "verdict": attack["verdict"],
            "severity": attack["severity"],
            "classifier_score": attack.get("classifier_score", 0.0),
            "citation": attack.get("citation", ""),
            "mitigation": attack.get("mitigation", ""),
            "blast_radius": attack.get("blast_radius", 1),
            "progress": round(index / total, 3),
        })
        await asyncio.sleep(0.08)

    # reporter
    score = nodes.compute_posture(state["attacks"])
    report = _build_report(state, score)
    async with SessionLocal() as db:
        run = await db.get(Run, run_id)
        run.status = "completed"
        run.posture_score = score
        run.report = report
        run.finished_at = datetime.now(timezone.utc)
        await db.commit()

    yield _sse("run_completed", {
        "run_id": run_id, "posture_score": score, "report": report,
    })


def _build_report(state: AgentState, score: int) -> dict:
    attacks = state["attacks"]
    by_ref: Dict[str, dict] = {}
    counts = {"SAFE": 0, "BLOCKED": 0, "LEAKED": 0, "HIJACKED": 0}
    sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for a in attacks:
        counts[a.get("verdict", "SAFE")] = counts.get(a.get("verdict", "SAFE"), 0) + 1
        if a.get("verdict") in ("LEAKED", "HIJACKED"):
            sev_counts[a.get("severity", "LOW")] += 1
        ref = a.get("owasp_ref", "")
        entry = by_ref.setdefault(ref, {"ref": ref, "total": 0, "failed": 0})
        entry["total"] += 1
        if a.get("verdict") in ("LEAKED", "HIJACKED"):
            entry["failed"] += 1
    success = counts["LEAKED"] + counts["HIJACKED"]
    return {
        "posture_score": score,
        "target": state["target"].get("name", "target"),
        "total_attacks": len(attacks),
        "successful_attacks": success,
        "attack_success_rate": round(success / len(attacks), 3) if attacks else 0,
        "verdict_counts": counts,
        "severity_counts": sev_counts,
        "owasp_coverage": list(by_ref.values()),
        "blast_radius": nodes.blast_radius(state["target"].get("tools", [])),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
