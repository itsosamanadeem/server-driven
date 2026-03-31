from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .serializer import DynamicModel
from core.db.connection import session
from core.crud.crud import CRUD
from core.crud.serializer import serialize

router = APIRouter()


def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


# 🔹 CREATE
@router.post("/{model}")
def create_record(model: str, data: DynamicModel, db: Session = Depends(get_db)):
    crud = CRUD(db)
    obj = crud.create(model, data.root)
    return serialize(obj)


# 🔹 LIST
@router.get("/{model}")
def list_records(model: str, db: Session = Depends(get_db)):
    crud = CRUD(db)
    records = crud.search(model)
    return [serialize(r) for r in records]


# 🔹 GET ONE
@router.get("/{model}/{id}")
def get_record(model: str, id: int, db: Session = Depends(get_db)):
    crud = CRUD(db)
    obj = crud.get(model, id)
    return serialize(obj)


# 🔹 UPDATE
@router.put("/{model}/{id}")
def update_record(model: str, id: int, data: DynamicModel, db: Session = Depends(get_db)):
    crud = CRUD(db)
    obj = crud.update(model, id, data.root)
    return serialize(obj)


# 🔹 DELETE
@router.delete("/{model}/{id}")
def delete_record(model: str, id: int, db: Session = Depends(get_db)):
    crud = CRUD(db)
    crud.delete(model, id)
    return {"status": "deleted"}