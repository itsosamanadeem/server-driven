from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .serializer import DynamicModel
from core.auth.field_access import FieldAccessService
from core.db.connection import session
from core.auth.dependencies import get_current_user
from core.crud.crud import CRUD
from core.crud.serializer import serialize
from modules.base.models.user import User

router = APIRouter()


def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


def _allowed_fields_for_user(user: User, db: Session, model: str, obj) -> set[str]:
    allowed = set()
    for column in obj.__table__.columns:
        if FieldAccessService.can_read_field(user, db, model, column.name):
            allowed.add(column.name)
    return allowed


# 🔹 CREATE
@router.post("/{model}")
def create_record(
    model: str,
    data: DynamicModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crud = CRUD(db, current_user=current_user)
    obj = crud.create(model, data.root)
    allowed = _allowed_fields_for_user(current_user, db, model, obj)
    return serialize(obj, allowed_fields=allowed)


# 🔹 LIST
@router.get("/{model}")
def list_records(
    model: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crud = CRUD(db, current_user=current_user)
    records = crud.search(model)
    return [
        serialize(r, allowed_fields=_allowed_fields_for_user(current_user, db, model, r))
        for r in records
    ]


# 🔹 GET ONE
@router.get("/{model}/{id}")
def get_record(
    model: str,
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crud = CRUD(db, current_user=current_user)
    obj = crud.get(model, id)
    allowed = _allowed_fields_for_user(current_user, db, model, obj)
    return serialize(obj, allowed_fields=allowed)


# 🔹 UPDATE
@router.put("/{model}/{id}")
def update_record(
    model: str,
    id: int,
    data: DynamicModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crud = CRUD(db, current_user=current_user)
    obj = crud.update(model, id, data.root)
    allowed = _allowed_fields_for_user(current_user, db, model, obj)
    return serialize(obj, allowed_fields=allowed)


# 🔹 DELETE
@router.delete("/{model}/{id}")
def delete_record(
    model: str,
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crud = CRUD(db, current_user=current_user)
    crud.delete(model, id)
    return {"status": "deleted"}
