from datetime import datetime
from typing import Optional

from core.db.base import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

association_table = Table(
    "user_group_rel",
    Base.metadata, # type: ignore[union-attr]
    Column("user_id", ForeignKey("ir_user.id")),
    Column("group_id", ForeignKey("ir_groups.id")),
)

class User(Base):
    __tablename__ = "ir_user" # type: ignore[assignment]
    
    id : Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50),nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    company_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ir_company.id")
    )

    company: Mapped["Company"] = relationship( #type: ignore[name-defined]
        back_populates="users"
    )
    groups = relationship(
        "Group",
        secondary="user_group_rel",
        back_populates="users"
    )
    direct_permissions = relationship(
        "Permission",
        secondary="user_permission_rel",
        back_populates="users"
    )
    def __repr__(self):
        return f"<User {self.name}>"
