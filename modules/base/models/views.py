from core.db.base import Base
from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

view_group_rel = Table(
    "ir_view_group_rel",
    Base.metadata,  # type: ignore[union-attr]
    Column("view_id", ForeignKey("ir_view.id"), primary_key=True),
    Column("group_id", ForeignKey("ir_groups.id"), primary_key=True),
)


class IrView(Base):
    __tablename__ = "ir_view"  # type: ignore[assignment]

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    arch_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[str] = mapped_column(String(16), default="db", nullable=False)
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    groups = relationship(
        "Group",
        secondary="ir_view_group_rel",
    )
