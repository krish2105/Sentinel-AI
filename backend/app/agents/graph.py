"""LangGraph StateGraph assembly.

When ``langgraph`` is installed this builds a real ``StateGraph`` with the exact
nodes and conditional edges from the architecture spec, including a ``human_gate``
interrupt for the "Arm live attacks" confirmation and a checkpointer so runs
survive reconnects.

The streaming :mod:`app.agents.engine` drives the same node functions directly so
we can emit every transition over SSE and persist per-attack — but this module is
the canonical graph definition and is import-safe even without langgraph.
"""
from __future__ import annotations

from typing import Callable, Optional

from app.agents.state import AgentState


def build_graph(db_factory: Callable):  # pragma: no cover - exercised when langgraph present
    """Assemble and compile the LangGraph StateGraph.

    Returns the compiled graph, or ``None`` if langgraph is unavailable (the
    engine fallback is used instead).
    """
    try:
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.graph import END, START, StateGraph
    except Exception:
        return None

    from app.agents import nodes

    async def orchestrator(state: AgentState) -> dict:
        queue = state.get("queue", [])
        if not queue:
            return {"current": {}}
        current, rest = queue[0], queue[1:]
        return {"current": current, "queue": rest}

    def route_after_orchestrator(state: AgentState) -> str:
        queue_has = bool(state.get("current"))
        if not queue_has and not state.get("queue"):
            return "reporter"
        # live + not armed → human gate
        cur = state.get("current", {})
        needs_live = bool(state["target"].get("endpoint_url"))
        if needs_live and not state.get("live_armed"):
            return "human_gate"
        return "attacker"

    async def attacker(state: AgentState) -> dict:
        async with db_factory() as db:
            return await nodes.attacker_node(state, db)

    def classifier(state: AgentState) -> dict:
        return nodes.classifier_node(state)

    async def harness(state: AgentState) -> dict:
        async with db_factory() as db:
            return await nodes.target_harness_node(state, db)

    async def judge(state: AgentState) -> dict:
        result = await nodes.judge_node(state)
        state.update(result)
        async with db_factory() as db:
            enriched = await nodes.enrich_citation(state, db)
        item = enriched["current"]
        return {"attacks": [item], "current": {}}

    async def human_gate(state: AgentState) -> dict:
        # Interrupt point; resumed when live_armed is set to True.
        return {}

    async def reporter(state: AgentState) -> dict:
        score = nodes.compute_posture(state.get("attacks", []))
        return {"posture_score": score, "report": {"posture_score": score}}

    g = StateGraph(AgentState)
    g.add_node("orchestrator", orchestrator)
    g.add_node("attacker", attacker)
    g.add_node("classifier_node", classifier)
    g.add_node("target_harness", harness)
    g.add_node("judge", judge)
    g.add_node("human_gate", human_gate)
    g.add_node("reporter", reporter)

    g.add_edge(START, "orchestrator")
    g.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {"human_gate": "human_gate", "attacker": "attacker", "reporter": "reporter"},
    )
    g.add_edge("human_gate", "orchestrator")
    g.add_edge("attacker", "classifier_node")
    g.add_edge("classifier_node", "target_harness")
    g.add_edge("target_harness", "judge")
    g.add_edge("judge", "orchestrator")
    g.add_edge("reporter", END)

    return g.compile(checkpointer=MemorySaver(), interrupt_before=["human_gate"])
