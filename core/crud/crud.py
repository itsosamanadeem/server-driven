from sqlalchemy.orm import Session
from core.registry import registry

class CRUD:

    def __init__(self, db: Session):
        self.db = db
        self.meta_cache = {}
        
    def _get_meta(self, obj):
        cls = type(obj)
        if cls not in self.meta_cache:
            self.meta_cache[cls] = registry.model_meta.get(cls.__name__, {})
        return self.meta_cache[cls]
    
    def get_model(self, model_name: str):
        model = registry.get_model(model_name)
        if not model:
            raise Exception(f"Model not found: {model_name}")
        return model

    # 🔹 CREATE
    def create(self, model_name: str, data: dict):
        model = self.get_model(model_name)

        obj = model()

        self._apply_data(obj, data)

        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)

        return obj

    # 🔹 READ (list)
    def search(self, model_name: str):
        model = self.get_model(model_name)
        return self.db.query(model).all()

    # 🔹 READ (single)
    def get(self, model_name: str, record_id: int):
        model = self.get_model(model_name)
        return self.db.query(model).get(record_id)

    # 🔹 UPDATE
    def update(self, model_name: str, record_id: int, data: dict):
        obj = self.get(model_name, record_id)
        if not obj:
            raise Exception("Record not found")

        self._apply_data(obj, data)

        self.db.commit()
        return obj

    # 🔹 DELETE
    def delete(self, model_name: str, record_id: int):
        obj = self.get(model_name, record_id)
        if not obj:
            raise Exception("Record not found")

        self.db.delete(obj)
        self.db.commit()

        return True

    # CORE LOGIC (Relationships handling)
    def _apply_data(self, obj, data: dict):
        """
        Use registry metadata instead of inspect
        """
        cls = type(obj)
        meta = self._get_meta(cls)
        columns = meta.get("columns", {})
        relationships = meta.get("relationships", {})
        print(columns, relationships)
        for key, value in data.items():

            # Skip unknown fields
            if key not in columns and key not in relationships:
                continue

            # 🔹 NORMAL FIELD
            if key in columns:
                setattr(obj, key, value)
                continue

            # 🔹 RELATIONSHIPS
            rel = relationships[key]
            direction = rel["direction"]
            related_model = rel["model"]
            uselist = rel["uselist"]
            secondary = rel["secondary"]

            if direction == "MANYTOONE":
                setattr(obj, key, self.db.get(related_model, value))

            elif secondary or (direction == "MANYTOMANY" and uselist):
                records = self.db.query(related_model).filter(
                    related_model.id.in_(value)
                ).all()
                setattr(obj, key, records)

            elif direction == "ONETOMANY":
                children = []
                for item in value:
                    child = related_model()
                    for k, v in item.items():
                        setattr(child, k, v)
                    children.append(child)
                setattr(obj, key, children)