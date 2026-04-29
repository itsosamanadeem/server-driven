import os
import importlib

def load_manifest(module_name):
    module = importlib.import_module(f"modules.{module_name}.__manifest__")
    return module.__dict__

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