import logging
logger = logging.getLogger(__name__)

from core.hooks.hook_registry import hook_registry
from core.hooks.result import HookResult

class HookExecutor:
    @staticmethod
    def run(event: str, ctx):
        hooks = hook_registry.get(event)
        for hook in hooks:
            try:
                result = hook(ctx)
                if result and hasattr(result, "allow") and not result.allow:
                    return result
            except Exception as e:
                logger.error(f"Hook failed [{event}]: {e}")
                return HookResult(
                    allow=False,
                    message=f"Hook error in {event}: {str(e)}"
                )

        return HookResult(allow=True)