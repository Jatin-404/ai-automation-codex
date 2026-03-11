from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
from app.nodes.base import Item


class WorkflowContext:
    """
    Carries state throughout a single workflow run.
    Stores per-node outputs as n8n-style items.
    """

    def __init__(self, run_id: Optional[str] = None, initial_payload: Any = None):
        self.run_id: str = run_id or str(uuid.uuid4())
        self.started_at: str = datetime.utcnow().isoformat()
        self.variables: Dict[str, Any] = {}
        self.node_outputs: Dict[str, List[List[Item]]] = {}
        self.execution_log: list = []
        self.trigger_payload: Any = initial_payload

    def set_node_output(self, node_id: str, outputs: List[List[Item]]):
        self.node_outputs[node_id] = outputs

    def get_node_output(self, node_id: str, output_index: int = 0) -> List[Item]:
        outputs = self.node_outputs.get(node_id, [])
        if output_index < 0 or output_index >= len(outputs):
            return []
        return outputs[output_index]

    def log(self, node_id: str, status: str, message: str, data: Any = None):
        self.execution_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "node_id": node_id,
            "status": status,
            "message": message,
            "data": data
        })

    def to_public_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "variables": self.variables,
            "trigger_payload": self.trigger_payload,
        }
