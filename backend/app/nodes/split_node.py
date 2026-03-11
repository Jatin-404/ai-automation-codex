import json
import operator
from typing import Any, Dict
from app.nodes.base import BaseNode, NodeDefinition, NodeResult

OPS = {
    "equals":           operator.eq,
    "not equals":       operator.ne,
    "greater than":     operator.gt,
    "less than":        operator.lt,
    "contains":         lambda a, b: str(b).lower() in str(a).lower(),
    "not contains":     lambda a, b: str(b).lower() not in str(a).lower(),
    "is empty":         lambda a, _: not a,
    "is not empty":     lambda a, _: bool(a),
    "starts with":      lambda a, b: str(a).startswith(str(b)),
    "ends with":        lambda a, b: str(a).endswith(str(b)),
}


def _get_nested(data: Any, path: str) -> Any:
    """Access nested dict values using dot notation: 'user.name'"""
    keys = path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current


class SplitNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="split",
            label="Split / Condition",
            description="Routes data down different paths based on a condition — like an IF statement",
            category="logic",
            color="#ef4444",
            icon="🔀",
            inputs=1,
            outputs=2,   # output 0 = TRUE path, output 1 = FALSE path
            config_schema=[
                {
                    "key": "field",
                    "label": "Field to check",
                    "type": "text",
                    "placeholder": "status  (or  user.age  for nested)",
                    "required": True,
                    "help": "Which field from the previous node's output to evaluate. Use dot notation for nested fields."
                },
                {
                    "key": "condition",
                    "label": "Condition",
                    "type": "select",
                    "options": list(OPS.keys()),
                    "default": "equals",
                    "required": True,
                    "help": "How to compare the field value"
                },
                {
                    "key": "value",
                    "label": "Compare Value",
                    "type": "text",
                    "placeholder": "active",
                    "required": False,
                    "help": "The value to compare against (not needed for 'is empty' / 'is not empty')"
                },
                {
                    "key": "true_label",
                    "label": "TRUE path label",
                    "type": "text",
                    "placeholder": "Yes / Match",
                    "default": "✅ True",
                    "required": False
                },
                {
                    "key": "false_label",
                    "label": "FALSE path label",
                    "type": "text",
                    "placeholder": "No / No match",
                    "default": "❌ False",
                    "required": False
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        input_data: Any,
        context: Dict[str, Any]
    ) -> NodeResult:
        field = config.get("field", "")
        condition = config.get("condition", "equals")
        compare_value = config.get("value", "")

        # Extract the field value from input
        if isinstance(input_data, dict):
            actual_value = _get_nested(input_data, field)
        else:
            actual_value = input_data

        # Evaluate the condition
        op_fn = OPS.get(condition)
        if not op_fn:
            return NodeResult(success=False, error=f"Unknown condition: {condition}")

        try:
            # Try numeric comparison
            try:
                actual_num = float(actual_value) if actual_value is not None else None
                compare_num = float(compare_value) if compare_value else None
                if actual_num is not None and compare_num is not None:
                    result = op_fn(actual_num, compare_num)
                else:
                    result = op_fn(actual_value, compare_value)
            except (ValueError, TypeError):
                result = op_fn(actual_value, compare_value)

        except Exception as e:
            return NodeResult(success=False, error=f"Condition evaluation failed: {str(e)}")

        return NodeResult(
            success=True,
            output={
                "data": input_data,          # pass original data through
                "branch": "true" if result else "false",
                "matched": result,
                "evaluated": {
                    "field": field,
                    "actual_value": actual_value,
                    "condition": condition,
                    "compare_value": compare_value,
                    "result": result
                }
            },
            metadata={
                "branch": "true" if result else "false",
                "output_index": 0 if result else 1   # engine uses this to route
            }
        )