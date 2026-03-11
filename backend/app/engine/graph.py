from typing import Dict, List, Tuple
from collections import defaultdict, deque


class WorkflowGraph:
    """
    Builds a Directed Acyclic Graph (DAG) from the React Flow
    nodes + edges payload and resolves execution order.
    """

    def __init__(self, nodes: List[Dict], edges: List[Dict]):
        self.nodes = {n["id"]: n for n in nodes}
        self.edges = edges
        self._adj: Dict[str, List[Tuple[str, int]]] = defaultdict(list)  # source -> [(target, source_output_index)]
        self._incoming: Dict[str, List[Dict]] = defaultdict(list)
        self._in_degree: Dict[str, int] = defaultdict(int)
        self._build()

    def _parse_handle_index(self, handle: str, prefix: str) -> int:
        if not handle:
            return 0
        if handle.startswith(prefix):
            handle = handle[len(prefix):]
        try:
            return int(handle.split("-")[-1])
        except (ValueError, IndexError):
            return 0

    def _build(self):
        for edge in self.edges:
            src = edge["source"]
            tgt = edge["target"]
            source_handle = edge.get("sourceHandle", "output-0") or "output-0"
            target_handle = edge.get("targetHandle", "input-0") or "input-0"

            source_index = self._parse_handle_index(source_handle, "output-")
            target_index = self._parse_handle_index(target_handle, "input-")

            self._adj[src].append((tgt, source_index))
            self._incoming[tgt].append({
                "source": src,
                "source_output": source_index,
                "target_input": target_index,
            })
            self._in_degree[tgt] += 1

        for node_id in self.nodes:
            if node_id not in self._in_degree:
                self._in_degree[node_id] = 0

    def get_start_nodes(self) -> List[str]:
        return [nid for nid, deg in self._in_degree.items() if deg == 0]

    def get_children(self, node_id: str, output_index: int = 0) -> List[str]:
        return [tgt for tgt, idx in self._adj.get(node_id, []) if idx == output_index]

    def get_incoming(self, node_id: str) -> List[Dict]:
        return list(self._incoming.get(node_id, []))

    def topological_order(self) -> List[str]:
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
            raise ValueError("Workflow contains a cycle - please check your connections.")

        return order

    def get_parent_ids(self, node_id: str) -> List[str]:
        parents = []
        for edge in self.edges:
            if edge["target"] == node_id:
                parents.append(edge["source"])
        return parents
