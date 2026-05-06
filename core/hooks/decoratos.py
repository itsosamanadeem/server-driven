from core.hooks.hook_registry import hook_registry

def hook(
    event: str,
    priority: int = 100,
    scope: str = "global",
    value: str | None = None,
    name: str | None = None,
):
    def decorator(func):
        hook_registry.register(
            event=event,
            func=func,
            priority=priority,
            scope_type=scope,  # type: ignore[arg-type]
            scope_value=value,
            name=name,
        )
        return func
    return decorator
