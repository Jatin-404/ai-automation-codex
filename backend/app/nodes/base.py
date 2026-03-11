from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

Item = Dict[str, Any]  # n8n-style item: {"json": {...}}

if TYPE_CHECKING:
    from app.engine.context import WorkflowContext as NodeExecutionContext


def ensure_item(value: Any) -> Item:
    if isinstance(value, dict) and "json" in value and len(value) == 1:
        return value
    if isinstance(value, dict):
        return {"json": value}
    return {"json": {"value": value}}


def normalize_items(value: Any) -> List[Item]:
    if value is None:
        return []
    if isinstance(value, list):
        return [ensure_item(v) for v in value]
    return [ensure_item(value)]


class NodeConfig(BaseModel):
    node_id: str
    node_type: str
    label: str
    config: Dict[str, Any] = Field(default_factory=dict)


class NodeExecutionResult(BaseModel):
    success: bool
    outputs: List[List[Item]] = Field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeDefinition(BaseModel):
    type: str
    label: str
    description: str
    category: str          # "trigger", "action", "logic", "ai"
    color: str             # hex color for the node card
    icon: str              # emoji or icon name
    config_schema: List[Dict[str, Any]] = Field(default_factory=list)
    inputs: int = 1
    outputs: int = 1
    run_on_empty: bool = False  # allow execution with no input items


class BaseNode(ABC):
    @classmethod
    @abstractmethod
    def definition(cls) -> NodeDefinition:
        ...

    @abstractmethod
    async def execute(
        self,
        config: Dict[str, Any],
        inputs: List[List[Item]],
        context: "NodeExecutionContext",
    ) -> NodeExecutionResult:
        ...
