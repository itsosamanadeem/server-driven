from core.db.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey
from typing import Optional

from sqlalchemy import Table, Column, ForeignKey

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
    def __repr__(self):
        return f"<User {self.name}>"