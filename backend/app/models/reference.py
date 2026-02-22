import enum
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Numeric, DateTime, Integer, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class VehicleType(str, enum.Enum):
    truck = "truck"


class Carrier(Base):
    __tablename__ = "carriers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    price_per_trip: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class Buyer(Base):
    __tablename__ = "buyers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plate_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    vehicle_type: Mapped[VehicleType] = mapped_column(Enum(VehicleType), nullable=False, default=VehicleType.truck)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )



class Machinery(Base):
    __tablename__ = "machinery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

class ObjectPlace(Base):
    __tablename__ = "object_places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("buyers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    comment: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # We need to import ForeignKey if we want full relationship here, but for now simple column is enough as per style, or add ForeignKey
    # let's add ForeignKey for consistency
    
    
class MachineryTariff(Base):
    __tablename__ = "machinery_tariffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machinery_id: Mapped[int] = mapped_column(Integer, ForeignKey("machinery.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    rate: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


