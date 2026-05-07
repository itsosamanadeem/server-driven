from collections import defaultdict
from types import SimpleNamespace

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
            # Store a plain in-memory snapshot, not SQLAlchemy instances,
            # to avoid DetachedInstanceError after session closes.
            self._cache[field.model].append(
                SimpleNamespace(
                    id=field.id,
                    model=field.model,
                    name=field.name,
                    field_type=field.field_type,
                    required=field.required,
                    relation=field.relation,
                    relation_table=field.relation_table,
                )
            )

    def get_fields(self, model_name: str):
        return self._cache.get(model_name, [])
