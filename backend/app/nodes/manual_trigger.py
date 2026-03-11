from datetime import datetime
from typing import Any, Dict
from app.nodes.base import BaseNode, NodeDefinition, NodeResult


class ManualTrigger(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="manual_trigger",
            label="Manual Trigger",
            description="Start the workflow manually by clicking Run Workflow",
            category="trigger",
            color="#6366f1",
            icon="▶️",
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
    
    async def execute(self, config: Dict[str, Any], input_data: Any, context: Dict[str, Any]) -> NodeResult:
        return NodeResult(
            success=True,
            output={
                "trigger_at": datetime.utcnow().isoformat(),
                "trigger_type": "manual",
                "note": config.get("note", "")
            },
            metadata={"trigger_type": "manual"}
        )