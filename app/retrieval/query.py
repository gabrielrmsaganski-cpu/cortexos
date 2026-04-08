from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.core.text_utils import extract_keywords, normalize_text


@dataclass
class NormalizedQuery:
    original: str
    normalized: str
    expanded: str
    keywords: list[str]


def normalize_query(text: str) -> NormalizedQuery:
    settings = get_settings()
    normalized = normalize_text(text)
    keywords = extract_keywords(text)
    expanded = normalized
    if settings.enable_query_expansion and keywords:
        expanded = f"{normalized} {' '.join(sorted(set(keywords)))}"
    return NormalizedQuery(
        original=text,
        normalized=normalized,
        expanded=expanded,
        keywords=keywords,
    )
