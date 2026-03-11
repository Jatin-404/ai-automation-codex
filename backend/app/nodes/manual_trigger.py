from datetime import datetime
from typing import Any, Dict, List
from app.nodes.base import BaseNode, NodeDefinition, NodeExecutionResult, normalize_items, Item


class ManualTrigger(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="manual_trigger",
            label="Manual Trigger",
            description="Start the workflow manually by clicking Run Workflow",
            category="trigger",
            color="#6366f1",
            icon="??",
            inputs=0,
            outputs=1,
            config_schema=[
                {
                    "key": "note",
                    "label": "Note (optional)",
                    "type": "text",
                    "placeholder": "What does this workflow do?",
                    "required": False,
                    "help": "Just a reminder for yourself"
                }
            ]
        )

    async def execute(self, config: Dict[str, Any], inputs: List[List[Item]], context) -> NodeExecutionResult:
        item = {
            "triggered_at": datetime.utcnow().isoformat(),
            "trigger_type": "manual",
            "note": config.get("note", "")
        }
        return NodeExecutionResult(
            success=True,
            outputs=[normalize_items(item)],
            metadata={"trigger_type": "manual"}
        )
