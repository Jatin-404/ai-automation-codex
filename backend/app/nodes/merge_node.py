from typing import Any, Dict, List
from app.nodes.base import BaseNode, NodeDefinition, NodeExecutionResult, Item


class MergeNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="merge",
            label="Merge",
            description="Combine data from multiple branches into one output",
            category="logic",
            color="#64748b",
            icon="??",
            inputs=2,
            outputs=1,
            config_schema=[
                {
                    "key": "mode",
                    "label": "How to merge",
                    "type": "select",
                    "options": [
                        "Combine into one object",
                        "Put into array",
                        "Keep first branch only",
                        "Keep second branch only"
                    ],
                    "default": "Combine into one object",
                    "required": True,
                    "help": "Choose how to combine the two inputs"
                },
                {
                    "key": "key_a",
                    "label": "Label for first input",
                    "type": "text",
                    "placeholder": "branch_a",
                    "default": "branch_a",
                    "required": False,
                    "help": "Key name for the first branch (used in 'Put into array' mode)"
                },
                {
                    "key": "key_b",
                    "label": "Label for second input",
                    "type": "text",
                    "placeholder": "branch_b",
                    "default": "branch_b",
                    "required": False,
                    "help": "Key name for the second branch"
                }
            ]
        )

    async def execute(self, config: Dict[str, Any], inputs: List[List[Item]], context) -> NodeExecutionResult:
        mode = config.get("mode", "Combine into one object")
        key_a = config.get("key_a", "branch_a")
        key_b = config.get("key_b", "branch_b")

        left = inputs[0] if len(inputs) > 0 else []
        right = inputs[1] if len(inputs) > 1 else []
        max_len = max(len(left), len(right))

        output_items: List[Item] = []

        for idx in range(max_len):
            a = left[idx].get("json", {}) if idx < len(left) else {}
            b = right[idx].get("json", {}) if idx < len(right) else {}

            if mode == "Combine into one object":
                a_obj = a if isinstance(a, dict) else {key_a: a}
                b_obj = b if isinstance(b, dict) else {key_b: b}
                output = {**a_obj, **b_obj}
            elif mode == "Put into array":
                output = {key_a: a, key_b: b}
            elif mode == "Keep first branch only":
                output = a
            elif mode == "Keep second branch only":
                output = b
            else:
                output = {key_a: a, key_b: b}

            output_items.append({"json": output})

        return NodeExecutionResult(success=True, outputs=[output_items])
