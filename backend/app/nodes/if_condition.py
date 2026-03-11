import operator
from typing import Any, Dict
from app.nodes.base import BaseNode, NodeDefinition, NodeResult

OPS = {
    "equals":       lambda a, b: str(a).strip().lower() == str(b).strip().lower(),
    "not equals":   lambda a, b: str(a).strip().lower() != str(b).strip().lower(),
    "greater than": lambda a, b: float(a) > float(b),
    "less than":    lambda a, b: float(a) < float(b),
    "contains":     lambda a, b: str(b).lower() in str(a).lower(),
    "not contains": lambda a, b: str(b).lower() not in str(a).lower(),
    "is empty":     lambda a, b: not a or str(a).strip() == "",
    "is not empty": lambda a, b: bool(a) and str(a).strip() != "",
    "starts with":  lambda a, b: str(a).lower().startswith(str(b).lower()),
    "ends with":    lambda a, b: str(a).lower().endswith(str(b).lower()),
}


def get_nested(data: Any, path: str) -> Any:
    for key in path.split("."):
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


class IfConditionNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="if_condition",
            label="IF Condition",
            description="Check a condition — if TRUE goes one way, if FALSE goes another way",
            category="logic",
            color="#f97316",
            icon="🔀",
            inputs=1,
            outputs=2,
            config_schema=[
                {
                    "key": "field",
                    "label": "Field to check",
                    "type": "text",
                    "placeholder": "status  or  user.age  or  price",
                    "required": True,
                    "help": "Which field from the previous data to check. Use dot notation for nested: user.name"
                },
                {
                    "key": "condition",
                    "label": "Condition",
                    "type": "select",
                    "options": list(OPS.keys()),
                    "default": "equals",
                    "required": True,
                    "help": "How to compare the value"
                },
                {
                    "key": "value",
                    "label": "Value to compare",
                    "type": "text",
                    "placeholder": "active",
                    "required": False,
                    "help": "Leave empty for 'is empty' / 'is not empty'"
                },
                {
                    "key": "true_label",
                    "label": "TRUE path label",
                    "type": "text",
                    "default": "✅ Yes",
                    "required": False
                },
                {
                    "key": "false_label",
                    "label": "FALSE path label",
                    "type": "text",
                    "default": "❌ No",
                    "required": False
                }
            ]
        )

    async def execute(self, config: Dict[str, Any], input_data: Any, context: Dict[str, Any]) -> NodeResult:
        field     = config.get("field", "")
        condition = config.get("condition", "equals")
        compare   = config.get("value", "")

        actual = get_nested(input_data, field) if isinstance(input_data, dict) else input_data

        op_fn = OPS.get(condition)
        if not op_fn:
            return NodeResult(success=False, error=f"Unknown condition: {condition}")

        try:
            result = op_fn(actual, compare)
        except (ValueError, TypeError) as e:
            return NodeResult(success=False, error=f"Could not compare values: {e}")

        return NodeResult(
            success=True,
            output={
                "data": input_data,
                "branch": "true" if result else "false",
                "matched": result,
                "evaluated": {"field": field, "actual": actual, "condition": condition, "compare": compare}
            },
            metadata={"branch": "true" if result else "false", "output_index": 0 if result else 1}
        )