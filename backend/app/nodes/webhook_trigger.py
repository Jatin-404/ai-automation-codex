from typing import Any, Dict, List
from app.nodes.base import BaseNode, NodeDefinition, NodeExecutionResult, normalize_items, Item


class WebhookTriggerNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="webhook_trigger",
            label="Webhook Trigger",
            description="Starts the workflow when an HTTP request arrives at a URL",
            category="trigger",
            color="#3b82f6",
            icon="??",
            inputs=0,
            outputs=1,
            config_schema=[
                {
                    "key": "path",
                    "label": "Webhook Path",
                    "type": "text",
                    "placeholder": "/my-webhook",
                    "required": True,
                    "help": "The URL path that will trigger this workflow"
                },
                {
                    "key": "method",
                    "label": "HTTP Method",
                    "type": "select",
                    "options": ["GET", "POST", "PUT"],
                    "default": "POST",
                    "required": True,
                    "help": "Which HTTP method to listen for"
                }
            ]
        )

    async def execute(self, config: Dict[str, Any], inputs: List[List[Item]], context) -> NodeExecutionResult:
        payload = context.trigger_payload or {}
        items = normalize_items(payload)
        return NodeExecutionResult(
            success=True,
            outputs=[items],
            metadata={"path": config.get("path"), "method": config.get("method")}
        )
