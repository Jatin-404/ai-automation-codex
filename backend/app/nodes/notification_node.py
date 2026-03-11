import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List
import httpx
from app.nodes.base import BaseNode, NodeDefinition, NodeExecutionResult, Item
from app.nodes.utils import resolve_expressions, json_dumps_safe


class NotificationNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="notification",
            label="Send Notification",
            description="Send an email or Slack message with data from your workflow",
            category="action",
            color="#ec4899",
            icon="??",
            inputs=1,
            outputs=1,
            config_schema=[
                {
                    "key": "channel",
                    "label": "Send via",
                    "type": "select",
                    "options": ["Email (SMTP)", "Slack Webhook"],
                    "default": "Email (SMTP)",
                    "required": True,
                    "help": "Choose how to send the notification"
                },
                {
                    "key": "smtp_host",
                    "label": "SMTP Host",
                    "type": "text",
                    "placeholder": "smtp.gmail.com",
                    "required": False,
                    "help": "Gmail: smtp.gmail.com | Outlook: smtp.office365.com"
                },
                {
                    "key": "smtp_port",
                    "label": "SMTP Port",
                    "type": "number",
                    "default": 587,
                    "required": False,
                    "help": "Usually 587 (TLS) or 465 (SSL)"
                },
                {
                    "key": "smtp_user",
                    "label": "Your Email Address",
                    "type": "text",
                    "placeholder": "you@gmail.com",
                    "required": False,
                    "help": "The email account to send from"
                },
                {
                    "key": "smtp_pass",
                    "label": "App Password",
                    "type": "text",
                    "placeholder": "xxxx xxxx xxxx xxxx",
                    "required": False,
                    "help": "Gmail: create at myaccount.google.com -> Security -> App Passwords"
                },
                {
                    "key": "to_email",
                    "label": "Send To",
                    "type": "text",
                    "placeholder": "colleague@company.com",
                    "required": False,
                    "help": "Recipient email address"
                },
                {
                    "key": "subject",
                    "label": "Email Subject",
                    "type": "text",
                    "placeholder": "Workflow Result",
                    "required": False,
                    "help": "Subject line of the email"
                },
                {
                    "key": "message",
                    "label": "Message",
                    "type": "textarea",
                    "placeholder": "Hello,\n\nHere is the result: {{data}}\n\nRegards",
                    "required": False,
                    "help": "Use {{data}} to include the current item's JSON"
                },
                {
                    "key": "slack_webhook_url",
                    "label": "Slack Webhook URL",
                    "type": "text",
                    "placeholder": "https://hooks.slack.com/services/xxx/yyy/zzz",
                    "required": False,
                    "help": "Get this from: Slack -> Apps -> Incoming Webhooks -> Add New Webhook"
                },
                {
                    "key": "slack_message",
                    "label": "Slack Message",
                    "type": "textarea",
                    "placeholder": "Workflow completed! Result: {{data}}",
                    "required": False,
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
        channel = config.get("channel", "Email (SMTP)")
        items = inputs[0] if inputs else []
        output_items: List[Item] = []

        if channel == "Email (SMTP)":
            host = (config.get("smtp_host") or "").strip()
            port = int(config.get("smtp_port", 587))
            user = (config.get("smtp_user") or "").strip()
            passwd = (config.get("smtp_pass") or "").strip()
            to = (config.get("to_email") or "").strip()

            if not all([host, user, passwd, to]):
                return NodeExecutionResult(success=False, error="Email requires: SMTP Host, Your Email, App Password, and Send To fields")

            for item in items:
                data = item.get("json", {}) if isinstance(item, dict) else {}
                subject = self._render(config.get("subject", "Workflow Notification"), data)
                body = self._render(config.get("message", "Workflow completed.\n\nData: {{data}}"), data)

                try:
                    msg = MIMEMultipart()
                    msg["From"] = user
                    msg["To"] = to
                    msg["Subject"] = subject
                    msg.attach(MIMEText(body, "plain"))

                    with smtplib.SMTP(host, port) as server:
                        server.ehlo()
                        server.starttls()
                        server.login(user, passwd)
                        server.sendmail(user, to, msg.as_string())

                    output_items.append({"json": {"sent": True, "to": to, "subject": subject, "channel": "email"}})
                except smtplib.SMTPAuthenticationError:
                    return NodeExecutionResult(success=False, error="Email login failed. Check your email and App Password.")
                except smtplib.SMTPException as e:
                    return NodeExecutionResult(success=False, error=f"Email error: {str(e)}")
                except Exception as e:
                    return NodeExecutionResult(success=False, error=f"Could not send email: {str(e)}")

            return NodeExecutionResult(success=True, outputs=[output_items])

        if channel == "Slack Webhook":
            webhook_url = (config.get("slack_webhook_url") or "").strip()
            if not webhook_url:
                return NodeExecutionResult(success=False, error="Slack Webhook URL is required")

            async with httpx.AsyncClient(timeout=10) as client:
                for item in items:
                    data = item.get("json", {}) if isinstance(item, dict) else {}
                    message = self._render(config.get("slack_message", "Workflow completed: {{data}}"), data)
                    try:
                        response = await client.post(webhook_url, json={"text": message})
                        if response.status_code == 200:
                            output_items.append({"json": {"sent": True, "channel": "slack", "message": message}})
                        else:
                            return NodeExecutionResult(success=False, error=f"Slack returned {response.status_code}: {response.text}")
                    except Exception as e:
                        return NodeExecutionResult(success=False, error=f"Slack error: {str(e)}")

            return NodeExecutionResult(success=True, outputs=[output_items])

        return NodeExecutionResult(success=False, error=f"Unknown channel: {channel}")
