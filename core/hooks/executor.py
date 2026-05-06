import logging
logger = logging.getLogger(__name__)

from core.hooks.hook_registry import hook_registry
from core.hooks.result import HookResult
from core.registry import registry

class HookExecutor:
    @staticmethod
    def run(event: str, ctx):
        model_name = getattr(ctx, "model", None)
        module_name = None

        if model_name:
            module_name = registry.model_meta.get(model_name, {}).get("module")
            ctx.module = module_name

        hooks = hook_registry.get(event=event, module=module_name, model=model_name)
        for entry in hooks:
            try:
                result = entry.func(ctx)
                if result and hasattr(result, "allow") and not result.allow:
                    return result
            except Exception as e:
                logger.error(f"Hook failed [{event}] [{entry.name}]: {e}")
                return HookResult(
                    allow=False,
                    message=f"Hook error in {event}: {str(e)}"
                )

        return HookResult(allow=True)
