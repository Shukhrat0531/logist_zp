import enum
from datetime import date, datetime, timezone
from sqlalchemy import (
    String, Date, DateTime, Integer, Enum, ForeignKey, Text
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class SessionStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    locked = "locked"


class MachinerySession(Base):
    __tablename__ = "machinery_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    operator_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    machinery_id: Mapped[int] = mapped_column(Integer, ForeignKey("machinery.id"), nullable=False)
    buyer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("buyers.id"), nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    hourly_rate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), nullable=False, default=SessionStatus.open, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    fuel_liters: Mapped[float | None] = mapped_column(nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
