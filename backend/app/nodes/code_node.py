import json
import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict
from app.nodes.base import BaseNode, NodeDefinition, NodeResult


class CodeNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="code_node",
            label="Code (JavaScript)",
            description="Write custom JavaScript to transform or process your data",
            category="action",
            color="#eab308",
            icon="</> ",
            inputs=1,
            outputs=1,
            config_schema=[
                {
                    "key": "code",
                    "label": "JavaScript Code",
                    "type": "textarea",
                    "placeholder": "// 'input' contains the previous node's output\n// Return the value you want to pass forward\n\nreturn {\n  message: 'Hello ' + input.name,\n  timestamp: new Date().toISOString()\n}",
                    "required": True,
                    "help": "Use 'input' to access previous node data. Whatever you return() is passed to the next node. Requires Node.js for real JavaScript."
                },
                {
                    "key": "timeout_ms",
                    "label": "Timeout (milliseconds)",
                    "type": "number",
                    "default": 5000,
                    "min": 100,
                    "max": 30000,
                    "required": False,
                    "help": "Max time allowed to run (default 5000ms = 5 seconds)"
                }
            ]
        )

    def _run_js(self, code: str, input_data: Any, timeout_ms: int) -> NodeResult:
        if not shutil.which("node"):
            return NodeResult(
                success=False,
                error="Node.js is not installed. Install Node.js to run JavaScript code.",
            )

        input_json = json.dumps(input_data, default=str)
        script = (
            "const input = JSON.parse(process.env.INPUT_JSON || 'null');\n"
            "async function __user(input) {\n"
            f"{code}\n"
            "}\n"
            "Promise.resolve(__user(input)).then((result) => {\n"
            "  process.stdout.write(JSON.stringify({ success: true, result }));\n"
            "}).catch((err) => {\n"
            "  process.stdout.write(JSON.stringify({ success: false, error: String(err) }));\n"
            "  process.exitCode = 1;\n"
            "});\n"
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".js", mode="w", encoding="utf-8") as tmp:
            tmp.write(script)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["node", tmp_path],
                capture_output=True,
                text=True,
                timeout=max(timeout_ms, 100) / 1000,
                env={**os.environ, "INPUT_JSON": input_json},
            )
        except subprocess.TimeoutExpired:
            return NodeResult(success=False, error=f"Code execution timed out after {timeout_ms} ms.")
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        stdout = (result.stdout or "").strip()
        if not stdout:
            return NodeResult(
                success=False,
                error=(result.stderr or "No output returned from Node.js."),
            )

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            return NodeResult(success=False, error=f"Invalid response from Node.js: {stdout}")

        if not payload.get("success"):
            return NodeResult(success=False, error=payload.get("error", "Unknown JS error"))

        return NodeResult(success=True, output=payload.get("result"))

    async def execute(self, config: Dict[str, Any], input_data: Any, context: Dict[str, Any]) -> NodeResult:
        code = config.get("code", "").strip()
        if not code:
            return NodeResult(success=False, error="No code provided")

        timeout_ms = int(config.get("timeout_ms", 5000))

        # Prefer real JavaScript via Node.js if available
        js_result = self._run_js(code, input_data, timeout_ms)
        if js_result.success:
            return js_result
        if js_result.error and "Node.js is not installed" not in js_result.error:
            return js_result

        # Fallback: run a limited Python-like shim for simple transformations
        try:
            import ast

            # Build a safe execution context
            safe_globals = {
                "__builtins__": {},
                "input": input_data,
                "json": json,
                "str": str, "int": int, "float": float,
                "bool": bool, "list": list, "dict": dict,
                "len": len, "range": range, "enumerate": enumerate,
                "zip": zip, "map": map, "filter": filter,
                "sorted": sorted, "reversed": reversed,
                "min": min, "max": max, "sum": sum,
                "print": print,
            }

            # Wrap code in a function to support return statements
            wrapped = "def _user_fn(input):\n"
            for line in code.split("\n"):
                # Skip JS-specific syntax
                line = line.replace("const ", "").replace("let ", "").replace("var ", "")
                line = line.replace("===", "==").replace("!==", "!=")
                line = line.replace("true", "True").replace("false", "False").replace("null", "None")
                wrapped += f"    {line}\n"
            wrapped += "\n_result = _user_fn(input)\n"

            local_vars = {"input": input_data}
            exec(wrapped, safe_globals, local_vars)
            result = local_vars.get("_result")

            return NodeResult(success=True, output=result)

        except Exception as e:
            return NodeResult(
                success=False,
                error=(
                    f"Code error: {str(e)}\n\n"
                    "Tip: Install Node.js for real JavaScript support or use simple Python-style code."
                )
            )
