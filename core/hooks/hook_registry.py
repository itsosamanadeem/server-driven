from collections import defaultdict

class HookRegistry:
    def __init__(self):
        self._hooks = defaultdict(list)

    def register(self, event: str, func, priority: int = 100):
        self._hooks[event].append((priority, func))
        self._hooks[event].sort(key=lambda x: x[0])  # lower = higher priority

    def get(self, event: str):
        return [func for _, func in self._hooks.get(event, [])]


hook_registry = HookRegistry()