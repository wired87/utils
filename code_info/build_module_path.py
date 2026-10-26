
import importlib.util
import os
import sys
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type


def get_project_root(start_path: Optional[str | Path] = None) -> Path:
    """Finds the root directory of the project by scanning upwards for project markers

    (.env, .venv, .git, or pyproject.toml).
    """
    current = Path(start_path or __file__).resolve()
    for parent in current.parents:
        if any(
            (
                (parent / ".env").is_file(),
                (parent / ".venv").is_dir(),
                (parent / ".git").is_dir(),
                (parent / "pyproject.toml").is_file(),
            )
        ):
            return parent
    return current.parents[1] if len(current.parents) > 1 else current


def build_class_module_path(
    file_path: str | Path, root_dir: Optional[str | Path] = None
) -> str:
    """Converts a local filesystem path into a dot-notated Python import path.

    Example: /project/app/components/api.py -> app.components.api
    """
    root = (
        Path(root_dir).resolve()
        if root_dir
        else get_project_root(file_path)
    )
    abs_file = Path(file_path).resolve()

    # Handle __init__.py files cleanly
    if abs_file.name == "__init__.py":
        rel_path = abs_file.parent.relative_to(root)
    else:
        rel_path = abs_file.relative_to(root).with_suffix("")

    parts = [p.replace(".", "_") if "." in p else p for p in rel_path.parts]
    return ".".join(parts)


@lru_cache(maxsize=None)
def resolve_module_symbol(
    module_name: str, symbol_name: Optional[str] = None
) -> Any:
    """Dynamically imports a module by dot-path and returns a named symbol or

    the module itself.
    """
    try:
        module = import_module(module_name)
        if symbol_name:
            return getattr(module, symbol_name, None)
        return module
    except ImportError as e:
        print(f"[ERROR] Could not import module '{module_name}': {e}", file=sys.stderr)
        return None


def extract_callable_or_class(file_path: str | Path) -> Optional[Any]:
    """Pure Python replacement for view extraction.

    Imports a module from its absolute filepath and inspects it for exported callables or classes without requiring Django/DRF subclasses.
    """
    abs_path = Path(file_path).resolve()
    if not abs_path.is_file():
        return None

    module_name = build_class_module_path(abs_path)
    found_export = None

    try:
        # Force a fresh import state
        if module_name in sys.modules:
            del sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(module_name, str(abs_path))
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            if module_name in sys.modules:
                del sys.modules[module_name]
            raise e

        # 1. Primary check: Explicit exported handler/class contract
        explicit_target = getattr(module, "HANDLER", None) or getattr(
            module, "COMPONENT_CLASS", None
        )
        if explicit_target:
            return explicit_target

        # 2. Fallback check: Pick first locally defined class or function
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue
            attr = getattr(module, attr_name)

            if isinstance(attr, (type, Callable)):
                # Match module location to prevent returning third-party imports
                if getattr(attr, "__module__", None) == module_name:
                    return attr
                found_export = found_export or attr

        return found_export

    except Exception as e:
        print(
            f"[ERROR] Failed to extract component from {module_name} ({abs_path}): {e}",
            file=sys.stderr,
        )
        return None


def build_component_registry(
    parent_dir: str | Path, target_filename: str = "api_view.py"
) -> List[Dict[str, Any]]:
    """Discovers target component files inside a root directory without web framework routing.

    Returns a clean dictionary mapping route paths, directory names, and exported components.
    """
    abs_parent = Path(parent_dir).resolve()
    registry = []

    if not abs_parent.exists():
        raise FileNotFoundError(f"Directory '{abs_parent}' does not exist.")

    for root, _, files in os.walk(abs_parent):
        if target_filename in files:
            target_path = Path(root) / target_filename
            rel_path = target_path.parent.relative_to(abs_parent)

            dir_name = target_path.parent.name
            route_path = (
                ""
                if dir_name == "index"
                else str(rel_path).replace(os.sep, "/") + "/"
            )

            component = extract_callable_or_class(target_path)
            module_name = build_class_module_path(target_path)

            if component:
                registry.append(
                    {
                        "route_path": route_path,
                        "dir_name": dir_name,
                        "module_name": module_name,
                        "file_path": str(target_path),
                        "component": component,
                    }
                )
                print(
                    f"[SUCCESS] Registered component: route='{route_path}' | target={getattr(component, '__name__', str(component))}"
                )
            else:
                print(
                    f"[WARN] No component found for route: '{route_path}' ({dir_name})",
                    file=sys.stderr,
                )

    return registry


if __name__ == "__main__":
    # Test path resolution against current script
    current_root = get_project_root()
    mod_path = build_class_module_path(__file__)

    print(f"Project Root : {current_root}")
    print(f"Module Path  : {mod_path}")