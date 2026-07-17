"""Serve evaluation reports for the in-app Model Card page.

Reads the JSON reports produced by the eval scripts; computes the classifier
report on the fly if it hasn't been generated yet so the page is never empty.
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/evals", tags=["evals"])

_EVALS_DIR = Path(__file__).resolve().parents[2] / "evals"


def _load(name: str):
    path = _EVALS_DIR / name
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
    return None


@router.get("")
async def get_evals():
    classifier = _load("classifier_report.json")
    if classifier is None:
        from app.ml.eval_classifier import evaluate

        classifier = evaluate()

    return {
        "classifier": classifier,
        "guardrail_ab": _load("guardrail_ab.json"),
        "judge": _load("judge_eval.json"),
        "rag": _load("rag_eval.json"),
    }
