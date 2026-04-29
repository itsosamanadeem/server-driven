from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from core.db.base import Base

class IrModel(Base):
    __tablename__ = "ir_model" #type: ignore

    id: Mapped[int] = mapped_column(primary_key=True)
    model: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    table_name: Mapped[str] = mapped_column(String(100))
    module: Mapped[str] = mapped_column(String(100))