from typing import Any, Dict, List, Optional
from app.engine.graph import WorkflowGraph
from app.engine.context import WorkflowContext
from app.nodes.registry import NodeRegistry
from app.nodes.base import NodeExecutionResult, Item


def _normalize_outputs(outputs: List[List[Item]], expected: int) -> List[List[Item]]:
    if outputs is None:
        outputs = []
    if len(outputs) < expected:
        outputs = outputs + [[] for _ in range(expected - len(outputs))]
    if len(outputs) > expected:
        outputs = outputs[:expected]
    return outputs


def _items_preview(items: List[Item]) -> Any:
    if not items:
        return None
    first = items[0]
    if isinstance(first, dict) and "json" in first:
        return first.get("json")
    return first


class WorkflowExecutor:
    """
    Runs a workflow definition end-to-end.
    Workflow definition format (matches React Flow output):
    {
        "nodes": [ { "id": "1", "type": "webhook_trigger", "data": { "config": {...} } }, ... ],
        "edges": [ { "source": "1", "target": "2", "sourceHandle": "output-0", "targetHandle": "input-0" }, ... ]
    }
    """

    async def execute(
        self,
        workflow: Dict,
        initial_payload: Any = None,
        run_id: Optional[str] = None,
        stop_at_node_id: Optional[str] = None,
    ) -> Dict:
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        if not nodes:
            return {"success": False, "error": "Workflow has no nodes", "log": []}

        try:
            graph = WorkflowGraph(nodes, edges)
            execution_order = graph.topological_order()
        except ValueError as e:
            return {"success": False, "error": str(e), "log": []}

        if stop_at_node_id and stop_at_node_id not in graph.nodes:
            return {
                "success": False,
                "error": f"Node '{stop_at_node_id}' not found in workflow",
                "log": []
            }

        context = WorkflowContext(run_id=run_id, initial_payload=initial_payload)
        context.log("engine", "started", f"Running {len(nodes)} nodes", {"order": execution_order})

        final_output = None
        node_output_previews: Dict[str, Any] = {}

        for node_id in execution_order:
            node_def = graph.nodes[node_id]
            node_type = node_def.get("type")
            node_config = node_def.get("data", {}).get("config", {})
            node_label = node_def.get("data", {}).get("label", node_type)

            try:
                node_class = NodeRegistry.get(node_type)
                node_instance = node_class()
                node_definition = node_class.definition()
            except ValueError as e:
                context.log(node_id, "error", str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "log": context.execution_log,
                    "run_id": context.run_id
                }

            incoming = graph.get_incoming(node_id)
            max_input_index = max([i["target_input"] for i in incoming], default=-1)
            input_slots = max(node_definition.inputs, max_input_index + 1, 0)
            inputs: List[List[Item]] = [[] for _ in range(input_slots)]

            for edge in incoming:
                parent_items = context.get_node_output(edge["source"], edge["source_output"])
                inputs[edge["target_input"]].extend(parent_items)

            has_any_input = any(len(items) > 0 for items in inputs)
            if incoming and not has_any_input and not node_definition.run_on_empty and node_definition.category != "trigger":
                context.log(node_id, "skipped", "No input items")
                continue

            context.log(node_id, "running", f"Executing: {node_label}")

            try:
                result: NodeExecutionResult = await node_instance.execute(
                    config=node_config,
                    inputs=inputs,
                    context=context,
                )
            except Exception as e:
                context.log(node_id, "error", f"Unexpected error: {str(e)}")
                return {
                    "success": False,
                    "error": f"Node '{node_label}' crashed: {str(e)}",
                    "log": context.execution_log,
                    "run_id": context.run_id
                }

            if not result.success:
                context.log(node_id, "error", result.error or "Node failed")
                return {
                    "success": False,
                    "error": f"Node '{node_label}' failed: {result.error}",
                    "log": context.execution_log,
                    "run_id": context.run_id,
                    "node_items": context.node_outputs
                }

            outputs = _normalize_outputs(result.outputs, node_definition.outputs)
            context.set_node_output(node_id, outputs)

            preview = _items_preview(outputs[0])
            if preview is not None:
                node_output_previews[node_id] = preview

            context.log(node_id, "success", f"Completed: {node_label}", {
                "output_counts": [len(o) for o in outputs]
            })

            final_output = [item.get("json", item) for item in outputs[0]] if outputs else None

            if stop_at_node_id and node_id == stop_at_node_id:
                context.log("engine", "stopped", f"Stopped after node {node_id}")
                break

        context.log("engine", "completed", "Workflow finished successfully")

        return {
            "success": True,
            "run_id": context.run_id,
            "final_output": final_output,
            "node_outputs": node_output_previews,
            "node_items": context.node_outputs,
            "log": context.execution_log,
            "stopped": bool(stop_at_node_id),
        }
