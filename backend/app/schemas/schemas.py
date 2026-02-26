from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional
from app.models.user import UserRole
from app.models.employee import EmployeeType
from app.models.trip_invoice import TripStatus
from app.models.machinery_session import SessionStatus
from app.models.payroll import PeriodStatus


# ──── Auth ────
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    employee_id: Optional[int] = None

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str = ""
    role: UserRole = UserRole.dispatcher
    employee_id: Optional[int] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    employee_id: Optional[int] = None


# ──── Employee ────
class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    employee_type: EmployeeType
    is_active: bool

class EmployeeCreate(BaseModel):
    full_name: str
    employee_type: EmployeeType
    is_active: bool = True

class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    employee_type: Optional[EmployeeType] = None
    is_active: Optional[bool] = None


# ──── Carrier ────
class CarrierRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    price_per_trip: float
    is_active: bool

class CarrierCreate(BaseModel):
    name: str
    price_per_trip: float
    is_active: bool = True

class CarrierUpdate(BaseModel):
    name: Optional[str] = None
    price_per_trip: Optional[float] = None
    is_active: Optional[bool] = None


# ──── Buyer ────
class BuyerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    is_active: bool

class BuyerCreate(BaseModel):
    name: str
    is_active: bool = True

class BuyerUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


# ──── Material ────
class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    is_active: bool

class MaterialCreate(BaseModel):
    name: str
    is_active: bool = True

class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


# ──── Vehicle ────
class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    plate_number: str
    vehicle_type: str
    is_active: bool

class VehicleCreate(BaseModel):
    plate_number: str
    is_active: bool = True

class VehicleUpdate(BaseModel):
    plate_number: Optional[str] = None
    is_active: Optional[bool] = None


# ──── Machinery ────
class MachineryTariffRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    machinery_id: int
    name: str
    rate: int
    is_active: bool

class MachineryTariffCreate(BaseModel):
    machinery_id: int
    name: str
    rate: int
    is_active: bool = True

class MachineryTariffUpdate(BaseModel):
    name: Optional[str] = None
    rate: Optional[int] = None
    is_active: Optional[bool] = None

class MachineryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    is_active: bool
    # We will need to load tariffs explicitly if we want them here, 
    # but for now let's keep it simple and fetch them separately or allow optional


class MachineryCreate(BaseModel):
    name: str
    is_active: bool = True

class MachineryUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None


# ──── ObjectPlace ────
class ObjectPlaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    buyer_id: int
    name: str
    comment: Optional[str] = None
    is_active: bool

class ObjectPlaceCreate(BaseModel):
    buyer_id: int
    name: str
    comment: Optional[str] = None
    is_active: bool = True

class ObjectPlaceUpdate(BaseModel):
    name: Optional[str] = None
    comment: Optional[str] = None
    is_active: Optional[bool] = None


# ──── DeliveryAct ────
class DeliveryActRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    buyer_id: int
    start_date: date
    end_date: date
    total_trips: int
    total_volume: float
    status: str
    created_at: datetime


class DeliveryActList(BaseModel):
    items: list[DeliveryActRead]
    total: int
    page: int
    size: int


class DeliveryActCreate(BaseModel):
    buyer_id: int
    start_date: date
    end_date: date


# ──── TripInvoice ────
class TripInvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trip_date: date
    driver_id: int
    vehicle_id: int
    carrier_id: int
    buyer_id: int
    material_id: int
    invoice_number: Optional[str] = None
    trip_price_fixed: float
    status: TripStatus
    created_by: int
    created_at: datetime
    updated_at: datetime
    # new fields
    fuel_liters: Optional[float] = None
    volume_m3: Optional[float] = None
    place_id: Optional[int] = None
    delivery_act_id: Optional[int] = None
    # joined fields
    driver_name: Optional[str] = None
    vehicle_plate: Optional[str] = None
    carrier_name: Optional[str] = None
    buyer_name: Optional[str] = None
    material_name: Optional[str] = None
    place_name: Optional[str] = None

class TripInvoiceCreate(BaseModel):
    trip_date: date
    driver_id: int
    vehicle_id: int
    carrier_id: int
    buyer_id: int
    material_id: int
    invoice_number: Optional[str] = None
    # new fields
    fuel_liters: Optional[float] = None
    volume_m3: Optional[float] = None
    place_id: Optional[int] = None

class TripInvoiceUpdate(BaseModel):
    trip_date: Optional[date] = None
    driver_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    carrier_id: Optional[int] = None
    buyer_id: Optional[int] = None
    material_id: Optional[int] = None
    invoice_number: Optional[str] = None
    fuel_liters: Optional[float] = None
    volume_m3: Optional[float] = None
    place_id: Optional[int] = None


# ──── MachinerySession ────
class MachinerySessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    work_date: date
    operator_id: int
    machinery_id: int
    buyer_id: Optional[int] = None
    start_at: datetime
    end_at: Optional[datetime] = None
    hourly_rate: int
    status: SessionStatus
    notes: Optional[str] = None
    created_by: int
    created_at: datetime
    # joined
    operator_name: Optional[str] = None
    machinery_name: Optional[str] = None
    buyer_name: Optional[str] = None
    pay_hours: Optional[float] = None

class MachinerySessionCreate(BaseModel):
    operator_id: int
    machinery_id: int
    buyer_id: Optional[int] = None
    start_at: datetime
    hourly_rate: int
    notes: Optional[str] = None

class MachinerySessionClose(BaseModel):
    end_at: datetime
    fuel_liters: Optional[float] = None

class MachinerySessionUpdate(BaseModel):
    operator_id: Optional[int] = None
    machinery_id: Optional[int] = None
    buyer_id: Optional[int] = None
    start_at: Optional[datetime] = None
    notes: Optional[str] = None
    hourly_rate: Optional[int] = None


# ──── SalaryAdvance ────
class SalaryAdvanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    amount: float
    date: date
    comment: Optional[str] = None
    # joined
    employee_name: Optional[str] = None

class SalaryAdvanceCreate(BaseModel):
    employee_id: int
    amount: float
    date: date
    comment: Optional[str] = None

class SalaryAdvanceUpdate(BaseModel):
    amount: Optional[float] = None
    date: Optional[date] = None
    comment: Optional[str] = None


# ──── Payroll ────
class PayrollPeriodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    month: str
    status: PeriodStatus
    closed_at: Optional[datetime] = None
    closed_by: Optional[int] = None

class PayrollLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    period_id: int
    employee_id: int
    employee_type: str
    trips_count: int
    trips_amount: float
    hours_total: float
    hours_amount: float
    total_amount: float
    manual_correction: float
    is_paid: bool
    employee_name: Optional[str] = None
    advances_amount: float = 0  # To be populated manually

class PayrollLineUpdate(BaseModel):
    manual_correction: Optional[float] = None
    is_paid: Optional[bool] = None


# ──── AuditLog ────
class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    action: str
    entity_type: str
    entity_id: int
    old_data: Optional[dict] = None
    new_data: Optional[dict] = None
    timestamp: datetime


# ──── Settings ────
class SettingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    value: str

class SettingUpdate(BaseModel):
    value: str
    key: str | None = None

class SettingCreate(BaseModel):
    key: str
    value: str


# ──── Pagination ────
class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int


# ──── Dashboard ────
class DashboardStats(BaseModel):
    today_trips: int = 0
    month_trips: int = 0
    open_sessions: int = 0
    month_sessions: int = 0
    today_trips_amount: float = 0
    month_trips_amount: float = 0


class GSMReportItem(BaseModel):
    vehicle_id: int
    vehicle_plate: str
    driver_name: Optional[str] = None
    total_fuel: float
    total_volume: float
    trips_count: int


class ObjectStatsItem(BaseModel):
    buyer_id: int
    buyer_name: str
    trips_count: int
    total_volume: float
    total_amount: float

class ObjectVehicleItem(BaseModel):
    vehicle_id: int
    vehicle_plate: str
    trips_count: int
    total_volume: float

