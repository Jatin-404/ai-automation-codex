from typing import Any, Dict, List
from app.nodes.base import BaseNode, NodeDefinition, NodeExecutionResult, Item
from app.nodes.utils import get_nested

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


class IfConditionNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="if_condition",
            label="IF Condition",
            description="Check a condition - TRUE goes one way, FALSE goes another way",
            category="logic",
            color="#f97316",
            icon="??",
            inputs=1,
            outputs=2,
            config_schema=[
                {
                    "key": "field",
                    "label": "Field to check",
                    "type": "text",
                    "placeholder": "status or user.age or price",
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
                    "default": "? Yes",
                    "required": False
                },
                {
                    "key": "false_label",
                    "label": "FALSE path label",
                    "type": "text",
                    "default": "? No",
                    "required": False
                }
            ]
        )

    async def execute(self, config: Dict[str, Any], inputs: List[List[Item]], context) -> NodeExecutionResult:
        field = config.get("field", "")
        condition = config.get("condition", "equals")
        compare = config.get("value", "")

        op_fn = OPS.get(condition)
        if not op_fn:
            return NodeExecutionResult(success=False, error=f"Unknown condition: {condition}")

        true_items: List[Item] = []
        false_items: List[Item] = []

        for item in (inputs[0] if inputs else []):
            data = item.get("json", {}) if isinstance(item, dict) else {}
            actual = get_nested(data, field) if field else data
            try:
                result = op_fn(actual, compare)
            except (ValueError, TypeError) as e:
                return NodeExecutionResult(success=False, error=f"Could not compare values: {e}")

            if result:
                true_items.append(item)
            else:
                false_items.append(item)

        return NodeExecutionResult(
            success=True,
            outputs=[true_items, false_items],
            metadata={"true_count": len(true_items), "false_count": len(false_items)}
        )
