from core.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer

class Group(Base):
    __tablename__ = "ir_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    users = relationship(
        "User",
        secondary="user_group_rel",
        back_populates="groups"
    )