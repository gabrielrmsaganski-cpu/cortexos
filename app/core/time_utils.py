from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

AGO_RE = re.compile(
    r"(?P<count>\d+)\s+"
    r"(?P<unit>day|days|week|weeks|month|months|year|years)\s+ago"
)


def now_utc() -> datetime:
    return datetime.now(UTC)


def iso_now() -> str:
    return now_utc().replace(microsecond=0).isoformat()


@dataclass
class TemporalIntent:
    target: datetime | None
    window_days: int


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_temporal_intent(query: str, reference: datetime | None = None) -> TemporalIntent:
    reference = reference or now_utc()
    lowered = query.lower()
    if "today" in lowered:
        return TemporalIntent(target=reference, window_days=1)
    if "yesterday" in lowered:
        return TemporalIntent(target=reference - timedelta(days=1), window_days=1)
    if "last week" in lowered:
        return TemporalIntent(target=reference - timedelta(days=7), window_days=7)
    if "last month" in lowered:
        return TemporalIntent(target=reference - timedelta(days=30), window_days=15)
    match = AGO_RE.search(lowered)
    if not match:
        return TemporalIntent(target=None, window_days=0)
    count = int(match.group("count"))
    unit = match.group("unit")
    factor = {
        "day": 1,
        "days": 1,
        "week": 7,
        "weeks": 7,
        "month": 30,
        "months": 30,
        "year": 365,
        "years": 365,
    }[unit]
    target = reference - timedelta(days=count * factor)
    return TemporalIntent(target=target, window_days=max(1, factor))
