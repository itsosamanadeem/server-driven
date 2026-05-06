from core.hooks import events
from core.hooks.decoratos import hook
from core.hooks.result import HookResult


@hook(
    events.BEFORE_CREATE,
    scope="module",
    value="employees",
    priority=200,
    name="employees.module_payload_presence",
)
def employees_module_payload_presence(ctx):
    # Applies to any model inside employees module.
    if not isinstance(ctx.data, dict):
        return HookResult(False, "Invalid payload for employees module")
    return HookResult(True)


@hook(
    events.BEFORE_CREATE,
    scope="model",
    value="ir_employee",
    priority=50,
    name="employees.model_require_name",
)
def employee_require_name(ctx):
    # Model-level rule: only runs for ir_employee.
    if not ctx.data.get("employee_name"):
        return HookResult(False, "employee_name is required")
    return HookResult(True)
