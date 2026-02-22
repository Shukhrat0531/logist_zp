import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.schemas import (
    PayrollPeriodRead,
    SalaryAdvanceRead, SalaryAdvanceCreate,
    PayrollLineRead, PayrollLineUpdate
)
from app.services.payroll import (
    generate_payroll, close_period, mark_period_paid,
    get_payroll_lines, get_periods, update_payroll_line,
    create_advance, delete_advance, get_advances
)
from app.utils.excel import build_payroll_excel

router = APIRouter(prefix="/payroll", tags=["Payroll"])


@router.get("/periods", response_model=list[PayrollPeriodRead])
async def list_periods(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await get_periods(db)


@router.post("/periods/generate", response_model=PayrollPeriodRead)
async def gen_payroll(
    month: str = Query(..., regex=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return await generate_payroll(db, month, user)


@router.post("/periods/{id}/close", response_model=PayrollPeriodRead)
async def close(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return await close_period(db, id, user)


@router.post("/periods/{id}/mark-paid", response_model=PayrollPeriodRead)
async def paid(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher, UserRole.accountant)),
):
    return await mark_period_paid(db, id, user)


@router.delete("/periods/{id}")
async def delete_period(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    from datetime import date as dt_date
    from app.models.payroll import PayrollPeriod, PayrollLine
    from app.models.trip_invoice import TripInvoice, TripStatus
    from app.models.machinery_session import MachinerySession, SessionStatus
    from sqlalchemy import delete as sql_delete, update as sql_update

    period = await db.get(PayrollPeriod, id)
    if not period:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Period not found")

    # Parse month to unlock invoices/sessions
    year, mon = int(period.month.split("-")[0]), int(period.month.split("-")[1])
    month_start = dt_date(year, mon, 1)
    month_end = dt_date(year + 1, 1, 1) if mon == 12 else dt_date(year, mon + 1, 1)

    # Unlock trip invoices: locked → confirmed
    await db.execute(
        sql_update(TripInvoice)
        .where(
            TripInvoice.trip_date >= month_start,
            TripInvoice.trip_date < month_end,
            TripInvoice.status == TripStatus.locked,
        )
        .values(status=TripStatus.confirmed)
    )

    # Unlock machinery sessions: locked → closed
    await db.execute(
        sql_update(MachinerySession)
        .where(
            MachinerySession.work_date >= month_start,
            MachinerySession.work_date < month_end,
            MachinerySession.status == SessionStatus.locked,
        )
        .values(status=SessionStatus.closed)
    )

    # Delete all lines and the period
    await db.execute(sql_delete(PayrollLine).where(PayrollLine.period_id == id))
    await db.delete(period)
    await db.commit()
    return {"ok": True}


@router.get("/periods/{id}/lines", response_model=list[PayrollLineRead])
async def lines(
    id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await get_payroll_lines(db, id)


@router.put("/lines/{id}", response_model=PayrollLineRead)
async def update_line(
    id: int,
    data: PayrollLineUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return await update_payroll_line(db, id, data, user)


@router.get("/periods/{id}/export-excel")
async def export_excel(
    id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    data = await get_payroll_lines(db, id)
    buf = build_payroll_excel(data, id)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=payroll_{id}.xlsx"},
    )


# ──── Salary Advances ────

@router.get("/advances", response_model=list[SalaryAdvanceRead])
async def list_advances(
    employee_id: int | None = None,
    month: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await get_advances(db, employee_id, month)


@router.post("/advances", response_model=SalaryAdvanceRead)
async def add_advance(
    data: SalaryAdvanceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return await create_advance(db, data, user)


@router.delete("/advances/{id}")
async def remove_advance(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return await delete_advance(db, id, user)
