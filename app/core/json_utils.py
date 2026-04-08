from __future__ import annotations

import json
from typing import Any

import orjson


def dumps(value: Any) -> str:
    return orjson.dumps(value, option=orjson.OPT_SORT_KEYS).decode("utf-8")


def loads(value: str | bytes | None, default: Any = None) -> Any:
    if value in (None, "", b""):
        return default
    if isinstance(value, str):
        return json.loads(value)
    return orjson.loads(value)
