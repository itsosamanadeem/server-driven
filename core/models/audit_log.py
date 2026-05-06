from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Text
from datetime import datetime
from core.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_log" #type: ignore

    id: Mapped[int] = mapped_column(primary_key=True)
    model: Mapped[str] = mapped_column(String(100))
    record_id: Mapped[int] = mapped_column(Integer)

    action: Mapped[str] = mapped_column(String(20))  # create/update/delete

    old_data: Mapped[str] = mapped_column(Text, nullable=True)
    new_data: Mapped[str] = mapped_column(Text, nullable=True)

    user: Mapped[str] = mapped_column(String(100), nullable=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
