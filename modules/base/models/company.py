from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from typing import List

from core.db.base import Base

class Company(Base):
    __tablename__ = "ir_company"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))

    users: Mapped[List["User"]] = relationship(
        back_populates="company",
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<Company {self.name}>"