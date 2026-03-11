from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict, deque


class WorkflowGraph:
    """
    Builds a Directed Acyclic Graph (DAG) from the React Flow
    nodes + edges payload and resolves execution order.
    """

    def __init__(self, nodes: List[Dict], edges: List[Dict]):
        self.nodes = {n["id"]: n for n in nodes}
        self.edges = edges
        self._adj: Dict[str, List[Tuple[str, int]]] = defaultdict(list)  # source → [(target, sourceHandle)]
        self._in_degree: Dict[str, int] = defaultdict(int)
        self._build()

    def _build(self):
        for edge in self.edges:
            src = edge["source"]
            tgt = edge["target"]
            # sourceHandle may be "output-0" or "output-1" for split nodes
            handle = edge.get("sourceHandle", "output-0") or "output-0"
            try:
                handle_index = int(handle.split("-")[-1])
            except (ValueError, IndexError):
                handle_index = 0
            self._adj[src].append((tgt, handle_index))
            self._in_degree[tgt] += 1

        # Ensure all nodes appear in in_degree map
        for node_id in self.nodes:
            if node_id not in self._in_degree:
                self._in_degree[node_id] = 0

    def get_start_nodes(self) -> List[str]:
        """Nodes with no incoming edges = trigger nodes."""
        return [nid for nid, deg in self._in_degree.items() if deg == 0]

    def get_children(self, node_id: str, output_index: int = 0) -> List[str]:
        """Return child node IDs connected to a specific output handle."""
        return [tgt for tgt, idx in self._adj.get(node_id, []) if idx == output_index]

    def topological_order(self) -> List[str]:
        """Kahn's algorithm — returns nodes in execution order."""
        in_deg = dict(self._in_degree)
        queue = deque(nid for nid, d in in_deg.items() if d == 0)
        order = []

        while queue:
            node_id = queue.popleft()
            order.append(node_id)
            for (child, _) in self._adj.get(node_id, []):
                in_deg[child] -= 1
                if in_deg[child] == 0:
                    queue.append(child)

        if len(order) != len(self.nodes):
            raise ValueError("Workflow contains a cycle — please check your connections.")

        return order

    def get_parent_ids(self, node_id: str) -> List[str]:
        """Return all nodes that connect TO this node."""
        parents = []
        for edge in self.edges:
            if edge["target"] == node_id:
                parents.append(edge["source"])
        return parents