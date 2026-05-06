from core.db.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.exc import SQLAlchemyError 
from sqlalchemy import ForeignKey, String, select
from core.hooks.decoratos import hook
from core.hooks import events
from core.hooks.result import HookResult

import logging
logger = logging.getLogger(__name__)

class Employee(Base):
    __tablename__ = "ir_employee" # type: ignore[assignment]
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_name : Mapped[str] = mapped_column(String(128), nullable=False)
    employee_email : Mapped[str] =  mapped_column(String(128), nullable=False)
    
    @hook(events.BEFORE_CREATE, scope="model", value="ir_employee", name="employees.unique_employee_name")
    def unique_employee_name(ctx):
        db = ctx.db #type:ignore

        email = ctx.data.get("employee_email") #type:ignore
        if email and email.endswith("@blocked.com"):
            return HookResult(False, "Blocked email domain")

        name = ctx.data.get("employee_name") #type:ignore
        exists = db.query(ctx.obj.__class__).filter_by(employee_name=name).all() #type:ignore
        if exists:
            return HookResult(False, "Employee name must be unique")

        return HookResult(True)
