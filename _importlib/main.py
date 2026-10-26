# Dynamischer Pfad je nach OS
import importlib

import importlib.util
import sys
from pathlib import Path


def get_py_module_content(class_name: str, py_module_path: str):
    
    module_path = Path(py_module_path).resolve()
    module_name = module_path.stem + "_dynamic"

    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return getattr(module, class_name)
