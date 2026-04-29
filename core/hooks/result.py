class HookResult:
    def __init__(self, allow=True, message=None, data=None):
        self.allow = allow
        self.message = message
        self.data = data