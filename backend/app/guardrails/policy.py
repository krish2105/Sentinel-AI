"""Least-privilege + shadow-mode policy for tool calls and known-bad patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

# Known exfiltration / egress patterns denied outright at the input layer.
_EXFIL_PATTERNS = [
    re.compile(r"\bforward all\b.*\bto\b", re.I),
    re.compile(r"\bemail\b.*@\w+\.\w+", re.I),
    re.compile(r"send .*(database|records|secrets|keys)", re.I),
    re.compile(r"exfiltrat", re.I),
    re.compile(r"https?://[^\s]*(evil|malware|attacker|exfil)", re.I),
]

RISK_ORDER = {"read": 0, "write": 1, "external": 2}


@dataclass
class ToolDecision:
    allowed: bool
    requires_approval: bool
    reason: str
    owasp_ref: str = ""


def check_exfil(text: str) -> Optional[str]:
    for pat in _EXFIL_PATTERNS:
        if pat.search(text):
            return f"Matched exfiltration pattern: {pat.pattern}"
    return None


def evaluate_tool_call(
    tool_name: str,
    declared_tools: List[dict],
    shadow_mode: bool,
) -> ToolDecision:
    """Enforce the target's declared allow-list + least privilege.

    write/external tools require shadow-mode human approval (LLM06 / ASI02).
    """
    match = next((t for t in declared_tools if t.get("name") == tool_name), None)
    if match is None:
        return ToolDecision(
            allowed=False,
            requires_approval=False,
            reason=f"Tool '{tool_name}' is not on the declared allow-list.",
            owasp_ref="LLM06",
        )
    risk = (match.get("risk") or "read").lower()
    if risk in ("write", "external"):
        if shadow_mode:
            return ToolDecision(
                allowed=False,
                requires_approval=True,
                reason=f"'{tool_name}' is a {risk} tool; shadow-mode approval required.",
                owasp_ref="LLM06",
            )
        return ToolDecision(
            allowed=True,
            requires_approval=False,
            reason=f"'{tool_name}' ({risk}) permitted (shadow mode off).",
            owasp_ref="LLM06",
        )
    return ToolDecision(
        allowed=True, requires_approval=False, reason=f"'{tool_name}' (read) permitted."
    )


def blast_radius(tools: List[dict]) -> int:
    """1-5 score of how far a compromise could propagate given declared tools."""
    if not tools:
        return 1
    max_risk = max((RISK_ORDER.get((t.get("risk") or "read").lower(), 0) for t in tools), default=0)
    count = len(tools)
    return min(5, 1 + max_risk * 2 + (1 if count >= 3 else 0))
