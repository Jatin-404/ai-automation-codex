import json
import re
from typing import Any, Dict, List
from app.nodes.base import BaseNode, NodeDefinition, NodeResult


def resolve_value(value: Any, input_data: Any) -> Any:
    """
    Resolve a value that may contain {{fieldName}} expressions.
    Supports dot notation: {{user.name}}
    """
    if not isinstance(value, str):
        return value

    # Full match = return actual typed value, not string
    full_match = re.fullmatch(r'\{\{([^}]+)\}\}', value.strip())
    if full_match and isinstance(input_data, dict):
        key = full_match.group(1).strip()
        result = get_nested(input_data, key)
        return result if result is not None else value

    # Partial match = string interpolation
    def replacer(match):
        key = match.group(1).strip()
        val = get_nested(input_data, key)
        return str(val) if val is not None else match.group(0)

    return re.sub(r'\{\{([^}]+)\}\}', replacer, value)


def get_nested(data: Any, path: str) -> Any:
    for key in path.split("."):
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


def cast_value(value: Any, field_type: str) -> Any:
    """Cast a value to the specified type."""
    try:
        if field_type == "Number":
            return float(value) if '.' in str(value) else int(value)
        elif field_type == "Boolean":
            if isinstance(value, bool): return value
            return str(value).lower() in ('true', '1', 'yes')
        elif field_type == "String":
            return str(value)
        elif field_type == "Array":
            if isinstance(value, list): return value
            return json.loads(value) if isinstance(value, str) else [value]
        elif field_type == "Object":
            if isinstance(value, dict): return value
            return json.loads(value) if isinstance(value, str) else value
    except Exception:
        pass
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
            icon="✏️",
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
                    # field_mappings is a JSON array managed by the visual UI
                    # Format: [{"name": "myField", "type": "String", "value": "{{joke}}"}]
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

    async def execute(self, config: Dict[str, Any], input_data: Any, context: Dict[str, Any]) -> NodeResult:
        mode        = config.get("mode", "Manual Mapping")
        include_all = config.get("include_input", False)
        raw_mappings = config.get("field_mappings", "[]")

        data = input_data if isinstance(input_data, dict) else {"value": input_data}

        # Parse mappings
        try:
            if isinstance(raw_mappings, list):
                mappings = raw_mappings
            else:
                mappings = json.loads(raw_mappings or "[]")
        except Exception:
            mappings = []

        if not mappings:
            return NodeResult(
                success=False,
                error="No fields defined. Use 'Add Field' or drag a field from the INPUT panel."
            )

        # Build output
        output = {}

        # Include all original fields first if toggled on
        if include_all or mode == "Manual Mapping":
            output = dict(data)

        if mode == "Keep Only Mapped Fields":
            output = {}

        # Apply each mapping
        for mapping in mappings:
            name  = mapping.get("name", "").strip()
            ftype = mapping.get("type", "String")
            value = mapping.get("value", "")

            if not name:
                continue

            resolved = resolve_value(value, data)
            casted   = cast_value(resolved, ftype)
            output[name] = casted

        return NodeResult(success=True, output=output)