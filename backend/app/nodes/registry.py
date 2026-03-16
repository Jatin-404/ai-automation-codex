import importlib
import pkgutil
from typing import Dict, List, Type
from app.nodes.base import BaseNode, NodeDefinition


class NodeRegistry:
    """
    Auto-discovers and registers all node plugins.
    To add a new node: just drop a .py file in app/nodes/ — it registers itself.
    """
    _registry: Dict[str, Type[BaseNode]] = {}

    @classmethod
    def discover(cls):
        """Scan the nodes package and import every module."""
        import app.nodes as nodes_pkg
        # Legacy nodes kept on disk but removed from the palette
        skip = {
            "base",
            "registry",
            "__init__",
            "if_condition",
            "split_node",
            "loop_node",
            "merge_node",
        }

        for _, module_name, _ in pkgutil.iter_modules(nodes_pkg.__path__):
            if module_name in skip:
                continue
            try:
                module = importlib.import_module(f"app.nodes.{module_name}")
                # Find all BaseNode subclasses in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseNode)
                        and attr is not BaseNode
                    ):
                        node_def = attr.definition()
                        cls._registry[node_def.type] = attr
                        print(f"  → Registered node: {node_def.type}")
            except Exception as e:
                print(f"  ⚠ Failed to load node module '{module_name}': {e}")

    @classmethod
    def get(cls, node_type: str) -> Type[BaseNode]:
        if node_type not in cls._registry:
            raise ValueError(f"Unknown node type: '{node_type}'. Available: {list(cls._registry.keys())}")
        return cls._registry[node_type]

    @classmethod
    def list_nodes(cls) -> List[str]:
        return list(cls._registry.keys())

    @classmethod
    def get_node_definitions(cls) -> List[dict]:
        """Return all node definitions for the frontend palette."""
        return [cls._registry[t].definition().dict() for t in cls._registry]
