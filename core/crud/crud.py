from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from core.auth.field_access import FieldAccessService
from core.auth.permissions import PermissionService
from core.auth.security import hash_password, is_password_hash
from core.registry import registry
from core.hooks.executor import HookExecutor
from core.hooks import events
from core.hooks.context import HookContext
from core.validators.validator import Validator
from core.audit.audit_service import AuditService
from core.utils.serializer import to_dict

class CRUD:

    def __init__(self, db: Session, current_user=None):
        self.db = db
        self.current_user = current_user
        self.meta_cache = {}

    def _ensure_permission(self, model_name: str, action: str):
        if not self.current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        PermissionService.ensure(self.current_user, model_name, action)

    def _ensure_field_write_access(self, model_name: str, data: dict):
        for field_name in data.keys():
            if not FieldAccessService.can_write_field(self.current_user, self.db, model_name, field_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Write access denied for field '{field_name}' on {model_name}",
                )

    def _prepare_secure_user_payload(self, model_name: str, data: dict) -> dict:
        if model_name != "ir_user":
            return data

        prepared = dict(data)

        # Preferred API contract: accept plain `password`, store only hashed `password_hash`.
        plain_password = prepared.pop("password", None)
        if plain_password:
            prepared["password_hash"] = hash_password(plain_password)

        # Backward compatibility: if caller sends `password_hash` but it is plain text,
        # convert it to a secure hash before persisting.
        incoming_hash = prepared.get("password_hash")
        if incoming_hash and not is_password_hash(incoming_hash):
            prepared["password_hash"] = hash_password(incoming_hash)

        return prepared
        
    def _get_meta(self, obj):
        cls = type(obj)
        if cls not in self.meta_cache:
            self.meta_cache[cls] = registry.model_meta.get(cls.__tablename__, {})
        return self.meta_cache[cls]
    
    def get_model(self, model_name: str):
        model = registry.get_model(model_name)
        if not model:
            raise Exception(f"Model not found: {model_name}")
        return model

    # 🔹 CREATE
    def create(self, model_name: str, data: dict):
        data = self._prepare_secure_user_payload(model_name, data)
        self._ensure_permission(model_name, "create")
        self._ensure_field_write_access(model_name, data)
        model = self.get_model(model_name)
        obj = model()

        ctx = HookContext(
            db=self.db,
            model=model_name,
            obj=obj,
            data=data,
            user=self.current_user,
            action="create",
        )

        try:
            result = HookExecutor.run(events.BEFORE_CREATE, ctx)
            
            if not result.allow:
                self.db.rollback()
                raise Exception(result.message or "Blocked by hook")
            
            Validator.validate(self.db, model_name, data)
            self._apply_data(obj, data)
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)

            ctx.obj = obj
            HookExecutor.run(events.AFTER_CREATE, ctx)
            AuditService.log(
                self.db,
                model_name,
                obj.id,
                "create",
                None,
                to_dict(obj)
            )
            self.db.commit()
            return obj

        except Exception as e:
            self.db.rollback()
            raise

    # 🔹 READ (list)
    def search(self, model_name: str):
        self._ensure_permission(model_name, "read")
        model = self.get_model(model_name)
        return self.db.query(model).all()

    # 🔹 READ (single)
    def get(self, model_name: str, record_id: int):
        self._ensure_permission(model_name, "read")
        model = self.get_model(model_name)
        return self.db.query(model).get(record_id)

    # 🔹 UPDATE
    def update(self, model_name: str, record_id: int, data: dict):
        data = self._prepare_secure_user_payload(model_name, data)
        self._ensure_permission(model_name, "write")
        self._ensure_field_write_access(model_name, data)
        obj = self.get(model_name, record_id)
        if not obj:
            raise Exception("Record not found")

        old_data = to_dict(obj)
        ctx = HookContext(
            db=self.db,
            model=model_name,
            obj=obj,
            data=data,
            user=self.current_user,
            action="write",
        )

        result = HookExecutor.run(events.BEFORE_UPDATE, ctx)
        if not result.allow:
            self.db.rollback()
            raise Exception(result.message or "Blocked by hook")

        self._apply_data(obj, data)

        self.db.commit()
        self.db.refresh(obj)

        HookExecutor.run(events.AFTER_UPDATE, ctx)
        AuditService.log(
            self.db,
            model_name,
            obj.id,
            "update",
            old_data,
            to_dict(obj),
        )
        self.db.commit()
        return obj

    # 🔹 DELETE
    def delete(self, model_name: str, record_id: int):
        self._ensure_permission(model_name, "delete")
        obj = self.get(model_name, record_id)
        if not obj:
            raise Exception("Record not found")
        old_data = to_dict(obj)

        ctx = HookContext(
            db=self.db,
            model=model_name,
            obj=obj,
            user=self.current_user,
            action="delete",
        )

        result = HookExecutor.run(events.BEFORE_DELETE, ctx)
        if not result.allow:
            self.db.rollback()
            raise Exception(result.message or "Blocked by hook")

        self.db.delete(obj)
        self.db.commit()

        HookExecutor.run(events.AFTER_DELETE, ctx)
        AuditService.log(
            self.db,
            model_name,
            record_id,
            "delete",
            old_data,
            None,
        )
        self.db.commit()

        return True

    # CORE LOGIC (Relationships handling)
    def _apply_data(self, obj, data: dict):
        """
        Use registry metadata instead of inspect
        """
        meta = self._get_meta(obj)
        columns = meta.get("columns", {})
        relationships = meta.get("relationships", {})
        # print(columns, relationships)
        for key, value in data.items():

            # Skip unknown fields
            if key not in columns and key not in relationships:
                continue

            # 🔹 NORMAL FIELD
            if key in columns:
                # print(f"Setting attribute {key} to {value} on {cls.__name__}")
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
