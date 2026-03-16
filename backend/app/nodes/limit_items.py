from typing import Any, Dict, List
from app.nodes.base import BaseNode, NodeDefinition, NodeExecutionResult, Item


class LimitItemsNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="limit_items",
            label="Limit Items",
            description="Pass through only the first N items",
            category="logic",
            color="#64748b",
            icon="N",
            inputs=1,
            outputs=1,
            config_schema=[
                {
                    "key": "count",
                    "label": "Max items",
                    "type": "number",
                    "default": 10,
                    "min": 1,
                    "max": 1000,
                    "required": True,
                    "help": "How many items to keep from the input."
                },
                {
                    "key": "keep",
                    "label": "Keep",
                    "type": "select",
                    "options": ["First Items", "Last Items"],
                    "default": "First Items",
                    "required": True
                }
            ]
        )

    async def execute(self, config: Dict[str, Any], inputs: List[List[Item]], context) -> NodeExecutionResult:
        try:
            count = int(config.get("count", 10))
        except (TypeError, ValueError):
            return NodeExecutionResult(success=False, error="Max items must be a number")

        if count < 1:
            return NodeExecutionResult(success=False, error="Max items must be at least 1")

        items = inputs[0] if inputs else []
        keep = config.get("keep", "First Items")
        output_items = items[:count] if keep == "First Items" else items[-count:]

        return NodeExecutionResult(success=True, outputs=[output_items])
