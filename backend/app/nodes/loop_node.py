from typing import Any, Dict, List
from app.nodes.base import BaseNode, NodeDefinition, NodeResult


class LoopNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="loop_node",
            label="Loop / Split Items",
            description="Take a list of items and process each one — like 'for each row in a spreadsheet'",
            category="logic",
            color="#8b5cf6",
            icon="🔁",
            inputs=1,
            outputs=1,
            config_schema=[
                {
                    "key": "field",
                    "label": "List field to loop over",
                    "type": "text",
                    "placeholder": "items  or  results  or  data.rows",
                    "required": False,
                    "help": "Which field contains the list? Leave empty if the whole input is a list."
                },
                {
                    "key": "mode",
                    "label": "Output mode",
                    "type": "select",
                    "options": ["Pass all items as array", "Pass first item only", "Pass last item only", "Pass count only"],
                    "default": "Pass all items as array",
                    "required": True,
                    "help": "How to pass the items to the next node"
                },
                {
                    "key": "max_items",
                    "label": "Max items to process",
                    "type": "number",
                    "default": 100,
                    "min": 1,
                    "max": 1000,
                    "required": False,
                    "help": "Stop after this many items (safety limit)"
                }
            ]
        )

    async def execute(self, config: Dict[str, Any], input_data: Any, context: Dict[str, Any]) -> NodeResult:
        field     = config.get("field", "").strip()
        mode      = config.get("mode", "Pass all items as array")
        try:
            max_items = int(config.get("max_items", 100))
        except (TypeError, ValueError):
            max_items = 100

        # Extract the list
        if field:
            parts = field.split(".")
            data = input_data
            for p in parts:
                if isinstance(data, dict):
                    data = data.get(p)
                else:
                    data = None
                    break
            items = data
        else:
            items = input_data

        if items is None:
            return NodeResult(success=False, error=f"Field '{field}' not found in input data")

        if not isinstance(items, list):
            items = [items]

        items = items[:max_items]

        if mode == "Pass all items as array":
            output = {"items": items, "count": len(items)}
        elif mode == "Pass first item only":
            output = items[0] if items else None
        elif mode == "Pass last item only":
            output = items[-1] if items else None
        elif mode == "Pass count only":
            output = {"count": len(items)}
        else:
            output = items

        return NodeResult(
            success=True,
            output=output,
            metadata={"item_count": len(items)}
        )
