import enum
from datetime import datetime, timezone, date
from sqlalchemy import (
    String, Numeric, DateTime, Integer, Enum, ForeignKey, Text, Boolean, Date
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class PeriodStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    paid = "paid"


class PayrollPeriod(Base):
    __tablename__ = "payroll_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    month: Mapped[str] = mapped_column(String(7), nullable=False, unique=True, index=True)  # YYYY-MM
    status: Mapped[PeriodStatus] = mapped_column(
        Enum(PeriodStatus), nullable=False, default=PeriodStatus.open
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class PayrollLine(Base):
    __tablename__ = "payroll_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(Integer, ForeignKey("payroll_periods.id"), nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    employee_type: Mapped[str] = mapped_column(String(20), nullable=False)  # driver | operator
    trips_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    trips_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    hours_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    hours_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    manual_correction: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(Integer, ForeignKey("payroll_periods.id"), nullable=False)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    paid_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class SalaryAdvance(Base):
    __tablename__ = "salary_advances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
