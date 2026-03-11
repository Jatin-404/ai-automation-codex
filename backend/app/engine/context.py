from typing import Any, Dict, Optional
from datetime import datetime
import uuid


class WorkflowContext:
    """
    Carries state throughout a single workflow run.
    Each node reads from and writes to this context.
    """

    def __init__(self, run_id: Optional[str] = None, initial_payload: Any = None):
        self.run_id: str = run_id or str(uuid.uuid4())
        self.started_at: str = datetime.utcnow().isoformat()
        self.variables: Dict[str, Any] = {}
        self.node_outputs: Dict[str, Any] = {}   # node_id → output
        self.execution_log: list = []
        self.webhook_payload: Any = initial_payload

    def set_node_output(self, node_id: str, output: Any):
        self.node_outputs[node_id] = output

    def get_node_output(self, node_id: str) -> Any:
        return self.node_outputs.get(node_id)

    def log(self, node_id: str, status: str, message: str, data: Any = None):
        self.execution_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "node_id": node_id,
            "status": status,
            "message": message,
            "data": data
        })

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "node_outputs": self.node_outputs,
            "execution_log": self.execution_log,
            "variables": self.variables,
            "webhook_payload": self.webhook_payload,
        }
