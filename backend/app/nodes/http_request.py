import json
from typing import Any, Dict
import httpx
from app.nodes.base import BaseNode, NodeDefinition, NodeResult


class HttpRequestNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="http_request",
            label="HTTP Request",
            description="Calls any external API and passes the response to the next node",
            category="action",
            color="#10b981",
            icon="🌐",
            inputs=1,
            outputs=1,
            config_schema=[
                {
                    "key": "url",
                    "label": "URL",
                    "type": "text",
                    "placeholder": "https://api.example.com/data",
                    "required": True,
                    "help": "The API endpoint to call"
                },
                {
                    "key": "method",
                    "label": "Method",
                    "type": "select",
                    "options": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                    "default": "GET",
                    "required": True,
                    "help": "HTTP method to use"
                },
                {
                    "key": "headers",
                    "label": "Headers (JSON)",
                    "type": "textarea",
                    "placeholder": '{"Authorization": "Bearer YOUR_TOKEN"}',
                    "required": False,
                    "help": "Optional request headers as JSON"
                },
                {
                    "key": "body",
                    "label": "Request Body (JSON)",
                    "type": "textarea",
                    "placeholder": '{"key": "value"}',
                    "required": False,
                    "help": "Optional body for POST/PUT requests"
                },
                {
                    "key": "use_input_as_body",
                    "label": "Use previous node output as body",
                    "type": "boolean",
                    "default": False,
                    "help": "Forward the previous node's output as the request body"
                },
                {
                    "key": "verify_ssl",
                    "label": "Verify SSL certificate",
                    "type": "boolean",
                    "default": True,
                    "help": "Disable only if you're calling a trusted server with a self-signed certificate"
                }
            ]
        )

    async def execute(
        self,
        config: Dict[str, Any],
        input_data: Any,
        context: Dict[str, Any]
    ) -> NodeResult:
        url = config.get("url", "").strip()
        method = config.get("method", "GET").upper()

        if not url:
            return NodeResult(success=False, error="URL is required")

        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        # Parse headers
        headers = {}
        if config.get("headers"):
            try:
                headers = json.loads(config["headers"])
            except json.JSONDecodeError:
                return NodeResult(success=False, error="Headers must be valid JSON. Example: {\"Authorization\": \"Bearer token\"}")

        # Determine body
        body = None
        if config.get("use_input_as_body") and input_data:
            body = input_data
        elif config.get("body"):
            try:
                body = json.loads(config["body"])
            except json.JSONDecodeError:
                return NodeResult(success=False, error="Body must be valid JSON. Example: {\"key\": \"value\"}")

        verify_ssl = config.get("verify_ssl", True)

        try:
            async with httpx.AsyncClient(
                timeout=30,
                verify=bool(verify_ssl),
                follow_redirects=True
            ) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if body else None
                )
                try:
                    output = response.json()
                except Exception:
                    output = response.text

                return NodeResult(
                    success=response.is_success,
                    output=output,
                    error=None if response.is_success else f"Server returned {response.status_code}",
                    metadata={
                        "status_code": response.status_code,
                        "url": url,
                        "method": method
                    }
                )

        except httpx.TimeoutException:
            return NodeResult(
                success=False,
                error=f"Request timed out after 30 seconds. Check if the URL is correct and accessible: {url}"
            )
        except httpx.ConnectError:
            return NodeResult(
                success=False,
                error=f"Could not connect to {url}. Check your internet connection and the URL."
            )
        except httpx.RequestError as e:
            return NodeResult(
                success=False,
                error=f"Request failed: {str(e)}"
            )
