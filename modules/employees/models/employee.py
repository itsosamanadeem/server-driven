from core.db.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ForeignKey, String

class Employee(Base):
    __tablename__ = "ir_employee"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_name : Mapped[str] = mapped_column(String(128), nullable=False)
    