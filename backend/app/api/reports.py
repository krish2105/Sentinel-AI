"""Scored report fetch + export (JSON / PDF)."""
from __future__ import annotations

import io
import json

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import Attack, Run, Target, User
from app.db.session import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


async def _load(run_id: str, db: AsyncSession, user: User):
    run = await db.get(Run, run_id)
    if not run or run.user_id != user.id:
        raise HTTPException(status_code=404, detail="Run not found.")
    attacks = (
        await db.execute(select(Attack).where(Attack.run_id == run_id).order_by(Attack.created_at))
    ).scalars().all()
    target = await db.get(Target, run.target_id)
    return run, attacks, target


def _serialize(run, attacks, target) -> dict:
    return {
        "run_id": run.id,
        "status": run.status,
        "posture_score": run.posture_score,
        "trace_url": run.trace_url,
        "target": {
            "name": target.name if target else "",
            "tools": target.tools if target else [],
        },
        "report": run.report,
        "attacks": [
            {
                "id": a.id, "category": a.category, "payload": a.payload,
                "target_response": a.target_response, "classifier_score": a.classifier_score,
                "verdict": a.verdict, "severity": a.severity, "owasp_ref": a.owasp_ref,
                "citation": a.citation, "mitigation": a.mitigation,
                "blast_radius": a.blast_radius,
                "injection_vector": getattr(a, "injection_vector", "direct"),
                "turns": getattr(a, "turns", 1),
            }
            for a in attacks
        ],
    }


@router.get("/{run_id}")
async def get_report(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run, attacks, target = await _load(run_id, db, user)
    return JSONResponse(_serialize(run, attacks, target))


@router.get("/{run_id}/json")
async def export_json(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run, attacks, target = await _load(run_id, db, user)
    data = json.dumps(_serialize(run, attacks, target), indent=2)
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="sentinel-report-{run_id[:8]}.json"'},
    )


@router.get("/{run_id}/pdf")
async def export_pdf(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run, attacks, target = await _load(run_id, db, user)
    data = _serialize(run, attacks, target)
    try:
        pdf_bytes = _render_pdf(data)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="sentinel-report-{run_id[:8]}.pdf"'},
        )
    except Exception:
        # Fallback: printable HTML (browser -> Save as PDF). Keeps export working
        # even when reportlab is not installed.
        return HTMLResponse(_render_html(data))


def _render_pdf(data: dict) -> bytes:  # pragma: no cover - optional dep
    """A styled, multi-section PDF via reportlab platypus (not plaintext lines)."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    INK = colors.HexColor("#0C1220")
    TEAL = colors.HexColor("#0D9488")
    MUTED = colors.HexColor("#5A6478")
    LINE = colors.HexColor("#D6DEEA")
    SEV_COLOR = {
        "CRITICAL": colors.HexColor("#DC2637"),
        "HIGH": colors.HexColor("#E4632B"),
        "MEDIUM": colors.HexColor("#B47806"),
        "LOW": colors.HexColor("#5A6478"),
    }
    VERDICT_COLOR = {
        "HIJACKED": colors.HexColor("#DC2637"),
        "LEAKED": colors.HexColor("#B47806"),
        "BLOCKED": TEAL,
        "SAFE": TEAL,
    }

    rep = data.get("report", {}) or {}
    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9, textColor=INK, leading=12)
    small = ParagraphStyle("small", parent=body, fontSize=7.5, textColor=MUTED, leading=9)
    # NOTE: reportlab Paragraph styles don't auto-scale `leading` (line height)
    # when you bump `fontSize` above the parent style's — the parent Title
    # style is sized for 18pt with leading=22, so a naive fontSize=48 override
    # leaves a 22pt-tall line box for a 48pt glyph, and it overflows into
    # whatever paragraph comes next. Always set leading explicitly (~1.15x
    # fontSize) alongside any fontSize override on a heading-derived style.
    h1 = ParagraphStyle("h1", parent=styles["Title"], fontSize=22, leading=26, textColor=INK, spaceAfter=2)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, textColor=INK, spaceBefore=10, spaceAfter=4)
    score_style = ParagraphStyle(
        "score", parent=styles["Title"], fontSize=48, leading=56,
        textColor=TEAL, alignment=TA_CENTER, spaceAfter=4,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=18 * mm, bottomMargin=16 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm, title="Sentinel AI Security Report",
    )
    story = []

    # Helvetica has no emoji glyphs — a literal shield emoji renders as tofu
    # boxes in the PDF, so the title is plain text here (fine elsewhere: HTML/UI
    # render it via system emoji fonts, only this reportlab path can't).
    story.append(Paragraph("Sentinel AI — Security Report", h1))
    story.append(Paragraph(
        f"Target: <b>{_esc(data['target']['name'])}</b> · Run {_esc(str(data['run_id'])[:8])}", body))
    story.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceBefore=6, spaceAfter=10))

    # Posture scorecard + summary metrics.
    story.append(Paragraph(f"{data['posture_score']}<font size=16>/100</font>", score_style))
    story.append(Paragraph("SECURITY POSTURE SCORE", ParagraphStyle(
        "cap", parent=small, alignment=TA_CENTER, spaceAfter=8)))

    summary = [
        ["Total attacks", str(rep.get("total_attacks", len(data["attacks"])))],
        ["Successful exploits", str(rep.get("successful_attacks", 0))],
        ["Attack-success rate", f"{rep.get('attack_success_rate', 0) * 100:.0f}%"],
        ["Blast radius", f"{rep.get('blast_radius', 1)}/5"],
    ]
    st = Table(summary, colWidths=[70 * mm, 100 * mm])
    st.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), INK),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(st)

    # Findings table.
    story.append(Paragraph("Findings", h2))
    rows = [["Sev", "OWASP", "Category", "Verdict", "Vector"]]
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for i, a in enumerate(data["attacks"], start=1):
        rows.append([
            a["severity"], a["owasp_ref"], _esc(a["category"]), a["verdict"],
            "document" if a.get("injection_vector") == "document" else "direct",
        ])
        style_cmds.append(("TEXTCOLOR", (0, i), (0, i), SEV_COLOR.get(a["severity"], MUTED)))
        style_cmds.append(("TEXTCOLOR", (3, i), (3, i), VERDICT_COLOR.get(a["verdict"], MUTED)))
        style_cmds.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
    ft = Table(rows, colWidths=[20 * mm, 20 * mm, 62 * mm, 26 * mm, 24 * mm], repeatRows=1)
    ft.setStyle(TableStyle(style_cmds))
    story.append(ft)

    # Per-finding mitigations.
    story.append(Paragraph("Recommended mitigations", h2))
    for a in data["attacks"]:
        story.append(Paragraph(
            f"<b>[{a['severity']}] {_esc(a['category'])}</b> ({a['owasp_ref']})", body))
        story.append(Paragraph(_esc(a.get("mitigation", "")), small))
        story.append(Spacer(1, 4))

    story.append(HRFlowable(width="100%", thickness=0.5, color=LINE, spaceBefore=8, spaceAfter=4))
    story.append(Paragraph(
        "Generated by Sentinel AI · defensive LLM red-team + runtime guardrail platform.", small))

    doc.build(story)
    return buf.getvalue()


def _esc(text: str) -> str:
    """Escape text for reportlab Paragraph mini-markup."""
    return (
        str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def _render_html(data: dict) -> str:
    rows = "".join(
        f"<tr><td>{a['severity']}</td><td>{a['owasp_ref']}</td>"
        f"<td>{a['category']}</td><td>{a['verdict']}</td>"
        f"<td>{a['mitigation']}</td></tr>"
        for a in data["attacks"]
    )
    rep = data.get("report", {}) or {}
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Sentinel Report {data['run_id'][:8]}</title>
<style>body{{font-family:system-ui;margin:40px;color:#0A0B0F}}
h1{{color:#0d9488}}table{{border-collapse:collapse;width:100%}}
td,th{{border:1px solid #ccc;padding:8px;text-align:left;font-size:13px}}
.score{{font-size:42px;font-weight:800;color:#0d9488}}</style></head>
<body><h1>Sentinel AI — Security Report</h1>
<p>Target: <b>{data['target']['name']}</b></p>
<div class="score">{data['posture_score']}/100</div>
<p>Attack success rate: {rep.get('attack_success_rate',0)*100:.0f}% · Total attacks: {rep.get('total_attacks',0)}</p>
<table><tr><th>Severity</th><th>OWASP</th><th>Category</th><th>Verdict</th><th>Mitigation</th></tr>
{rows}</table>
<p style="margin-top:24px;color:#666">Tip: Use your browser's Print → Save as PDF.</p>
</body></html>"""
