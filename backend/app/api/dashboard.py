from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.deps import get_db, get_current_user
from app.models.trip_invoice import TripInvoice, TripStatus
from app.models.machinery_session import MachinerySession, SessionStatus
from app.schemas.schemas import DashboardStats, GSMReportItem, ObjectStatsItem, ObjectVehicleItem
from app.models.reference import Vehicle, Buyer
from app.models.employee import Employee

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    today = date.today()
    month_start = today.replace(day=1)

    # Today trips
    today_q = await db.execute(
        select(
            func.count(TripInvoice.id),
            func.coalesce(func.sum(TripInvoice.trip_price_fixed), 0),
        ).where(
            TripInvoice.trip_date == today,
            TripInvoice.status != TripStatus.void,
        )
    )
    today_row = today_q.one()

    # Month trips
    month_q = await db.execute(
        select(
            func.count(TripInvoice.id),
            func.coalesce(func.sum(TripInvoice.trip_price_fixed), 0),
        ).where(
            TripInvoice.trip_date >= month_start,
            TripInvoice.status != TripStatus.void,
        )
    )
    month_row = month_q.one()

    # Open sessions
    open_q = await db.execute(
        select(func.count(MachinerySession.id)).where(MachinerySession.status == SessionStatus.open)
    )
    open_count = open_q.scalar()

    # Month sessions
    month_sess = await db.execute(
        select(func.count(MachinerySession.id)).where(
            MachinerySession.work_date >= month_start,
        )
    )
    month_sess_count = month_sess.scalar()

    return DashboardStats(
        today_trips=today_row[0],
        month_trips=month_row[0],
        today_trips_amount=float(today_row[1]),
        month_trips_amount=float(month_row[1]),
        open_sessions=open_count,
        month_sessions=month_sess_count,
    )


@router.get("/gsm-report", response_model=list[GSMReportItem])
async def get_gsm_report(
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    query = (
        select(
            TripInvoice.vehicle_id,
            Vehicle.plate_number,
            Employee.full_name,
            func.sum(TripInvoice.fuel_liters).label("total_fuel"),
            func.sum(TripInvoice.volume_m3).label("total_volume"),
            func.count(TripInvoice.id).label("trips_count"),
        )
        .join(Vehicle, TripInvoice.vehicle_id == Vehicle.id)
        .outerjoin(Employee, TripInvoice.driver_id == Employee.id)
        .where(
            TripInvoice.trip_date >= date_from,
            TripInvoice.trip_date <= date_to,
            TripInvoice.status != TripStatus.void,
        )
        .group_by(TripInvoice.vehicle_id, Vehicle.plate_number, Employee.full_name)
        .order_by(Vehicle.plate_number)
    )
    
    rows = (await db.execute(query)).all()
    
    items = []
    for row in rows:
        items.append(GSMReportItem(
            vehicle_id=row.vehicle_id,
            vehicle_plate=row.plate_number,
            driver_name=row.full_name,
            total_fuel=float(row.total_fuel or 0),
            total_volume=float(row.total_volume or 0),
            trips_count=row.trips_count,
        ))
        
    return items


@router.get("/gsm-vehicle-history")
async def get_gsm_vehicle_history(
    vehicle_id: int = Query(...),
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    query = (
        select(
            TripInvoice.trip_date,
            TripInvoice.fuel_liters,
            Employee.full_name.label("driver_name"),
            Buyer.name.label("buyer_name"),
        )
        .outerjoin(Employee, TripInvoice.driver_id == Employee.id)
        .outerjoin(Buyer, TripInvoice.buyer_id == Buyer.id)
        .where(
            TripInvoice.vehicle_id == vehicle_id,
            TripInvoice.trip_date >= date_from,
            TripInvoice.trip_date <= date_to,
            TripInvoice.status != TripStatus.void,
            TripInvoice.fuel_liters.isnot(None),
            TripInvoice.fuel_liters > 0,
        )
        .order_by(TripInvoice.trip_date.desc())
    )
    rows = (await db.execute(query)).all()
    return [
        {
            "trip_date": str(r.trip_date),
            "fuel_liters": float(r.fuel_liters),
            "driver_name": r.driver_name or "—",
            "buyer_name": r.buyer_name or "—",
        }
        for r in rows
    ]


@router.get("/objects-stats", response_model=list[ObjectStatsItem])
async def get_objects_stats(
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    if not date_from:
        date_from = date.today().replace(day=1)
    if not date_to:
        date_to = date.today()

    query = (
        select(
            TripInvoice.buyer_id,
            Buyer.name,
            func.count(TripInvoice.id).label("trips_count"),
            func.sum(TripInvoice.volume_m3).label("total_volume"),
            func.sum(TripInvoice.trip_price_fixed).label("total_amount"),
        )
        .join(Buyer, TripInvoice.buyer_id == Buyer.id)
        .where(
            TripInvoice.trip_date >= date_from,
            TripInvoice.trip_date <= date_to,
            TripInvoice.status != TripStatus.void,
        )
        .group_by(TripInvoice.buyer_id, Buyer.name)
        .order_by(func.sum(TripInvoice.volume_m3).desc())
    )
    
    rows = (await db.execute(query)).all()
    
    return [
        ObjectStatsItem(
            buyer_id=row.buyer_id,
            buyer_name=row.name,
            trips_count=row.trips_count,
            total_volume=float(row.total_volume or 0),
            total_amount=float(row.total_amount or 0),
        )
        for row in rows
    ]


@router.get("/objects/{id}/vehicles", response_model=list[ObjectVehicleItem])
async def get_object_vehicles(
    id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    if not date_from:
        date_from = date.today().replace(day=1)
    if not date_to:
        date_to = date.today()

    query = (
        select(
            TripInvoice.vehicle_id,
            Vehicle.plate_number,
            func.count(TripInvoice.id).label("trips_count"),
            func.sum(TripInvoice.volume_m3).label("total_volume"),
        )
        .join(Vehicle, TripInvoice.vehicle_id == Vehicle.id)
        .where(
            TripInvoice.buyer_id == id,
            TripInvoice.trip_date >= date_from,
            TripInvoice.trip_date <= date_to,
            TripInvoice.status != TripStatus.void,
        )
        .group_by(TripInvoice.vehicle_id, Vehicle.plate_number)
        .order_by(func.sum(TripInvoice.volume_m3).desc())
    )
    
    rows = (await db.execute(query)).all()
    
    return [
        ObjectVehicleItem(
            vehicle_id=row.vehicle_id,
            vehicle_plate=row.plate_number,
            trips_count=row.trips_count,
            total_volume=float(row.total_volume or 0),
        )
        for row in rows
    ]


@router.get("/objects/{id}/pending-stats")
async def get_object_pending_stats(
    id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    query = (
        select(
            func.count(TripInvoice.id),
            func.sum(TripInvoice.volume_m3),
            func.sum(TripInvoice.trip_price_fixed),
        )
        .where(
            TripInvoice.buyer_id == id,
            TripInvoice.status == TripStatus.confirmed,
            TripInvoice.delivery_act_id.is_(None),
        )
    )
    
    row = (await db.execute(query)).one()
    
    return {
        "trips_count": row[0] or 0,
        "total_volume": float(row[1] or 0),
        "total_amount": float(row[2] or 0),
    }

