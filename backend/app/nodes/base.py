from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NodeConfig(BaseModel):
    """Configuration schema for a node instance."""
    node_id: str
    node_type: str
    label: str
    config: Dict[str, Any] = Field(default_factory=dict)


class NodeResult(BaseModel):
    """Standard output every node must return."""
    success: bool
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NodeDefinition(BaseModel):
    """Describes a node type to the frontend (palette + config form)."""
    type: str
    label: str
    description: str
    category: str          # "trigger", "action", "logic", "ai"
    color: str             # hex color for the node card
    icon: str              # emoji or icon name
    config_schema: List[Dict[str, Any]] = Field(default_factory=list)   # fields the user fills in
    inputs: int = 1        # number of input handles
    outputs: int = 1       # number of output handles


class BaseNode(ABC):
    """
    Every node plugin must inherit from this class.
    Implementing execute() is the only requirement.
    """

    @classmethod
    @abstractmethod
    def definition(cls) -> NodeDefinition:
        """Return metadata about this node type."""
        ...

    @abstractmethod
    async def execute(
        self,
        config: Dict[str, Any],
        input_data: Any,
        context: Dict[str, Any]
    ) -> NodeResult:
        """
        Run the node logic.

        Args:
            config:     User-provided configuration from the UI
            input_data: Output from the previous node
            context:    Shared workflow context (run_id, variables, etc.)

        Returns:
            NodeResult with success flag and output data
        """
        ...
