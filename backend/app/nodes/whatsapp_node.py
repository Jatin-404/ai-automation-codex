import httpx
from typing import Any, Dict, List
from app.nodes.base import BaseNode, NodeDefinition, NodeExecutionResult, Item
from app.nodes.utils import resolve_expressions, json_dumps_safe


class WhatsAppNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="whatsapp",
            label="WhatsApp",
            description="Send a WhatsApp message via Twilio or WhatsApp Business API",
            category="action",
            color="#25d366",
            icon="??",
            inputs=1,
            outputs=1,
            config_schema=[
                {
                    "key": "provider",
                    "label": "Provider",
                    "type": "select",
                    "options": ["Twilio", "simulate"],
                    "default": "simulate",
                    "required": True,
                    "help": "Choose 'simulate' to test without a real account"
                },
                {
                    "key": "account_sid",
                    "label": "Twilio Account SID",
                    "type": "text",
                    "placeholder": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "required": False,
                    "help": "Find this at console.twilio.com"
                },
                {
                    "key": "auth_token",
                    "label": "Twilio Auth Token",
                    "type": "text",
                    "placeholder": "your_auth_token",
                    "required": False,
                    "help": "Find this at console.twilio.com"
                },
                {
                    "key": "from_number",
                    "label": "From (Twilio WhatsApp number)",
                    "type": "text",
                    "placeholder": "+14155238886",
                    "required": False,
                    "help": "Your Twilio WhatsApp sandbox number"
                },
                {
                    "key": "to_number",
                    "label": "Send To (phone number)",
                    "type": "text",
                    "placeholder": "+919876543210",
                    "required": True,
                    "help": "Include country code, e.g. +91 for India"
                },
                {
                    "key": "message",
                    "label": "Message",
                    "type": "textarea",
                    "placeholder": "Hello! Workflow result: {{data}}",
                    "required": True,
                    "help": "Use {{data}} to include the current item's JSON"
                }
            ]
        )

    def _render(self, template: str, data: Any) -> str:
        if template is None:
            return ""
        rendered = template.replace("{{data}}", json_dumps_safe(data))
        return resolve_expressions(rendered, data if isinstance(data, dict) else {})

    async def execute(self, config: Dict[str, Any], inputs: List[List[Item]], context) -> NodeExecutionResult:
        provider = config.get("provider", "simulate")
        to_number = (config.get("to_number") or "").strip()

        if not to_number:
            return NodeExecutionResult(success=False, error="Phone number is required")

        output_items: List[Item] = []

        for item in (inputs[0] if inputs else []):
            data = item.get("json", {}) if isinstance(item, dict) else {}
            message = self._render(config.get("message", "Workflow result: {{data}}"), data)

            if provider == "simulate":
                output_items.append({"json": {"sent": True, "simulated": True, "to": to_number, "message": message}})
                continue

            if provider == "Twilio":
                sid = (config.get("account_sid") or "").strip()
                token = (config.get("auth_token") or "").strip()
                frm = (config.get("from_number") or "").strip()

                if not all([sid, token, frm]):
                    return NodeExecutionResult(success=False, error="Twilio requires Account SID, Auth Token, and From number")

                try:
                    async with httpx.AsyncClient(timeout=15) as client:
                        response = await client.post(
                            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                            auth=(sid, token),
                            data={
                                "From": f"whatsapp:{frm}",
                                "To": f"whatsapp:{to_number}",
                                "Body": message
                            }
                        )
                        data_resp = response.json()
                        if response.is_success:
                            output_items.append({"json": {"sent": True, "sid": data_resp.get("sid"), "to": to_number}})
                            continue
                        return NodeExecutionResult(success=False, error=f"Twilio error: {data_resp.get('message', response.text)}")
                except Exception as e:
                    return NodeExecutionResult(success=False, error=f"WhatsApp send failed: {str(e)}")

            return NodeExecutionResult(success=False, error=f"Unknown provider: {provider}")

        return NodeExecutionResult(success=True, outputs=[output_items])
