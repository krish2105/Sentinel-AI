"""SQLAlchemy 2.0 async models.

Portable across SQLite (zero-setup local) and Postgres/pgvector (docker-compose,
Supabase). Embeddings are stored as JSON arrays so the same schema runs on both;
on Postgres a pgvector column + index can be layered on via migration for scale.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    api_key_hash: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    targets: Mapped[list["Target"]] = relationship(back_populates="user")


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    system_prompt: Mapped[str] = mapped_column(Text)
    endpoint_url: Mapped[str | None] = mapped_column(String, nullable=True)
    endpoint_headers_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    tools: Mapped[list] = mapped_column(JSON, default=list)  # [{name, risk}]
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["User"] = relationship(back_populates="targets")
    runs: Mapped[list["Run"]] = relationship(back_populates="target")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    target_id: Mapped[str] = mapped_column(ForeignKey("targets.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="queued")
    live_armed: Mapped[bool] = mapped_column(Boolean, default=False)
    selected_categories: Mapped[list] = mapped_column(JSON, default=list)
    posture_score: Mapped[int] = mapped_column(Integer, default=0)
    report: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    target: Mapped["Target"] = relationship(back_populates="runs")
    attacks: Mapped[list["Attack"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )

    @property
    def trace_url(self) -> str | None:
        """Deep-link to this run's Langfuse trace (None when tracing is off).

        The trace id is the run id (see engine.start_trace), so the link is
        derivable without storing anything extra.
        """
        from app.observability.tracing import trace_url as _trace_url

        return _trace_url(self.id)


class Attack(Base):
    __tablename__ = "attacks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), index=True)
    category: Mapped[str] = mapped_column(String)
    payload: Mapped[str] = mapped_column(Text)
    target_response: Mapped[str] = mapped_column(Text, default="")
    classifier_score: Mapped[float] = mapped_column(Float, default=0.0)
    verdict: Mapped[str] = mapped_column(String, default="SAFE")
    severity: Mapped[str] = mapped_column(String, default="LOW")
    owasp_ref: Mapped[str] = mapped_column(String, default="")
    citation: Mapped[str] = mapped_column(Text, default="")
    mitigation: Mapped[str] = mapped_column(Text, default="")
    blast_radius: Mapped[int] = mapped_column(Integer, default=1)
    # How the payload reached the target: "direct" (user turn) or "document"
    # (hidden inside retrieved/tool content — a truly-indirect injection).
    injection_vector: Mapped[str] = mapped_column(String, default="direct")
    # Number of conversation turns (>1 for multi-turn "crescendo" attacks).
    turns: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    run: Mapped["Run"] = relationship(back_populates="attacks")


class ProxyEvent(Base):
    __tablename__ = "proxy_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    direction: Mapped[str] = mapped_column(String)  # input | output
    action: Mapped[str] = mapped_column(String)  # PASS | BLOCK
    reason: Mapped[str] = mapped_column(Text, default="")
    owasp_ref: Mapped[str] = mapped_column(String, default="")
    payload_hash: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ToolApproval(Base):
    """A write/external tool call held for shadow-mode human approval (LLM06).

    When the guardrail policy flags a privileged tool call, it is parked here as
    ``pending`` instead of executing, until a human approves or denies it.
    """

    __tablename__ = "tool_approvals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    target_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    target_name: Mapped[str] = mapped_column(String, default="")
    tool_name: Mapped[str] = mapped_column(String)
    risk: Mapped[str] = mapped_column(String, default="write")  # write | external
    arguments: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    owasp_ref: Mapped[str] = mapped_column(String, default="LLM06")
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|approved|denied
    decided_by: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AuditLog(Base):
    """Append-only. Never updated or deleted in application code."""

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    actor: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ThreatChunk(Base):
    __tablename__ = "threat_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    catalog: Mapped[str] = mapped_column(String, index=True)
    ref_id: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String, default="")
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(JSON, default=list)  # float[384]
