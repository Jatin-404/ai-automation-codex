import json
from typing import Any, Dict, List
import httpx
from app.nodes.base import BaseNode, NodeDefinition, NodeExecutionResult, Item
from app.nodes.utils import resolve_expressions


class AiNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="ai_node",
            label="AI Node",
            description="Send data to a local AI model (Ollama) or any OpenAI-compatible API",
            category="ai",
            color="#8b5cf6",
            icon="??",
            inputs=1,
            outputs=1,
            config_schema=[
                {
                    "key": "provider",
                    "label": "AI Provider",
                    "type": "select",
                    "options": ["ollama", "openai_compatible", "simulate"],
                    "default": "simulate",
                    "required": True,
                    "help": "Choose 'simulate' for testing without a real model"
                },
                {
                    "key": "base_url",
                    "label": "API Base URL",
                    "type": "text",
                    "placeholder": "http://localhost:11434",
                    "required": False,
                    "help": "Ollama default: http://localhost:11434 - leave empty for simulation"
                },
                {
                    "key": "api_key",
                    "label": "API Key (for OpenAI-compatible)",
                    "type": "text",
                    "placeholder": "sk-...",
                    "required": False,
                    "help": "Only needed for OpenAI-compatible providers"
                },
                {
                    "key": "model",
                    "label": "Model Name",
                    "type": "text",
                    "placeholder": "llama3",
                    "default": "llama3",
                    "required": False,
                    "help": "The model to use, e.g. llama3, mistral, phi3"
                },
                {
                    "key": "prompt",
                    "label": "System Prompt",
                    "type": "textarea",
                    "placeholder": "You are a helpful assistant. Summarize the following data:",
                    "required": True,
                    "help": "Instructions for the AI. The current item is appended automatically."
                },
                {
                    "key": "temperature",
                    "label": "Temperature (creativity)",
                    "type": "slider",
                    "min": 0,
                    "max": 1,
                    "step": 0.1,
                    "default": 0.7,
                    "required": False,
                    "help": "0 = focused/deterministic, 1 = creative/random"
                }
            ]
        )

    async def execute(self, config: Dict[str, Any], inputs: List[List[Item]], context) -> NodeExecutionResult:
        provider = config.get("provider", "simulate")
        prompt = config.get("prompt", "Process this data:")
        model = config.get("model", "llama3")
        temperature = float(config.get("temperature", 0.7))

        output_items: List[Item] = []
        items = inputs[0] if inputs else []

        for item in items:
            data = item.get("json", {}) if isinstance(item, dict) else {}
            resolved_prompt = resolve_expressions(prompt, data)
            input_text = json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data or "")
            full_prompt = f"{resolved_prompt}\n\n{input_text}"

            if provider == "simulate":
                simulated = (
                    f"[AI Simulation] Processed with model '{model}'.\n"
                    f"Prompt: {str(resolved_prompt)[:80]}...\n"
                    f"Input length: {len(input_text)} chars\n"
                    "Result: This is a simulated AI response. Connect Ollama to get real responses."
                )
                output_items.append({"json": {"response": simulated, "model": model, "simulated": True}})
                continue

            if provider == "ollama":
                base_url = (config.get("base_url") or "http://localhost:11434").rstrip("/")
                try:
                    async with httpx.AsyncClient(timeout=120) as client:
                        response = await client.post(
                            f"{base_url}/api/generate",
                            json={
                                "model": model,
                                "prompt": full_prompt,
                                "temperature": temperature,
                                "stream": False
                            }
                        )
                        if response.is_success:
                            data_resp = response.json()
                            output_items.append({"json": {"response": data_resp.get("response", ""), "model": model}})
                            continue
                        return NodeExecutionResult(success=False, error=f"Ollama returned {response.status_code}: {response.text}")
                except httpx.ConnectError:
                    return NodeExecutionResult(
                        success=False,
                        error=(
                            "Cannot connect to Ollama. "
                            "Make sure Ollama is running: `ollama serve` "
                            f"and the model is pulled: `ollama pull {model}`"
                        )
                    )

            if provider == "openai_compatible":
                base_url = (config.get("base_url") or "http://localhost:11434/v1").rstrip("/")
                api_key = config.get("api_key", "not-needed")
                try:
                    async with httpx.AsyncClient(timeout=120) as client:
                        response = await client.post(
                            f"{base_url}/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}"},
                            json={
                                "model": model,
                                "messages": [{"role": "user", "content": full_prompt}],
                                "temperature": temperature
                            }
                        )
                        if response.is_success:
                            data_resp = response.json()
                            text = data_resp["choices"][0]["message"]["content"]
                            output_items.append({"json": {"response": text, "model": model}})
                            continue
                        return NodeExecutionResult(success=False, error=f"API error: {response.text}")
                except httpx.ConnectError as e:
                    return NodeExecutionResult(success=False, error=f"Connection failed: {str(e)}")

            return NodeExecutionResult(success=False, error=f"Unknown provider: {provider}")

        return NodeExecutionResult(success=True, outputs=[output_items])
