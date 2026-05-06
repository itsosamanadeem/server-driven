from collections import defaultdict
from core.models.ir_fields import IrField

class FieldCache:
    def __init__(self):
        self._cache = defaultdict(list)

    def load(self, db):
        """
        Load all fields from DB into memory
        """     
        records = db.query(IrField).all()
        self._cache.clear()

        for field in records:
            self._cache[field.model].append(field)

    def get_fields(self, model_name: str):
        return self._cache.get(model_name, [])