from core.db.base import Base
from sqlalchemy import Boolean, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

group_permission_rel = Table(
    "group_permission_rel",
    Base.metadata,  # type: ignore[union-attr]
    Column("group_id", ForeignKey("ir_groups.id"), primary_key=True),
    Column("permission_id", ForeignKey("ir_permission.id"), primary_key=True),
)

user_permission_rel = Table(
    "user_permission_rel",
    Base.metadata,  # type: ignore[union-attr]
    Column("user_id", ForeignKey("ir_user.id"), primary_key=True),
    Column("permission_id", ForeignKey("ir_permission.id"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "ir_permission"  # type: ignore[assignment]

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)

    groups = relationship(
        "Group",
        secondary="group_permission_rel",
        back_populates="permissions",
    )
    users = relationship(
        "User",
        secondary="user_permission_rel",
        back_populates="direct_permissions",
    )


class FieldAccess(Base):
    __tablename__ = "ir_field_access"  # type: ignore[assignment]

    id: Mapped[int] = mapped_column(primary_key=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    can_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    can_write: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    group_id: Mapped[int | None] = mapped_column(ForeignKey("ir_groups.id"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("ir_user.id"), nullable=True)

    group = relationship("Group")
    user = relationship("User")
