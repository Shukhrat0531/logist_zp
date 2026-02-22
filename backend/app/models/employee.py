import enum
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Enum, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class EmployeeType(str, enum.Enum):
    driver = "driver"
    operator = "operator"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    employee_type: Mapped[EmployeeType] = mapped_column(Enum(EmployeeType), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
