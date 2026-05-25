"""Deterministic content classification and entity extraction."""

from __future__ import annotations

import re


CLASS_KEYWORDS = {
    "invoice": {"invoice", "total due", "bill to", "vendor"},
    "resume": {"experience", "skills", "education", "certification"},
    "contract": {"agreement", "effective date", "term", "party"},
}


def classify_text(text: str) -> str:
    lowered = text.lower()
    best_label = "general"
    best_score = 0
    for label, keywords in CLASS_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_label = label
            best_score = score
    return best_label


def extract_entities(text: str) -> dict[str, list[str]]:
    return {
        "emails": sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", text))),
        "dates": sorted(set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text))),
        "currency_amounts": sorted(set(re.findall(r"\$\d+(?:,\d{3})*(?:\.\d{2})?", text))),
        "invoice_ids": sorted(set(re.findall(r"INV-\d+", text))),
    }
