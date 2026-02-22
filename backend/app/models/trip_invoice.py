import enum
from datetime import date, datetime, timezone
from sqlalchemy import (
    String, Numeric, Date, DateTime, Integer, Enum, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class TripStatus(str, enum.Enum):
    draft = "draft"
    confirmed = "confirmed"
    void = "void"
    locked = "locked"


class TripInvoice(Base):
    __tablename__ = "trip_invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", "trip_date", "vehicle_id", name="uq_invoice_trip_vehicle"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    driver_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False)
    carrier_id: Mapped[int] = mapped_column(Integer, ForeignKey("carriers.id"), nullable=False)
    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("buyers.id"), nullable=False)
    material_id: Mapped[int] = mapped_column(Integer, ForeignKey("materials.id"), nullable=False)
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    trip_price_fixed: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus), nullable=False, default=TripStatus.draft, index=True
    )
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # New fields
    fuel_liters: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    volume_m3: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    place_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("object_places.id"), nullable=True)
    delivery_act_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("delivery_acts.id"), nullable=True)

class ActStatus(str, enum.Enum):
    open = "open"
    closed = "closed"

class DeliveryAct(Base):
    __tablename__ = "delivery_acts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("buyers.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_trips: Mapped[int] = mapped_column(Integer, default=0)
    total_volume: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[ActStatus] = mapped_column(Enum(ActStatus), default=ActStatus.open)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
