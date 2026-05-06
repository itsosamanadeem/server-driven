import logging

from core.hooks import events
from core.hooks.decoratos import hook
from core.hooks.result import HookResult

logger = logging.getLogger(__name__)


@hook(events.BEFORE_CREATE, scope="global", priority=1000, name="base.global_before_create_trace")
def global_before_create_trace(ctx):
    # Global hooks should never assume model-specific fields.
    logger.debug(
        "Global hook before_create model=%s module=%s action=%s",
        ctx.model,
        ctx.module,
        ctx.action,
    )
    return HookResult(True)
