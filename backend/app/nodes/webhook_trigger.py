from typing import Any, Dict
from app.nodes.base import BaseNode, NodeDefinition, NodeResult


class WebhookTriggerNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="webhook_trigger",
            label="Webhook Trigger",
            description="Starts the workflow when an HTTP request arrives at a URL",
            category="trigger",
            color="#3b82f6",
            icon="🔗",
            inputs=0,   # triggers have no input
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

    async def execute(
        self,
        config: Dict[str, Any],
        input_data: Any,
        context: Dict[str, Any]
    ) -> NodeResult:
        # Webhook data is injected into context by the webhook route handler
        webhook_payload = context.get("webhook_payload", {})
        return NodeResult(
            success=True,
            output=webhook_payload,
            metadata={"path": config.get("path"), "method": config.get("method")}
        )