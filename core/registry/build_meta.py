from sqlalchemy.inspection import inspect
from .registry import Registry

import logging
logger = logging.getLogger(__name__)

class BuildMeta(Registry):
    def build_meta(self):
        for name, model_class in self.models.items():
            try:
                mapper = inspect(model_class)
            except Exception as e:
                logger.error(f"Cannot inspect {name}: {e}")
                continue

            columns = {c.key: c for c in mapper.columns}
            relationships = {}

            for r in mapper.relationships:
                relationships[r.key] = {
                    "model": r.mapper.class_,
                    "direction": r.direction.name,
                    "uselist": r.uselist,
                    "secondary": r.secondary is not None,
                }

            self.model_meta[name]["columns"] = columns
            self.model_meta[name]["relationships"] = relationships
            
        logger.info("🔧 Model metadata built")