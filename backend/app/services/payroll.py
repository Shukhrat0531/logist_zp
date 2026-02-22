from datetime import datetime, timezone, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update, delete
from fastapi import HTTPException
from app.models.payroll import PayrollPeriod, PayrollLine, PeriodStatus, SalaryAdvance
from app.models.trip_invoice import TripInvoice, TripStatus
from app.models.machinery_session import MachinerySession, SessionStatus
from app.models.employee import Employee, EmployeeType
from app.models.settings import SystemSettings
from app.models.user import User, UserRole
from app.services.machinery_session import calc_pay_hours
from app.services.audit import write_audit
from app.schemas.schemas import SalaryAdvanceCreate, SalaryAdvanceUpdate, PayrollLineUpdate


async def _get_hour_rate(db: AsyncSession) -> float:
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.key == "machinery_hour_rate")
    )
    setting = result.scalar_one_or_none()
    try:
        return float(setting.value) if setting else 0.0
    except (ValueError, TypeError):
        return 0.0


async def generate_payroll(db: AsyncSession, month: str, user: User):
    """Generate or update payroll lines for a given month (YYYY-MM)."""
    # Parse month
    try:
        year, mon = month.split("-")
        year, mon = int(year), int(mon)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    month_start = date(year, mon, 1)
    if mon == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, mon + 1, 1)

    # Get or create period
    result = await db.execute(select(PayrollPeriod).where(PayrollPeriod.month == month))
    period = result.scalar_one_or_none()
    if period and period.status != PeriodStatus.open:
        raise HTTPException(status_code=400, detail="Period is already closed or paid")
    if not period:
        period = PayrollPeriod(month=month, status=PeriodStatus.open)
        db.add(period)
        await db.flush()
        await db.refresh(period)

    # Preserve Manual Corrections & Is Paid status if lines exist
    # Fetch existing lines to map employee_id -> (manual_correction, is_paid)
    existing_lines_q = await db.execute(select(PayrollLine).where(PayrollLine.period_id == period.id))
    existing_map = {}
    for line in existing_lines_q.scalars().all():
        existing_map[line.employee_id] = {
            "manual_correction": line.manual_correction,
            "is_paid": line.is_paid
        }

    # Delete old lines for this period (we will recreate them)
    await db.execute(delete(PayrollLine).where(PayrollLine.period_id == period.id))
    await db.flush()

    hour_rate = await _get_hour_rate(db)

    # ── Drivers ──
    driver_query = (
        select(
            TripInvoice.driver_id,
            func.count(TripInvoice.id).label("cnt"),
            func.sum(TripInvoice.trip_price_fixed).label("total"),
        )
        .where(
            TripInvoice.status == TripStatus.confirmed,
            TripInvoice.trip_date >= month_start,
            TripInvoice.trip_date < month_end,
        )
        .group_by(TripInvoice.driver_id)
    )
    driver_rows = (await db.execute(driver_query)).all()

    for row in driver_rows:
        saved = existing_map.get(row.driver_id, {})
        line = PayrollLine(
            period_id=period.id,
            employee_id=row.driver_id,
            employee_type="driver",
            trips_count=row.cnt,
            trips_amount=float(row.total or 0),
            hours_total=0,
            hours_amount=0,
            total_amount=float(row.total or 0),
            manual_correction=saved.get("manual_correction", 0),
            is_paid=saved.get("is_paid", False),
        )
        db.add(line)

    # ── Operators ──
    # Note: machinery_session service logic uses MachinerySession now
    session_query = (
        select(MachinerySession)
        .where(
            MachinerySession.status == SessionStatus.closed,
            MachinerySession.work_date >= month_start,
            MachinerySession.work_date < month_end,
        )
    )
    sessions = (await db.execute(session_query)).scalars().all()

    operator_data: dict[int, dict] = {}
    for s in sessions:
        ph = calc_pay_hours(s.start_at, s.end_at)
        rate = float(s.hourly_rate) if s.hourly_rate else hour_rate
        amount = round(ph * rate, 2)
        
        if s.operator_id not in operator_data:
            operator_data[s.operator_id] = {"hours": 0.0, "amount": 0.0}
        operator_data[s.operator_id]["hours"] += ph
        operator_data[s.operator_id]["amount"] += amount

    for op_id, d in operator_data.items():
        saved = existing_map.get(op_id, {})
        line = PayrollLine(
            period_id=period.id,
            employee_id=op_id,
            employee_type="operator",
            trips_count=0,
            trips_amount=0,
            hours_total=d["hours"],
            hours_amount=d["amount"],
            total_amount=d["amount"],
            manual_correction=saved.get("manual_correction", 0),
            is_paid=saved.get("is_paid", False),
        )
        db.add(line)

    await db.commit()
    return period


async def close_period(db: AsyncSession, period_id: int, user: User):
    period = await db.get(PayrollPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    if period.status != PeriodStatus.open:
        raise HTTPException(status_code=400, detail="Period is not open")

    month = period.month
    year, mon = int(month.split("-")[0]), int(month.split("-")[1])
    month_start = date(year, mon, 1)
    month_end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)

    # Lock invoices
    await db.execute(
        update(TripInvoice)
        .where(
            TripInvoice.trip_date >= month_start,
            TripInvoice.trip_date < month_end,
            TripInvoice.status == TripStatus.confirmed,
        )
        .values(status=TripStatus.locked)
    )

    # Lock sessions
    await db.execute(
        update(MachinerySession)
        .where(
            MachinerySession.work_date >= month_start,
            MachinerySession.work_date < month_end,
            MachinerySession.status == SessionStatus.closed,
        )
        .values(status=SessionStatus.locked)
    )

    period.status = PeriodStatus.closed
    period.closed_at = datetime.now(timezone.utc)
    period.closed_by = user.id

    await write_audit(db, user.id, "close_period", "PayrollPeriod", period.id, None, {"status": "closed"})
    await db.commit()
    return period


async def mark_period_paid(db: AsyncSession, period_id: int, user: User):
    period = await db.get(PayrollPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")
    if period.status != PeriodStatus.closed:
        raise HTTPException(status_code=400, detail="Period must be closed first")

    period.status = PeriodStatus.paid
    await write_audit(db, user.id, "mark_paid", "PayrollPeriod", period.id, None, {"status": "paid"})
    await db.commit()
    return period


async def update_payroll_line(db: AsyncSession, line_id: int, data: PayrollLineUpdate, user: User):
    line = await db.get(PayrollLine, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Payroll line not found")
    
    # Check if period is open? Allowed to edit correction if period is open.
    # If period is closed/paid, maybe allow ONLY if admin? 
    # For now, allow if not paid? Or follow period status logic.
    period = await db.get(PayrollPeriod, line.period_id)
    if period.status == PeriodStatus.paid and user.role != UserRole.admin:
        raise HTTPException(status_code=400, detail="Cannot edit paid period")

    if data.manual_correction is not None:
        line.manual_correction = data.manual_correction
    if data.is_paid is not None:
        line.is_paid = data.is_paid
        
    await db.commit()
    await db.refresh(line)
    return line


async def get_payroll_lines(db: AsyncSession, period_id: int):
    period = await db.get(PayrollPeriod, period_id)
    if not period:
        return []

    month = period.month
    year, mon = int(month.split("-")[0]), int(month.split("-")[1])
    month_start = date(year, mon, 1)
    month_end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)

    # Fetch advances for this month
    advances_q = select(
        SalaryAdvance.employee_id,
        func.sum(SalaryAdvance.amount).label("total_adv")
    ).where(
        SalaryAdvance.date >= month_start,
        SalaryAdvance.date < month_end
    ).group_by(SalaryAdvance.employee_id)
    
    adv_rows = (await db.execute(advances_q)).all()
    adv_map = {row.employee_id: float(row.total_adv or 0) for row in adv_rows}

    query = (
        select(PayrollLine, Employee.full_name.label("employee_name"))
        .outerjoin(Employee, PayrollLine.employee_id == Employee.id)
        .where(PayrollLine.period_id == period_id)
        .order_by(PayrollLine.employee_type, Employee.full_name)
    )
    rows = (await db.execute(query)).all()

    items = []
    for row in rows:
        line = row[0]
        adv = adv_map.get(line.employee_id, 0.0)
        items.append({
            "id": line.id,
            "period_id": line.period_id,
            "employee_id": line.employee_id,
            "employee_type": line.employee_type,
            "trips_count": line.trips_count,
            "trips_amount": float(line.trips_amount),
            "hours_total": float(line.hours_total),
            "hours_amount": float(line.hours_amount),
            "total_amount": float(line.total_amount),
            "manual_correction": float(line.manual_correction),
            "is_paid": line.is_paid,
            "employee_name": row[1],
            "advances_amount": adv,
        })
    return items


async def get_periods(db: AsyncSession):
    result = await db.execute(select(PayrollPeriod).order_by(PayrollPeriod.month.desc()))
    return result.scalars().all()


# ──── Salary Advance CRUD ────

async def get_advances(
    db: AsyncSession,
    employee_id: int | None = None,
    month: str | None = None
):
    query = select(SalaryAdvance, Employee.full_name.label("employee_name"))\
        .join(Employee, SalaryAdvance.employee_id == Employee.id)
    
    if employee_id:
        query = query.where(SalaryAdvance.employee_id == employee_id)
    
    if month:
        try:
            year, mon = month.split("-")
            start_d = date(int(year), int(mon), 1)
            end_d = date(int(year) + 1, 1, 1) if int(mon) == 12 else date(int(year), int(mon) + 1, 1)
            query = query.where(SalaryAdvance.date >= start_d, SalaryAdvance.date < end_d)
        except:
            pass
            
    query = query.order_by(SalaryAdvance.date.desc())
    rows = (await db.execute(query)).all()
    
    return [
        {**row[0].__dict__, "employee_name": row.employee_name}
        for row in rows
    ]

async def create_advance(db: AsyncSession, data: SalaryAdvanceCreate, user: User):
    adv = SalaryAdvance(**data.model_dump())
    db.add(adv)
    await db.commit()
    await db.refresh(adv)
    return adv

async def delete_advance(db: AsyncSession, id: int, user: User):
    adv = await db.get(SalaryAdvance, id)
    if not adv:
        raise HTTPException(404, "Advance not found")
    await db.delete(adv)
    await db.commit()
    return {"ok": True}
