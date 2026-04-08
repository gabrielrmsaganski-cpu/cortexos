from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.core.text_utils import lexical_overlap_score, normalize_text
from app.models.schemas import MemoryRecord

KEY_VALUE_PATTERNS = [
    re.compile(
        r"(?P<subject>[A-Za-z0-9 _/\-]+?)\s+"
        r"(?:is|are|uses|prefer(?:s)?|runs on|deadline is|launch is|moved to|changed to)\s+"
        r"(?P<value>[^.\n]+)",
        re.IGNORECASE,
    ),
]

UPDATE_HINTS = ("changed to", "moved to", "updated to", "now", "replaced", "instead of")


@dataclass
class RelationDecision:
    relation_type: str
    score: float
    reason: str


def compare_memories(new_text: str, existing: MemoryRecord) -> RelationDecision | None:
    normalized_new = normalize_text(new_text)
    normalized_old = existing.normalized_text
    sequence = SequenceMatcher(None, normalized_new, normalized_old).ratio()
    lexical = lexical_overlap_score(new_text, existing.verbatim_text)

    if sequence >= 0.97:
        return RelationDecision("duplicate", sequence, "Exact or near-exact normalized duplicate.")

    new_claims = _extract_claims(new_text)
    old_claims = _extract_claims(existing.verbatim_text)
    for key, new_value in new_claims.items():
        if key not in old_claims:
            continue
        old_value = old_claims[key]
        if new_value == old_value and lexical >= 0.55:
            return RelationDecision(
                "complements",
                lexical,
                f"Same fact key `{key}` with matching value.",
            )
        if new_value != old_value:
            if any(hint in normalized_new for hint in UPDATE_HINTS):
                return RelationDecision(
                    "supersedes",
                    max(sequence, lexical),
                    (
                        f"Fact key `{key}` changed from `{old_value}` "
                        f"to `{new_value}` with update cue."
                    ),
                )
            return RelationDecision(
                "conflicts_with",
                max(sequence, lexical),
                f"Fact key `{key}` has incompatible values `{old_value}` vs `{new_value}`.",
            )

    if sequence >= 0.82 and lexical >= 0.55:
        return RelationDecision(
            "complements",
            max(sequence, lexical),
            "High semantic and lexical overlap.",
        )
    return None


def _extract_claims(text: str) -> dict[str, str]:
    claims: dict[str, str] = {}
    for pattern in KEY_VALUE_PATTERNS:
        for match in pattern.finditer(text):
            key = _normalize_claim_key(match.group("subject"))
            value = normalize_text(match.group("value"))
            if key and value:
                claims[key] = value
    for date_match in re.finditer(r"\b(20\d{2}-\d{2}-\d{2})\b", text):
        claims["date"] = date_match.group(1)
    return claims


def _normalize_claim_key(subject: str) -> str:
    key = normalize_text(subject)
    key = re.sub(r"^the\s+", "", key)
    key = re.sub(r"\s+(date|deadline|time)$", "", key)
    return key
