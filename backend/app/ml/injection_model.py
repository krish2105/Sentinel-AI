"""Prompt-injection classifier wrapper.

Primary model: ``protectai/deberta-v3-base-prompt-injection-v2`` (open, local,
no key). Loading transformers/torch is gated behind ``ENABLE_HEAVY_ML`` so the
service boots fast by default. When the heavy model is unavailable we fall back
to a **transparent heuristic detector** built from documented injection
signatures — deterministic, explainable, and good enough to demo the two-tier
defense end-to-end.

This is the fast, deterministic first layer of the two-tier detector; the
LLM-as-judge is the reasoning second layer.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional

from app.config import settings


@dataclass
class Classification:
    label: str  # "INJECTION" | "SAFE"
    score: float  # probability of INJECTION in [0, 1]
    signals: List[str]  # human-readable matched signals
    engine: str  # "deberta" | "heuristic"


# Documented injection signatures (regex, weight, label)
_SIGNATURES = [
    (r"ignore (all|any|the|your)? ?(previous|prior|above|earlier) (instructions|prompts|rules|directives)", 0.9, "ignore-previous"),
    (r"disregard (all|the|your)? ?(previous|prior|above)", 0.85, "disregard"),
    (r"(system\s*(override|prompt)|override:\s*true)", 0.8, "system-override"),
    (r"developer mode", 0.7, "developer-mode"),
    (r"\bDAN\b|do anything now", 0.7, "dan-jailbreak"),
    (r"(reveal|print|repeat|show|output).{0,30}(system prompt|instructions|configuration)", 0.85, "prompt-extraction"),
    (r"you are now", 0.55, "role-reset"),
    (r"(exfiltrat|forward all|send .* to .*@)", 0.8, "exfiltration"),
    (r"(api[_\- ]?key|secret|password|credentials|session token)", 0.5, "sensitive-token"),
    (r"new (primary )?objective|your (real|only) (goal|mission)", 0.65, "goal-hijack"),
    (r"<!--.*(ignore|system|instruction).*-->", 0.85, "hidden-html-comment"),
    (r"base64|\[encoded directive", 0.5, "encoding-obfuscation"),
    (r"stay in character no matter what", 0.6, "persona-lock"),
]


# Common Cyrillic/Greek homoglyphs of Latin letters used to evade keyword
# filters (e.g. Cyrillic 'о' U+043E for Latin 'o'). NFKC does NOT fold these
# because they are different scripts, so we map them explicitly.
_CONFUSABLES = {
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y",
    "к": "k", "м": "m", "н": "h", "т": "t", "в": "b", "і": "i", "ѕ": "s",
    "ԁ": "d", "ɡ": "g", "ⅼ": "l", "ｅ": "e",
    "α": "a", "ο": "o", "ρ": "p", "ϲ": "c", "ν": "v", "ι": "i", "κ": "k",
}


def _fold_confusables(text: str) -> str:
    return "".join(_CONFUSABLES.get(c, c) for c in text)


def _normalize(text: str) -> str:
    # NFKC folds compatibility characters and strips zero-width/format chars used
    # to smuggle hidden instructions; homoglyph folding catches cross-script
    # confusables that NFKC leaves alone.
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    text = _fold_confusables(text)
    return text


class _HeuristicClassifier:
    engine = "heuristic"

    def classify(self, text: str) -> Classification:
        norm = _normalize(text).lower()
        score = 0.0
        signals: List[str] = []
        for pattern, weight, name in _SIGNATURES:
            if re.search(pattern, norm):
                signals.append(name)
                # Combine independent evidence (noisy-OR).
                score = 1 - (1 - score) * (1 - weight)
        label = "INJECTION" if score >= settings.injection_threshold else "SAFE"
        return Classification(label=label, score=round(score, 4), signals=signals,
                              engine=self.engine)


class _DebertaClassifier:  # pragma: no cover - requires heavy deps
    engine = "deberta"

    def __init__(self) -> None:
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            pipeline,
        )

        tok = AutoTokenizer.from_pretrained(settings.injection_model)
        model = AutoModelForSequenceClassification.from_pretrained(
            settings.injection_model
        )
        self._pipe = pipeline(
            "text-classification", model=model, tokenizer=tok, truncation=True
        )

    def classify(self, text: str) -> Classification:
        norm = _normalize(text)
        out = self._pipe(norm[:2000])[0]
        raw_label = out["label"].upper()
        is_injection = raw_label in ("INJECTION", "LABEL_1", "1")
        score = out["score"] if is_injection else 1 - out["score"]
        label = "INJECTION" if score >= settings.injection_threshold else "SAFE"
        return Classification(label=label, score=round(float(score), 4),
                              signals=[f"deberta:{raw_label}"], engine=self.engine)


_instance: Optional[object] = None


def get_classifier():
    global _instance
    if _instance is not None:
        return _instance
    if settings.enable_heavy_ml:
        try:
            _instance = _DebertaClassifier()
            return _instance
        except Exception:
            pass
    _instance = _HeuristicClassifier()
    return _instance


def classify(text: str) -> Classification:
    return get_classifier().classify(text)
