from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from app.engine.executor import WorkflowExecutor
from app.scheduler.job_store import (
    add_scheduled_workflow, remove_scheduled_workflow, list_scheduled_jobs
)
from app.engine.webhook_registry import register_webhook, unregister_webhook, list_webhooks

router = APIRouter()


class WorkflowRunRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    payload: Optional[Any] = None


class WorkflowRunNodeRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    node_id: str
    payload: Optional[Any] = None


class ScheduleRequest(BaseModel):
    workflow_id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    interval_type: str
    interval_value: int


class WebhookRegisterRequest(BaseModel):
    path: str
    method: str = "POST"
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class WebhookUnregisterRequest(BaseModel):
    path: str
    method: str = "POST"


# Single shared executor instance
_executor = WorkflowExecutor()


async def _run_scheduled(workflow: Dict):
    """Called by APScheduler every interval."""
    try:
        result = await _executor.execute(workflow)
        status = "✅ success" if result.get("success") else "❌ failed"
        print(f"[Scheduler] {status} | run_id={result.get('run_id', '?')}")
    except Exception as e:
        print(f"[Scheduler] crashed: {e}")


@router.post("/run")
async def run_workflow(request: WorkflowRunRequest):
    result = await _executor.execute(
        workflow={"nodes": request.nodes, "edges": request.edges},
        initial_payload=request.payload
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result)
    return result


@router.post("/run-node")
async def run_single_node(request: WorkflowRunNodeRequest):
    """Run the workflow up to and including a specific node (for Execute Step)."""
    result = await _executor.execute(
        workflow={"nodes": request.nodes, "edges": request.edges},
        initial_payload=request.payload,
        stop_at_node_id=request.node_id
    )
    # Return even on failure so frontend can show per-node output
    return result


@router.post("/schedule")
async def schedule_workflow(request: ScheduleRequest):
    workflow = {"nodes": request.nodes, "edges": request.edges}
    add_scheduled_workflow(
        job_id=request.workflow_id,
        workflow=workflow,
        interval_type=request.interval_type,
        interval_value=request.interval_value,
        execute_fn=_run_scheduled
    )
    return {
        "scheduled": True,
        "workflow_id": request.workflow_id,
        "interval": f"every {request.interval_value} {request.interval_type}"
    }


@router.delete("/schedule/{workflow_id}")
async def unschedule_workflow(workflow_id: str):
    remove_scheduled_workflow(workflow_id)
    return {"stopped": True, "workflow_id": workflow_id}


@router.get("/schedule")
async def get_scheduled_workflows():
    return {"jobs": list_scheduled_jobs()}


@router.post("/webhook/register")
async def register_webhook_workflow(request: WebhookRegisterRequest):
    workflow = {"nodes": request.nodes, "edges": request.edges}
    info = register_webhook(request.path, request.method, workflow)
    return {"registered": True, **info}


@router.post("/webhook/unregister")
async def unregister_webhook_workflow(request: WebhookUnregisterRequest):
    removed = unregister_webhook(request.path, request.method)
    return {"unregistered": removed, "path": request.path, "method": request.method}


@router.get("/webhook")
async def list_registered_webhooks():
    return {"webhooks": list_webhooks()}


@router.post("/validate")
async def validate_workflow(request: WorkflowRunRequest):
    from app.engine.graph import WorkflowGraph
    from app.nodes.registry import NodeRegistry
    errors = []
    for node in request.nodes:
        if node.get("type") not in NodeRegistry.list_nodes():
            errors.append(f"Unknown node type: '{node.get('type')}'")
    try:
        graph = WorkflowGraph(request.nodes, request.edges)
        order = graph.topological_order()
    except ValueError as e:
        errors.append(str(e))
        order = []
    if errors:
        return {"valid": False, "errors": errors}
    return {"valid": True, "execution_order": order}
