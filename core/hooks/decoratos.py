from core.hooks.hook_registry import hook_registry

def hook(event: str, priority: int = 100):
    def decorator(func):
        hook_registry.register(event, func, priority)
        return func
    return decorator