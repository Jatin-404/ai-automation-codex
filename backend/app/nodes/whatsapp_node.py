import httpx
from typing import Any, Dict
from app.nodes.base import BaseNode, NodeDefinition, NodeResult


class WhatsAppNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="whatsapp",
            label="WhatsApp",
            description="Send a WhatsApp message via Twilio or WhatsApp Business API",
            category="action",
            color="#25d366",
            icon="💬",
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
                    "help": "Use {{data}} to include the previous node's output"
                }
            ]
        )

    def _fill_template(self, template: str, data: Any) -> str:
        import json
        data_str = json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)
        return template.replace("{{data}}", data_str)

    async def execute(self, config: Dict[str, Any], input_data: Any, context: Dict[str, Any]) -> NodeResult:
        provider   = config.get("provider", "simulate")
        to_number  = config.get("to_number", "").strip()
        message    = self._fill_template(config.get("message", "Workflow result: {{data}}"), input_data)

        if not to_number:
            return NodeResult(success=False, error="Phone number is required")

        if provider == "simulate":
            return NodeResult(
                success=True,
                output={"sent": True, "simulated": True, "to": to_number, "message": message},
                metadata={"provider": "simulate"}
            )

        if provider == "Twilio":
            sid   = config.get("account_sid", "").strip()
            token = config.get("auth_token", "").strip()
            frm   = config.get("from_number", "").strip()

            if not all([sid, token, frm]):
                return NodeResult(success=False, error="Twilio requires Account SID, Auth Token, and From number")

            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    response = await client.post(
                        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                        auth=(sid, token),
                        data={
                            "From": f"whatsapp:{frm}",
                            "To":   f"whatsapp:{to_number}",
                            "Body": message
                        }
                    )
                    data = response.json()
                    if response.is_success:
                        return NodeResult(
                            success=True,
                            output={"sent": True, "sid": data.get("sid"), "to": to_number},
                            metadata={"provider": "twilio"}
                        )
                    else:
                        return NodeResult(success=False, error=f"Twilio error: {data.get('message', response.text)}")
            except Exception as e:
                return NodeResult(success=False, error=f"WhatsApp send failed: {str(e)}")

        return NodeResult(success=False, error=f"Unknown provider: {provider}")