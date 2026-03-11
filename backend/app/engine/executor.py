from typing import Any, Dict, List, Optional
from app.engine.graph import WorkflowGraph
from app.engine.context import WorkflowContext
from app.nodes.registry import NodeRegistry


class WorkflowExecutor:
    """
    Runs a workflow definition end-to-end.

    Workflow definition format (matches React Flow output):
    {
        "nodes": [ { "id": "1", "type": "webhook_trigger", "data": { "config": {...} } }, ... ],
        "edges": [ { "source": "1", "target": "2", "sourceHandle": "output-0" }, ... ]
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

        # Build the graph
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

        # Create run context
        context = WorkflowContext(run_id=run_id, initial_payload=initial_payload)
        context.log("engine", "started", f"Running {len(nodes)} nodes", {"order": execution_order})

        final_output = None
        skipped_nodes = set()

        for node_id in execution_order:
            if node_id in skipped_nodes:
                parent_ids = graph.get_parent_ids(node_id)
                has_live_parent = any(pid in context.node_outputs for pid in parent_ids)
                if not has_live_parent:
                    context.log(node_id, "skipped", "Node was skipped by a branch condition")
                    continue
                skipped_nodes.discard(node_id)

            node_def = graph.nodes[node_id]
            node_type = node_def.get("type")
            node_config = node_def.get("data", {}).get("config", {})
            node_label = node_def.get("data", {}).get("label", node_type)

            context.log(node_id, "running", f"Executing: {node_label}")

            # Get the node plugin
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

            # Resolve input: gather parent outputs
            parent_ids = graph.get_parent_ids(node_id)
            input_data = None
            if parent_ids:
                parent_outputs = []
                for parent_id in parent_ids:
                    parent_output = context.get_node_output(parent_id)
                    if isinstance(parent_output, dict) and "data" in parent_output and "branch" in parent_output:
                        parent_output = parent_output.get("data")
                    parent_outputs.append(parent_output)

                expects_multi = (node_definition.inputs or 0) > 1 or node_type == "merge"
                if expects_multi or len(parent_outputs) > 1:
                    input_data = parent_outputs
                else:
                    input_data = parent_outputs[0]

            # Execute
            try:
                result = await node_instance.execute(
                    config=node_config,
                    input_data=input_data,
                    context=context.to_dict()
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
                    "node_outputs": context.node_outputs
                }

            context.set_node_output(node_id, result.output)
            context.log(node_id, "success", f"Completed: {node_label}", result.output)
            final_output = result.output

            # Handle branching by output index
            output_index = None
            if isinstance(result.metadata, dict):
                output_index = result.metadata.get("output_index")

            if isinstance(output_index, int) and (node_definition.outputs or 0) > 1:
                for idx in range(node_definition.outputs):
                    if idx == output_index:
                        continue
                    skipped_nodes.update(graph.get_children(node_id, output_index=idx))
                context.log(node_id, "branch", f"Taking output {output_index}")

            if stop_at_node_id and node_id == stop_at_node_id:
                context.log("engine", "stopped", f"Stopped after node {node_id}")
                break

        context.log("engine", "completed", "Workflow finished successfully")

        return {
            "success": True,
            "run_id": context.run_id,
            "final_output": final_output,
            "node_outputs": context.node_outputs,
            "log": context.execution_log,
            "stopped": bool(stop_at_node_id),
        }
