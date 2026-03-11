from __future__ import annotations

import json
import re
from typing import Any, Dict
from app.nodes.base import Item, normalize_items, ensure_item


def get_nested(data: Any, path: str) -> Any:
    if not path:
        return None
    cur = data
    for key in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(key)
        else:
            return None
    return cur


def resolve_expressions(value: Any, data: Dict[str, Any]) -> Any:
    if not isinstance(value, str):
        return value

    full_match = re.fullmatch(r"\{\{([^}]+)\}\}", value.strip())
    if full_match:
        key = full_match.group(1).strip()
        result = get_nested(data, key)
        return result if result is not None else value

    def replacer(match):
        key = match.group(1).strip()
        val = get_nested(data, key)
        return str(val) if val is not None else match.group(0)

    return re.sub(r"\{\{([^}]+)\}\}", replacer, value)


def resolve_in_object(value: Any, data: Dict[str, Any]) -> Any:
    if isinstance(value, list):
        return [resolve_in_object(v, data) for v in value]
    if isinstance(value, dict):
        return {k: resolve_in_object(v, data) for k, v in value.items()}
    return resolve_expressions(value, data)


def json_dumps_safe(value: Any) -> str:
    try:
        return json.dumps(value, default=str)
    except Exception:
        return str(value)


def to_output_items(value: Any) -> list[Item]:
    return normalize_items(value)
