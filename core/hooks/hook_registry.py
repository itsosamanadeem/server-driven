from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Literal

ScopeType = Literal["global", "module", "model"]


@dataclass(frozen=True)
class HookEntry:
    event: str
    func: Callable
    priority: int
    scope_type: ScopeType
    scope_value: str | None
    name: str


class HookRegistry:
    def __init__(self):
        self._global_hooks = defaultdict(list)
        self._module_hooks = defaultdict(list)
        self._model_hooks = defaultdict(list)
        self._names = set()

    def register(
        self,
        event: str,
        func: Callable,
        priority: int = 100,
        scope_type: ScopeType = "global",
        scope_value: str | None = None,
        name: str | None = None,
    ):
        hook_name = name or f"{func.__module__}.{func.__name__}"
        dedupe_key = (event, hook_name, scope_type, scope_value)
        if dedupe_key in self._names:
            return
        self._names.add(dedupe_key)

        entry = HookEntry(
            event=event,
            func=func,
            priority=priority,
            scope_type=scope_type,
            scope_value=scope_value,
            name=hook_name,
        )

        if scope_type == "global":
            self._global_hooks[event].append(entry)
            self._global_hooks[event].sort(key=lambda x: (x.priority, x.name))
            return

        if scope_type == "module":
            if not scope_value:
                raise ValueError("module scoped hook requires scope_value")
            self._module_hooks[(event, scope_value)].append(entry)
            self._module_hooks[(event, scope_value)].sort(key=lambda x: (x.priority, x.name))
            return

        if scope_type == "model":
            if not scope_value:
                raise ValueError("model scoped hook requires scope_value")
            self._model_hooks[(event, scope_value)].append(entry)
            self._model_hooks[(event, scope_value)].sort(key=lambda x: (x.priority, x.name))
            return

        raise ValueError(f"Unknown scope_type: {scope_type}")

    def get(self, event: str, module: str | None = None, model: str | None = None):
        hooks = list(self._global_hooks.get(event, []))

        if module:
            hooks.extend(self._module_hooks.get((event, module), []))

        if model:
            hooks.extend(self._model_hooks.get((event, model), []))

        hooks.sort(key=lambda x: (x.priority, x.name))
        return hooks


hook_registry = HookRegistry()
