"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---
class RegisterRequest(BaseModel):
    email: EmailStr


class RegisterResponse(BaseModel):
    user_id: str
    api_key: str
    message: str = "Store this API key securely — it is shown only once."


class TokenRequest(BaseModel):
    api_key: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Targets ---
class ToolSpec(BaseModel):
    name: str
    risk: str = Field(default="read", pattern="^(read|write|external)$")


class TargetCreate(BaseModel):
    name: str
    system_prompt: str
    endpoint_url: Optional[str] = None
    endpoint_headers: Optional[dict] = None
    tools: List[ToolSpec] = Field(default_factory=list)
    consent: bool = False


class TargetOut(BaseModel):
    id: str
    name: str
    system_prompt: str
    endpoint_url: Optional[str]
    tools: List[dict]
    consent: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Runs ---
class RunCreate(BaseModel):
    target_id: str
    selected_categories: List[str] = Field(default_factory=lambda: ["all"])
    live_armed: bool = False


class RunOut(BaseModel):
    id: str
    target_id: str
    status: str
    live_armed: bool
    posture_score: int
    selected_categories: List[str]
    started_at: datetime
    finished_at: Optional[datetime]
    trace_url: Optional[str] = None

    class Config:
        from_attributes = True


class AttackOut(BaseModel):
    id: str
    category: str
    payload: str
    target_response: str
    classifier_score: float
    verdict: str
    severity: str
    owasp_ref: str
    citation: str
    mitigation: str
    blast_radius: int
    injection_vector: str = "direct"
    turns: int = 1

    class Config:
        from_attributes = True


# --- Proxy ---
class ProxyChatRequest(BaseModel):
    message: str
    system_prompt: str = "You are a helpful assistant."
    guardrails: bool = True
    tools: List[ToolSpec] = Field(default_factory=list)
    shadow_mode: bool = True
    # When set, the proxy pulls the system prompt + declared tools from a
    # registered target instead of the free-form fields (unified playground).
    target_id: Optional[str] = None
    # Optional untrusted context (a "retrieved document" / tool output). When
    # guardrails are on, it is scanned like user input (indirect-injection guard).
    document: Optional[str] = None


class ProxyChatResponse(BaseModel):
    blocked: bool
    stage: str  # input | output | none
    action: str  # PASS | BLOCK | REDACT
    reason: str
    owasp_ref: str
    response: str
    classifier_score: float
    input_scan: dict
    output_scan: dict
    latency_ms: int


class ProxyABResponse(BaseModel):
    """Before/after result: the same attack with guardrails off vs on."""

    message: str
    without_guardrails: ProxyChatResponse
    with_guardrails: ProxyChatResponse
    neutralized: bool  # leaked when off, stopped when on
    owasp_ref: str


# --- Shadow-mode tool approvals ---
class ToolCallRequest(BaseModel):
    """A simulated agent tool call submitted to the guardrail policy."""

    tool_name: str
    arguments: str = ""
    tools: List[ToolSpec] = Field(default_factory=list)
    shadow_mode: bool = True
    target_id: Optional[str] = None


class ToolCallResponse(BaseModel):
    status: str  # executed | pending_approval | denied
    allowed: bool
    requires_approval: bool
    reason: str
    owasp_ref: str
    approval_id: Optional[str] = None


class ApprovalOut(BaseModel):
    id: str
    target_id: Optional[str]
    target_name: str
    tool_name: str
    risk: str
    arguments: str
    reason: str
    owasp_ref: str
    status: str
    created_at: datetime
    decided_at: Optional[datetime]

    class Config:
        from_attributes = True


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern="^(approve|deny)$")


# --- Run-to-run comparison ---
class RunComparison(BaseModel):
    run_id: str
    previous_run_id: Optional[str]
    has_previous: bool
    posture: int
    previous_posture: Optional[int]
    posture_delta: Optional[int]  # positive = improved
    asr: float
    previous_asr: Optional[float]
    asr_delta: Optional[float]  # positive = worse
    regressed_categories: List[str]  # passed before, failing now
    fixed_categories: List[str]  # failed before, passing now
    regression: bool  # posture dropped or a new category started failing
    summary: str
