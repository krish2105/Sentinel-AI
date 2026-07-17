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
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 25 * mm

    c.setFont("Helvetica-Bold", 20)
    c.drawString(20 * mm, y, "Sentinel AI — Security Report")
    y -= 12 * mm
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, y, f"Target: {data['target']['name']}")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Posture Score: {data['posture_score']}/100")
    y -= 7 * mm
    rep = data.get("report", {}) or {}
    c.drawString(20 * mm, y, f"Attack Success Rate: {rep.get('attack_success_rate', 0)*100:.0f}%")
    y -= 12 * mm

    c.setFont("Helvetica-Bold", 13)
    c.drawString(20 * mm, y, "Findings")
    y -= 8 * mm
    c.setFont("Helvetica", 9)
    for a in data["attacks"]:
        if y < 30 * mm:
            c.showPage()
            y = height - 25 * mm
            c.setFont("Helvetica", 9)
        line = f"[{a['severity']}] {a['owasp_ref']} {a['category']} -> {a['verdict']}"
        c.drawString(20 * mm, y, line[:110])
        y -= 5 * mm
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(24 * mm, y, ("Mitigation: " + a["mitigation"])[:120])
        c.setFont("Helvetica", 9)
        y -= 7 * mm
    c.showPage()
    c.save()
    return buf.getvalue()


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
