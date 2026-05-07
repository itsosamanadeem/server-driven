from copy import deepcopy

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from core.view.view_validator import ViewValidator, ViewValidationError
from core.registry import registry

from core.auth.dependencies import get_current_user, require_super_admin
from core.auth.field_access import FieldAccessService
from core.db.session import get_db
from modules.base.models.groups import Group
from modules.base.models.user import User
from modules.base.models.views import IrView

router = APIRouter(prefix="/views", tags=["views"])


class ViewCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    model: str = Field(min_length=2, max_length=100)
    type: str = Field(pattern="^(list|form)$")
    arch_json: dict
    priority: int = 100
    active: bool = True


def _collect_fields(node, fields: set[str]):
    if isinstance(node, dict):
        if node.get("type") == "field" and isinstance(node.get("name"), str):
            fields.add(node["name"])
        if isinstance(node.get("field"), str):
            fields.add(node["field"])
        for value in node.values():
            _collect_fields(value, fields)
    elif isinstance(node, list):
        for item in node:
            _collect_fields(item, fields)


def _apply_field_rules(node, read_allowed: set[str], write_allowed: set[str]):
    if isinstance(node, dict):
        field_name = None
        if node.get("type") == "field" and isinstance(node.get("name"), str):
            field_name = node["name"]
        elif isinstance(node.get("field"), str):
            field_name = node["field"]

        if field_name:
            if field_name not in read_allowed:
                return None
            if field_name not in write_allowed:
                node["readonly"] = True

        filtered = {}
        for key, value in node.items():
            result = _apply_field_rules(value, read_allowed, write_allowed)
            if result is not None:
                filtered[key] = result
        return filtered

    if isinstance(node, list):
        result = []
        for item in node:
            filtered_item = _apply_field_rules(item, read_allowed, write_allowed)
            if filtered_item is not None:
                result.append(filtered_item)
        return result

    return node


@router.post("")
def create_view(
    payload: ViewCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    print(f'this is the payload : {payload}')
    validator = ViewValidator(db, registry.field_cache)
    try:
        validator.validate(payload.model, payload.type, payload.arch_json)
    except ViewValidationError as e:
        raise HTTPException(status_code=422, detail={"errors": e.errors})
    
    view = IrView(
        name=payload.name, #type: ignore
        model=payload.model, #type: ignore
        type=payload.type, #type: ignore
        arch_json=payload.arch_json, #type: ignore
        priority=payload.priority, #type: ignore
        active=payload.active, #type: ignore
    )
    db.add(view)
    db.commit()
    db.refresh(view)
    return {"id": view.id, "name": view.name, "model": view.model, "type": view.type}


@router.post("/{view_id}/groups/{group_id}")
def attach_group_to_view(
    view_id: int,
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    view = db.query(IrView).filter(IrView.id == view_id).first()
    if not view:
        raise HTTPException(status_code=404, detail="View not found")

    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group not in view.groups:
        view.groups.append(group)
        db.commit()
    return {"status": "ok"}


@router.get("/{model}")
def resolve_view(
    model: str,
    type: str = Query(default="form", pattern="^(list|form)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(IrView)
        .filter(IrView.model == model, IrView.type == type, IrView.active.is_(True))
        .order_by(desc(IrView.priority), IrView.id.asc())
    )
    candidates = query.all()
    if not candidates:
        raise HTTPException(status_code=404, detail="No view found")

    user_group_ids = {group.id for group in current_user.groups}
    selected = None
    for view in candidates:
        if not view.groups:
            selected = view
            break
        view_group_ids = {group.id for group in view.groups}
        if user_group_ids.intersection(view_group_ids):
            selected = view
            break

    if not selected:
        raise HTTPException(status_code=403, detail="No accessible view for current user")

    payload = deepcopy(selected.arch_json)
    fields = set()
    _collect_fields(payload, fields)

    read_allowed = set()
    write_allowed = set()
    for field in fields:
        if FieldAccessService.can_read_field(current_user, db, model, field):
            read_allowed.add(field)
        if FieldAccessService.can_write_field(current_user, db, model, field):
            write_allowed.add(field)

    filtered_arch = _apply_field_rules(payload, read_allowed, write_allowed)

    return {
        "id": selected.id,
        "name": selected.name,
        "model": selected.model,
        "type": selected.type,
        "priority": selected.priority,
        "arch_json": filtered_arch,
    }
