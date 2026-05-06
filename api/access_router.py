from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.auth.dependencies import require_super_admin
from core.db.session import get_db
from modules.base.models.groups import Group
from modules.base.models.rbac import FieldAccess, Permission
from modules.base.models.user import User

router = APIRouter(prefix="/access", tags=["access"])


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50)


class FieldAccessRequest(BaseModel):
    model: str
    field: str
    can_read: bool = True
    can_write: bool = True
    group_id: int | None = None
    user_id: int | None = None


@router.get("/groups")
def list_groups(
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    groups = db.query(Group).all()
    return [{"id": g.id, "name": g.name} for g in groups]


@router.post("/groups")
def create_group(
    payload: GroupCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    existing = db.query(Group).filter(Group.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Group already exists")

    group = Group(name=payload.name)  # type: ignore
    db.add(group)
    db.commit()
    db.refresh(group)
    return {"id": group.id, "name": group.name}


@router.post("/groups/{group_id}/users/{user_id}")
def attach_user_to_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if not group or not user:
        raise HTTPException(status_code=404, detail="Group or user not found")

    if group not in user.groups:
        user.groups.append(group)
        db.commit()
    return {"status": "ok"}


@router.delete("/groups/{group_id}/users/{user_id}")
def remove_user_from_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if not group or not user:
        raise HTTPException(status_code=404, detail="Group or user not found")

    if group in user.groups:
        user.groups.remove(group)
        db.commit()
    return {"status": "ok"}


@router.get("/permissions")
def list_permissions(
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    perms = db.query(Permission).all()
    return [
        {"id": p.id, "code": p.code, "model": p.model, "action": p.action}
        for p in perms
    ]


@router.post("/groups/{group_id}/permissions/{permission_id}")
def attach_permission_to_group(
    group_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not group or not permission:
        raise HTTPException(status_code=404, detail="Group or permission not found")

    if permission not in group.permissions:
        group.permissions.append(permission)
        db.commit()
    return {"status": "ok"}


@router.delete("/groups/{group_id}/permissions/{permission_id}")
def remove_permission_from_group(
    group_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not group or not permission:
        raise HTTPException(status_code=404, detail="Group or permission not found")

    if permission in group.permissions:
        group.permissions.remove(permission)
        db.commit()
    return {"status": "ok"}


@router.get("/users/{user_id}/effective-permissions")
def user_effective_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    group_perms = {(perm.model, perm.action) for group in user.groups for perm in group.permissions}
    direct_perms = {(perm.model, perm.action) for perm in user.direct_permissions}
    all_perms = sorted(group_perms.union(direct_perms))

    return {
        "user_id": user.id,
        "email": user.email,
        "groups": [group.name for group in user.groups],
        "permissions": [{"model": m, "action": a} for m, a in all_perms],
    }


@router.post("/field-rules")
def upsert_field_rule(
    payload: FieldAccessRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    if (payload.group_id is None) == (payload.user_id is None):
        raise HTTPException(status_code=400, detail="Provide exactly one of group_id or user_id")

    rule = (
        db.query(FieldAccess)
        .filter(
            FieldAccess.model == payload.model,
            FieldAccess.field == payload.field,
            FieldAccess.group_id == payload.group_id,
            FieldAccess.user_id == payload.user_id,
        )
        .first()
    )

    if not rule:
        rule = FieldAccess(
            model=payload.model,
            field=payload.field,
            can_read=payload.can_read,
            can_write=payload.can_write,
            group_id=payload.group_id,
            user_id=payload.user_id,
        )
        db.add(rule)
    else:
        rule.can_read = payload.can_read
        rule.can_write = payload.can_write

    db.commit()
    return {"status": "ok"}


@router.get("/field-rules")
def list_field_rules(
    model: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    query = db.query(FieldAccess)
    if model:
        query = query.filter(FieldAccess.model == model)

    rules = query.all()
    return [
        {
            "id": rule.id,
            "model": rule.model,
            "field": rule.field,
            "can_read": rule.can_read,
            "can_write": rule.can_write,
            "group_id": rule.group_id,
            "user_id": rule.user_id,
        }
        for rule in rules
    ]
