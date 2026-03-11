import json
from typing import Any, Dict, List
from app.nodes.base import BaseNode, NodeDefinition, NodeExecutionResult, Item
from app.nodes.utils import resolve_expressions


def cast_value(value: Any, field_type: str) -> Any:
    try:
        if field_type == "Number":
            return float(value) if '.' in str(value) else int(value)
        if field_type == "Boolean":
            if isinstance(value, bool):
                return value
            return str(value).lower() in ("true", "1", "yes")
        if field_type == "String":
            return str(value)
        if field_type == "Array":
            if isinstance(value, list):
                return value
            return json.loads(value) if isinstance(value, str) else [value]
        if field_type == "Object":
            if isinstance(value, dict):
                return value
            return json.loads(value) if isinstance(value, str) else value
    except Exception:
        return value
    return value


class SetTransformNode(BaseNode):

    @classmethod
    def definition(cls) -> NodeDefinition:
        return NodeDefinition(
            type="set_transform",
            label="Set / Transform Data",
            description="Add, rename, or update fields in your data without writing code",
            category="action",
            color="#06b6d4",
            icon="??",
            inputs=1,
            outputs=1,
            config_schema=[
                {
                    "key": "mode",
                    "label": "Mode",
                    "type": "select",
                    "options": ["Manual Mapping", "Keep Only Mapped Fields"],
                    "default": "Manual Mapping",
                    "required": True,
                    "help": "Manual Mapping: add/update fields and keep the rest. Keep Only: output only the fields you map."
                },
                {
                    "key": "field_mappings",
                    "label": "field_mappings",
                    "type": "hidden",
                    "default": "[]",
                    "required": False,
                    "help": "Managed by the visual field builder"
                },
                {
                    "key": "include_input",
                    "label": "Include Other Input Fields",
                    "type": "boolean",
                    "default": False,
                    "help": "Pass through all original fields in addition to your mapped fields"
                }
            ]
        )

    async def execute(self, config: Dict[str, Any], inputs: List[List[Item]], context) -> NodeExecutionResult:
        mode = config.get("mode", "Manual Mapping")
        include_all = config.get("include_input", False)
        raw_mappings = config.get("field_mappings", "[]")

        try:
            mappings = raw_mappings if isinstance(raw_mappings, list) else json.loads(raw_mappings or "[]")
        except Exception:
            mappings = []

        if not mappings:
            return NodeExecutionResult(
                success=False,
                error="No fields defined. Use 'Add Field' or drag a field from the INPUT panel."
            )

        output_items: List[Item] = []
        for item in (inputs[0] if inputs else []):
            data = item.get("json", {}) if isinstance(item, dict) else {}

            if include_all or mode == "Manual Mapping":
                output = dict(data)
            else:
                output = {}

            if mode == "Keep Only Mapped Fields":
                output = {}

            for mapping in mappings:
                name = (mapping.get("name", "") or "").strip()
                ftype = mapping.get("type", "String")
                value = mapping.get("value", "")
                if not name:
                    continue

                resolved = resolve_expressions(value, data)
                output[name] = cast_value(resolved, ftype)

            output_items.append({"json": output})

        return NodeExecutionResult(success=True, outputs=[output_items])
