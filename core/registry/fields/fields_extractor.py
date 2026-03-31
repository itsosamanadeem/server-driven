from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy import inspect
from core.registry import registry
import logging
logger = logging.getLogger(__name__)

def extract_fields():
    all_fields = []
    # registry = Registry()
    
    for model_name, model_class in registry.models.items():
        if not isinstance(model_class, DeclarativeMeta):
            continue
        
        if not hasattr(model_class, "__table__"):
            continue
        
        try:
            mapper = inspect(model_class)
        except Exception as e:
            logger.error(e)
            
        # 🔹 1. Handle columns (many2one + basic fields)
        for column in mapper.columns:
            field_type = str(column.type)

            relation = None

            if column.foreign_keys:
                fk = list(column.foreign_keys)[0]
                relation = fk.target_fullname.split(".")[0]

                field_type = "many2one"

            all_fields.append({
                "model": model_name,
                "name": column.key,
                "field_type": field_type,
                "required": not column.nullable,
                "relation": relation,
                "relation_table": None
            })

        # 🔹 2. Handle relationships
        for rel in mapper.relationships:

            rel_type = None

            if rel.direction.name == "MANYTOONE":
                continue  # already handled via FK

            elif rel.direction.name == "ONETOMANY":
                rel_type = "one2many"

            elif rel.direction.name == "MANYTOMANY":
                rel_type = "many2many"

            all_fields.append({
                "model": model_name,
                "name": rel.key,
                "field_type": rel_type,
                "required": False,
                "relation": rel.mapper.class_.__tablename__,
                "relation_table": (
                    rel.secondary.name if rel.secondary is not None else None
                )
            })

    return all_fields