from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from core.auth.dependencies import get_current_user
from core.auth.security import create_access_token, hash_password, verify_password
from core.db.session import get_db
from modules.base.models.groups import Group
from modules.base.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class BootstrapAdminRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.last_login_at = datetime.now(timezone.utc)
    token = create_access_token(subject=user.email)
    db.commit()

    return {"access_token": token, "token_type": "bearer"}


@router.post("/bootstrap-admin")
def bootstrap_admin(payload: BootstrapAdminRequest, db: Session = Depends(get_db)):
    existing_users = db.query(User).count()
    if existing_users > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bootstrap disabled. Users already exist.",
        )

    super_admin_group = db.query(Group).filter(Group.name == "super_admin").first()
    if not super_admin_group:
        super_admin_group = Group(name="super_admin") #type:ignore
        db.add(super_admin_group)
        db.flush()

    user = User(name=payload.name,email=payload.email,password_hash=hash_password(payload.password),is_active=True) #type:ignore
    user.groups.append(super_admin_group)

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.email)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "groups": [group.name for group in current_user.groups],
    }
