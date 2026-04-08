from __future__ import annotations

import re

from app.models.schemas import MemoryInput

PROCEDURAL_HINTS = ("step", "steps", "procedure", "run", "execute", "first", "then", "finally")
EPISODIC_HINTS = ("yesterday", "today", "last week", "meeting", "we decided", "we discussed")
REFERENCE_HINTS = ("http://", "https://", "docs", "manual", "documentation", "reference")
UPDATE_HINTS = ("changed to", "moved to", "replaced", "now", "updated to", "instead of")


def classify_memory(input_data: MemoryInput) -> tuple[str, dict[str, float | str]]:
    text = input_data.text.lower()
    source = input_data.source.lower()

    scores = {
        "episodic": 0.2,
        "factual": 0.2,
        "procedural": 0.2,
        "reference": 0.2,
    }

    if any(hint in text for hint in PROCEDURAL_HINTS):
        scores["procedural"] += 0.45
    if any(hint in text for hint in EPISODIC_HINTS):
        scores["episodic"] += 0.45
    if any(hint in text for hint in REFERENCE_HINTS) or source in {"web", "document"}:
        scores["reference"] += 0.45
    if re.search(r"\\b(is|are|uses|has|prefers|runs on|deadline|launch|version)\\b", text):
        scores["factual"] += 0.4
    if any(hint in text for hint in UPDATE_HINTS):
        scores["factual"] += 0.1
        scores["episodic"] += 0.1

    memory_type = max(scores, key=scores.get)
    importance = _importance(text)
    confidence = _confidence(input_data.source, memory_type)
    classifier = {
        "memory_type": memory_type,
        "scores": scores,
        "importance": importance,
        "confidence": confidence,
    }
    return memory_type, classifier


def _importance(text: str) -> float:
    value = 0.45
    if any(
        token in text
        for token in ("critical", "urgent", "must", "production", "never", "always")
    ):
        value += 0.3
    if any(token in text for token in ("decision", "deadline", "launch", "incident", "policy")):
        value += 0.15
    return min(value, 1.0)


def _confidence(source: str, memory_type: str) -> float:
    base = {
        "api": 0.75,
        "manual": 0.8,
        "document": 0.85,
        "web": 0.7,
        "crawl": 0.7,
    }.get(source, 0.7)
    if memory_type == "reference":
        base += 0.05
    return min(base, 0.98)
