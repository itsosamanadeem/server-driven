import os
import importlib

def load_manifest(module_name):
    module = importlib.import_module(f"modules.{module_name}.__manifest__")
    return module.__dict__

def resolve_dependencies(modules):
    
    resolved = []
    seen = set()

    def visit(module):
        if module in seen:
            return
        seen.add(module)

        manifest = load_manifest(module)
        
        for dep in manifest.get("depends", []):
            visit(dep)

        resolved.append(module)

    for m in modules:
        visit(m)

    return resolved