import os
from core.registry.manifest import resolve_dependencies
from core.registry import registry
from core.db.base import Base

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
    for module in ordered:
        registry.load_modules(module)
        
    for cls in Base.registry.mappers: # type: ignore
        model_class = cls.class_
        registry.register_model(model_class.__tablename__, model_class)
        
    registry.setup_models()
    registry.build_meta()    
    registry.finalize()
    