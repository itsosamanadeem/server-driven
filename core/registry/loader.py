import os
from core.registry.manifest import resolve_dependencies
from core.registry.build_meta import BuildMeta

registry = BuildMeta()

def discover_modules():
    modules = []
    
    for name in os.listdir("modules"):
        path = f"modules/{name}"
        
        if not os.path.isdir(path):
            continue
        if os.path.exists(f"{path}/__manifest__.py"):
            modules.append(name)
    return modules

def load_all():
    modules = discover_modules()
    ordered = resolve_dependencies(modules)

    registry.modules = ordered
    registry.load_modules(ordered)
    registry.build_meta()
    registry.setup_models()
    registry.finalize()
    