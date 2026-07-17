"""Output scan: PII/secret leakage, system-prompt-leak, toxicity.

Layer [4] of the Guardrail Proxy. Redacts or blocks responses that leak
sensitive data or the system prompt (LLM02 / LLM07).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import List, Optional

from app.config import settings

# PII / secret detectors (presidio-style regex layer)
_PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "api_key": re.compile(r"\b(sk|pk|api|key|token)[_\-][A-Za-z0-9]{8,}\b", re.I),
    "aws_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
}

_TOXIC_MARKERS = re.compile(
    r"\b(kill yourself|how to make a bomb|as dan|bypass a filter)\b", re.I
)


@dataclass
class OutputScanResult:
    action: str  # "PASS" | "BLOCK" | "REDACT"
    reason: str
    owasp_ref: str
    redacted: str
    findings: List[str] = field(default_factory=list)


def _detect_pii(text: str) -> List[str]:
    found = []
    for name, pat in _PII_PATTERNS.items():
        if pat.search(text):
            found.append(name)
    return found


def _redact(text: str) -> str:
    for name, pat in _PII_PATTERNS.items():
        text = pat.sub(f"[REDACTED:{name}]", text)
    return text


def _prompt_leak_ratio(response: str, system_prompt: str) -> float:
    if not system_prompt:
        return 0.0
    # Longest-common-substring style similarity of significant chunks.
    sp = system_prompt.strip().lower()
    resp = response.lower()
    ratio = SequenceMatcher(None, sp[:400], resp[:800]).ratio()
    # Also catch verbatim substring leakage of a distinctive slice.
    if len(sp) > 40 and sp[:40] in resp:
        return max(ratio, 0.9)
    return ratio


def scan_output(response: str, system_prompt: str = "") -> OutputScanResult:
    findings: List[str] = []

    pii = _detect_pii(response)
    if pii:
        findings.extend([f"pii:{p}" for p in pii])

    leak_ratio = _prompt_leak_ratio(response, system_prompt)
    if leak_ratio >= settings.prompt_leak_similarity:
        findings.append(f"system-prompt-leak:{leak_ratio:.2f}")
        return OutputScanResult(
            action="BLOCK",
            reason=f"Output resembles the protected system prompt (similarity {leak_ratio:.2f}).",
            owasp_ref="LLM07",
            redacted="[BLOCKED: system-prompt leakage prevented]",
            findings=findings,
        )

    if _TOXIC_MARKERS.search(response):
        findings.append("toxicity")
        return OutputScanResult(
            action="BLOCK",
            reason="Output contains unsafe / jailbroken content.",
            owasp_ref="LLM05",
            redacted="[BLOCKED: unsafe content]",
            findings=findings,
        )

    if pii:
        return OutputScanResult(
            action="REDACT",
            reason=f"Redacted sensitive data: {', '.join(pii)}.",
            owasp_ref="LLM02",
            redacted=_redact(response),
            findings=findings,
        )

    return OutputScanResult(
        action="PASS",
        reason="No sensitive data or leakage detected.",
        owasp_ref="",
        redacted=response,
        findings=findings,
    )
