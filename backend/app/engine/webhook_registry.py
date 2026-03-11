from typing import Any, Dict, Optional, Tuple

_registry: Dict[Tuple[str, str], Dict[str, Any]] = {}


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    return path if path.startswith("/") else f"/{path}"


def register_webhook(path: str, method: str, workflow: Dict[str, Any]) -> Dict[str, Any]:
    key = (_normalize_path(path), method.upper())
    _registry[key] = workflow
    return {"path": key[0], "method": key[1]}


def unregister_webhook(path: str, method: str) -> bool:
    key = (_normalize_path(path), method.upper())
    return _registry.pop(key, None) is not None


def get_webhook(path: str, method: str) -> Optional[Dict[str, Any]]:
    return _registry.get((_normalize_path(path), method.upper()))


def list_webhooks() -> list:
    return [{"path": k[0], "method": k[1]} for k in _registry.keys()]
