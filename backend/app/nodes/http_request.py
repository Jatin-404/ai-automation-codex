import json
from typing import Any, Dict, List
import httpx
from app.nodes.base import BaseNode, NodeDefinition, NodeExecutionResult, Item
from app.nodes.utils import resolve_expressions, resolve_in_object


class HttpRequestNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="http_request",
            label="HTTP Request",
            description="Calls any external API and passes the response to the next node",
            category="action",
            color="#10b981",
            icon="??",
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

    def _parse_json_field(self, raw: str, data: Dict[str, Any]) -> Any:
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError("Must be valid JSON")
        return resolve_in_object(parsed, data)

    async def execute(self, config: Dict[str, Any], inputs: List[List[Item]], context) -> NodeExecutionResult:
        raw_url = (config.get("url") or "").strip()
        method = (config.get("method") or "GET").upper()
        verify_ssl = bool(config.get("verify_ssl", True))

        if not raw_url:
            return NodeExecutionResult(success=False, error="URL is required")

        output_items: List[Item] = []
        items = inputs[0] if inputs else []

        if not items:
            return NodeExecutionResult(success=True, outputs=[[]])

        async with httpx.AsyncClient(timeout=30, verify=verify_ssl, follow_redirects=True) as client:
            for item in items:
                data = item.get("json", {}) if isinstance(item, dict) else {}
                url = resolve_expressions(raw_url, data)
                if isinstance(url, str) and not url.startswith("http://") and not url.startswith("https://"):
                    url = "https://" + url

                headers = {}
                if config.get("headers"):
                    try:
                        headers = self._parse_json_field(config.get("headers"), data)
                    except ValueError:
                        return NodeExecutionResult(success=False, error="Headers must be valid JSON. Example: {\"Authorization\": \"Bearer token\"}")

                body = None
                if config.get("use_input_as_body") and data:
                    body = data
                elif config.get("body"):
                    try:
                        body = self._parse_json_field(config.get("body"), data)
                    except ValueError:
                        return NodeExecutionResult(success=False, error="Body must be valid JSON. Example: {\"key\": \"value\"}")

                try:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=body if body is not None else None,
                    )
                except httpx.TimeoutException:
                    return NodeExecutionResult(success=False, error=f"Request timed out after 30 seconds. Check if the URL is correct and accessible: {url}")
                except httpx.ConnectError:
                    return NodeExecutionResult(success=False, error=f"Could not connect to {url}. Check your internet connection and the URL.")
                except httpx.RequestError as e:
                    return NodeExecutionResult(success=False, error=f"Request failed: {str(e)}")

                try:
                    payload = response.json()
                except Exception:
                    payload = {"body": response.text}

                output_items.append({
                    "json": {
                        "status_code": response.status_code,
                        "ok": response.is_success,
                        "data": payload,
                        "url": url,
                        "method": method,
                    }
                })

                if not response.is_success:
                    return NodeExecutionResult(success=False, error=f"Server returned {response.status_code}")

        return NodeExecutionResult(success=True, outputs=[output_items])
