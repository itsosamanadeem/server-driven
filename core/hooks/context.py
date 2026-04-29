class HookContext:
    def __init__(self, db, model, obj=None, data=None, user=None, action=None):
        self.db = db
        self.model = model
        self.obj = obj
        self.data = data
        self.user = user
        self.action=action
        self.errors = []
        self.meta = {}