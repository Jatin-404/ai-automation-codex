import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict
import httpx
from app.nodes.base import BaseNode, NodeDefinition, NodeResult


class NotificationNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="notification",
            label="Send Notification",
            description="Send an email or Slack message with data from your workflow",
            category="action",
            color="#ec4899",
            icon="🔔",
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
                # --- Email fields ---
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
                    "help": "Gmail: create at myaccount.google.com → Security → App Passwords"
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
                    "help": "Use {{data}} to include the previous node's output in the message"
                },
                # --- Slack fields ---
                {
                    "key": "slack_webhook_url",
                    "label": "Slack Webhook URL",
                    "type": "text",
                    "placeholder": "https://hooks.slack.com/services/xxx/yyy/zzz",
                    "required": False,
                    "help": "Get this from: Slack → Apps → Incoming Webhooks → Add New Webhook"
                },
                {
                    "key": "slack_message",
                    "label": "Slack Message",
                    "type": "textarea",
                    "placeholder": "Workflow completed! Result: {{data}}",
                    "required": False,
                    "help": "Use {{data}} to include the previous node's output"
                }
            ]
        )

    def _fill_template(self, template: str, data: Any) -> str:
        """Replace {{data}} in template with actual data."""
        import json
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, indent=2)
        else:
            data_str = str(data)
        return template.replace("{{data}}", data_str)

    async def execute(self, config: Dict[str, Any], input_data: Any, context: Dict[str, Any]) -> NodeResult:
        channel = config.get("channel", "Email (SMTP)")

        if channel == "Email (SMTP)":
            return await self._send_email(config, input_data)
        elif channel == "Slack Webhook":
            return await self._send_slack(config, input_data)
        else:
            return NodeResult(success=False, error=f"Unknown channel: {channel}")

    async def _send_email(self, config: Dict, input_data: Any) -> NodeResult:
        host    = config.get("smtp_host", "").strip()
        port    = int(config.get("smtp_port", 587))
        user    = config.get("smtp_user", "").strip()
        passwd  = config.get("smtp_pass", "").strip()
        to      = config.get("to_email", "").strip()
        subject = config.get("subject", "Workflow Notification")
        body    = self._fill_template(config.get("message", "Workflow completed.\n\nData: {{data}}"), input_data)

        if not all([host, user, passwd, to]):
            return NodeResult(success=False, error="Email requires: SMTP Host, Your Email, App Password, and Send To fields")

        try:
            msg = MIMEMultipart()
            msg["From"]    = user
            msg["To"]      = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(host, port) as server:
                server.ehlo()
                server.starttls()
                server.login(user, passwd)
                server.sendmail(user, to, msg.as_string())

            return NodeResult(
                success=True,
                output={"sent": True, "to": to, "subject": subject, "channel": "email"},
                metadata={"channel": "email"}
            )
        except smtplib.SMTPAuthenticationError:
            return NodeResult(success=False, error="Email login failed. Check your email and App Password.")
        except smtplib.SMTPException as e:
            return NodeResult(success=False, error=f"Email error: {str(e)}")
        except Exception as e:
            return NodeResult(success=False, error=f"Could not send email: {str(e)}")

    async def _send_slack(self, config: Dict, input_data: Any) -> NodeResult:
        webhook_url = config.get("slack_webhook_url", "").strip()
        message     = self._fill_template(config.get("slack_message", "Workflow completed: {{data}}"), input_data)

        if not webhook_url:
            return NodeResult(success=False, error="Slack Webhook URL is required")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(webhook_url, json={"text": message})
                if response.status_code == 200:
                    return NodeResult(
                        success=True,
                        output={"sent": True, "channel": "slack", "message": message},
                        metadata={"channel": "slack"}
                    )
                else:
                    return NodeResult(success=False, error=f"Slack returned {response.status_code}: {response.text}")
        except Exception as e:
            return NodeResult(success=False, error=f"Slack error: {str(e)}")