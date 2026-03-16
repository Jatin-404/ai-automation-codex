import json
from datetime import datetime
from typing import Any, Dict, List
from app.nodes.base import BaseNode, NodeDefinition, NodeExecutionResult, Item
from app.nodes.utils import get_nested, resolve_expressions


def _to_number(value: Any) -> float:
    return float(value)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _to_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


OPS = {
    "equals":       lambda a, b: a == b,
    "not equals":   lambda a, b: a != b,
    "greater than": lambda a, b: a > b,
    "greater than or equal": lambda a, b: a >= b,
    "less than":    lambda a, b: a < b,
    "less than or equal": lambda a, b: a <= b,
    "contains":     lambda a, b: str(b).lower() in str(a).lower(),
    "not contains": lambda a, b: str(b).lower() not in str(a).lower(),
    "starts with":  lambda a, b: str(a).lower().startswith(str(b).lower()),
    "ends with":    lambda a, b: str(a).lower().endswith(str(b).lower()),
    "is empty":     lambda a, b: not a or str(a).strip() == "",
    "is not empty": lambda a, b: bool(a) and str(a).strip() != "",
}


class FilterItemsNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="filter_items",
            label="Filter Items",
            description="Allow or block items based on conditions (like n8n Filter)",
            category="logic",
            color="#ef4444",
            icon="F",
            inputs=1,
            outputs=2,
            config_schema=[
                {
                    "key": "combine_mode",
                    "label": "Combine Conditions",
                    "type": "select",
                    "options": ["AND", "OR"],
                    "default": "AND",
                    "required": True,
                    "help": "AND = all conditions match, OR = any condition matches"
                },
                {
                    "key": "data_type",
                    "label": "Data Type",
                    "type": "select",
                    "options": ["String", "Number", "Boolean", "Date & Time"],
                    "default": "String",
                    "required": True,
                    "help": "Controls how values are compared"
                },
                {
                    "key": "conditions",
                    "label": "Conditions",
                    "type": "conditions",
                    "required": True
                }
            ]
        )

    async def execute(self, config: Dict[str, Any], inputs: List[List[Item]], context) -> NodeExecutionResult:
        combine_mode = (config.get("combine_mode") or "AND").upper()
        data_type = config.get("data_type") or "String"
        raw_conditions = config.get("conditions") or []

        if isinstance(raw_conditions, str):
            try:
                raw_conditions = json.loads(raw_conditions)
            except json.JSONDecodeError:
                return NodeExecutionResult(success=False, error="Conditions must be valid JSON")

        if not isinstance(raw_conditions, list) or not raw_conditions:
            return NodeExecutionResult(success=False, error="Add at least one condition")

        def coerce(value: Any) -> Any:
            if data_type == "Number":
                return _to_number(value)
            if data_type == "Boolean":
                return _to_bool(value)
            if data_type == "Date & Time":
                return _to_datetime(value)
            return str(value)

        true_items: List[Item] = []
        false_items: List[Item] = []

        for item in (inputs[0] if inputs else []):
            data = item.get("json", {}) if isinstance(item, dict) else {}
            results: List[bool] = []

            for cond in raw_conditions:
                value1 = (cond.get("value1") or "").strip()
                operation = cond.get("operation", "equals")
                value2 = (cond.get("value2") or "").strip()

                op_fn = OPS.get(operation)
                if not op_fn:
                    return NodeExecutionResult(success=False, error=f"Unknown operation: {operation}")

                # Resolve value1 (field path or expression)
                if value1.startswith("{{$json.") and value1.endswith("}}"):
                    value1 = value1.replace("{{$json.", "").replace("}}", "")
                if value1.startswith("$json."):
                    value1 = value1.replace("$json.", "", 1)

                if "{{" in value1 and "}}" in value1:
                    actual = resolve_expressions(value1, data)
                else:
                    actual = get_nested(data, value1) if value1 else data

                compare = resolve_expressions(value2, data) if value2 else value2

                try:
                    left = coerce(actual)
                    right = coerce(compare) if operation not in {"is empty", "is not empty"} else compare
                    result = op_fn(left, right)
                except (ValueError, TypeError) as e:
                    return NodeExecutionResult(success=False, error=f"Condition evaluation failed: {e}")

                results.append(bool(result))

            is_match = all(results) if combine_mode == "AND" else any(results)

            if is_match:
                true_items.append(item)
            else:
                false_items.append(item)

        return NodeExecutionResult(success=True, outputs=[true_items, false_items])
