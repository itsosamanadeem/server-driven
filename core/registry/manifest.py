import importlib
import ast
from pathlib import Path

def load_manifest(module_name):
    module = importlib.import_module(f"modules.{module_name}.__manifest__")

    # Preferred explicit styles
    if hasattr(module, "MANIFEST") and isinstance(module.MANIFEST, dict):
        return module.MANIFEST
    if hasattr(module, "__manifest__") and isinstance(module.__manifest__, dict):
        return module.__manifest__

    # Backward compatibility: file contains a top-level dict literal.
    file_path = Path("modules") / module_name / "__manifest__.py"
    source = file_path.read_text(encoding="utf-8")
    parsed = ast.parse(source, filename=str(file_path))

    for node in parsed.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Dict):
            return ast.literal_eval(node.value)

    return {}

def resolve_dependencies(modules):
    resolved = []
    visiting = set()
    visited = set()

    def visit(module):
        if module in visited:
            return

        if module in visiting:
            raise Exception(f"Circular dependency detected: {module}")

        if module not in modules:
            raise Exception(f"Missing dependency: {module}")

        visiting.add(module)

        manifest = load_manifest(module)

        for dep in manifest.get("depends", []):
            visit(dep)

        visiting.remove(module)
        visited.add(module)
        resolved.append(module)

    for m in modules:
        visit(m)

    return resolved
