import json
from typing import Any, Dict
from app.nodes.base import BaseNode, NodeDefinition, NodeResult


class MergeNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="merge",
            label="Merge",
            description="Combine data from multiple branches into one output",
            category="logic",
            color="#64748b",
            icon="🔗",
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

    async def execute(self, config: Dict[str, Any], input_data: Any, context: Dict[str, Any]) -> NodeResult:
        mode  = config.get("mode", "Combine into one object")
        key_a = config.get("key_a", "branch_a")
        key_b = config.get("key_b", "branch_b")

        # input_data may be a list of [branch_a_data, branch_b_data] when merging
        if isinstance(input_data, list) and len(input_data) >= 2:
            data_a = input_data[0]
            data_b = input_data[1]
        else:
            data_a = input_data
            data_b = {}

        if mode == "Combine into one object":
            a = data_a if isinstance(data_a, dict) else {key_a: data_a}
            b = data_b if isinstance(data_b, dict) else {key_b: data_b}
            output = {**a, **b}

        elif mode == "Put into array":
            output = [data_a, data_b]

        elif mode == "Keep first branch only":
            output = data_a

        elif mode == "Keep second branch only":
            output = data_b

        else:
            output = input_data

        return NodeResult(success=True, output=output)
