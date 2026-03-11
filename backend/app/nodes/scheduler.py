from datetime import datetime
from typing import Any, Dict, List
from app.nodes.base import BaseNode, NodeDefinition, NodeExecutionResult, normalize_items, Item


class SchedulerNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="scheduler",
            label="Schedule Trigger",
            description="Runs the workflow automatically on a repeating schedule. Use the /api/workflows/schedule endpoint to activate.",
            category="trigger",
            color="#f59e0b",
            icon="?",
            inputs=0,
            outputs=1,
            config_schema=[
                {
                    "key": "interval_type",
                    "label": "Run Every",
                    "type": "select",
                    "options": ["minute", "hour", "day", "week"],
                    "default": "hour",
                    "required": True,
                    "help": "How often the workflow should repeat"
                },
                {
                    "key": "interval_value",
                    "label": "Amount",
                    "type": "number",
                    "default": 1,
                    "min": 1,
                    "max": 100,
                    "required": True,
                    "help": "E.g. 2 + hour = every 2 hours"
                },
                {
                    "key": "workflow_id",
                    "label": "Workflow ID",
                    "type": "text",
                    "placeholder": "my-daily-report",
                    "required": True,
                    "help": "A unique name for this schedule (no spaces)"
                }
            ]
        )

    async def execute(self, config: Dict[str, Any], inputs: List[List[Item]], context) -> NodeExecutionResult:
        item = {
            "triggered_at": datetime.utcnow().isoformat(),
            "schedule": f"every {config.get('interval_value', 1)} {config.get('interval_type', 'hour')}",
            "trigger_type": "schedule"
        }
        return NodeExecutionResult(
            success=True,
            outputs=[normalize_items(item)],
            metadata={"trigger_type": "schedule"}
        )
