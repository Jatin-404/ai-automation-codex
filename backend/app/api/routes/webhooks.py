from fastapi import APIRouter, Request
from typing import Any
from app.engine.executor import WorkflowExecutor
from app.engine.webhook_registry import get_webhook

router = APIRouter()
_executor = WorkflowExecutor()

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def receive_webhook(path: str, request: Request):
    """
    Catch-all webhook receiver.
    In MVP: returns the payload so it can be manually injected.
    Future: look up registered workflows for this path and auto-trigger them.
    """
    try:
        body = await request.json()
    except Exception:
        body = await request.body()
        body = body.decode() if body else None

    full_path = f"/{path}"
    workflow = get_webhook(full_path, request.method)

    if workflow:
        result = await _executor.execute(
            workflow=workflow,
            initial_payload=body
        )
        return result

    return {
        "received": True,
        "path": full_path,
        "method": request.method,
        "payload": body,
        "headers": dict(request.headers)
    }
