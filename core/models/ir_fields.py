from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean
from core.db.base import Base

class IrField(Base):
    __tablename__ = "ir_fields" # type: ignore

    id: Mapped[int] = mapped_column(primary_key=True)

    model: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))

    field_type: Mapped[str] = mapped_column(String(50))  
    # string, integer, many2one, one2many, many2many

    required: Mapped[bool] = mapped_column(Boolean, default=False)

    relation: Mapped[str] = mapped_column(String(100), nullable=True)
    # target model (res_company, etc)

    relation_table: Mapped[str] = mapped_column(String(100), nullable=True)
    # for many2many