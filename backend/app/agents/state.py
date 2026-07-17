"""Typed state for the adversarial red-team agent graph."""
from __future__ import annotations

import operator
from typing import Annotated, Any, List, Literal, TypedDict


class Attack(TypedDict, total=False):
    id: str
    category: str
    payload: str
    target_response: str
    classifier_score: float
    classifier_signals: List[str]
    verdict: Literal["SAFE", "BLOCKED", "LEAKED", "HIJACKED"]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    owasp_ref: str
    citation: str
    mitigation: str
    blast_radius: int


class AgentState(TypedDict, total=False):
    run_id: str
    target: dict  # {system_prompt, endpoint_url, tools, consent}
    selected_categories: List[str]
    live_armed: bool
    queue: List[dict]
    current: dict
    attacks: Annotated[List[Attack], operator.add]
    posture_score: int
    report: dict
    _trace: Any  # optional Langfuse trace handle; None when tracing is disabled
