from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from typing import List
from core.hooks import events
from core.hooks.decoratos import hook
from core.hooks.result import HookResult
from core.db.base import Base

class Company(Base):
    __tablename__ = "ir_company" # type: ignore[assignment]

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))

    users: Mapped[List["User"]] = relationship( #type: ignore[name-defined]
        back_populates="company",
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<Company {self.name}>"
    
    @hook(events.BEFORE_CREATE, scope="model", value="ir_company", name="company.unique_company_name")
    def unique_company_name(ctx):
        db = ctx.db #type:ignore

        company_name = ctx.data.get("name") #type:ignore
        exists = db.query(ctx.obj.__class__).filter_by(name=company_name).first() #type:ignore
        if exists:
            return HookResult(False, "Company Name must be unique")

        return HookResult(True)
