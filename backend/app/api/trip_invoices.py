from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.schemas import TripInvoiceRead, TripInvoiceCreate, TripInvoiceUpdate
from app.services.trip_invoice import (
    create_trip_invoice, update_trip_invoice,
    confirm_trip_invoice, void_trip_invoice, get_trip_invoices,
)

router = APIRouter(prefix="/trip-invoices", tags=["Trip Invoices"])


@router.get("")
async def list_invoices(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    trip_date_from: date | None = None,
    trip_date_to: date | None = None,
    driver_id: int | None = None,
    carrier_id: int | None = None,
    buyer_id: int | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await get_trip_invoices(
        db, page=page, size=size,
        trip_date_from=trip_date_from, trip_date_to=trip_date_to,
        driver_id=driver_id, carrier_id=carrier_id,
        buyer_id=buyer_id, status_filter=status,
    )


@router.post("", response_model=TripInvoiceRead)
async def create_invoice(
    data: TripInvoiceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    invoice = await create_trip_invoice(db, data, user)
    await db.commit()
    return invoice


@router.put("/{id}", response_model=TripInvoiceRead)
async def update_invoice(
    id: int,
    data: TripInvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    invoice = await update_trip_invoice(db, id, data, user)
    await db.commit()
    return invoice


@router.post("/{id}/confirm", response_model=TripInvoiceRead)
async def confirm_invoice(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    invoice = await confirm_trip_invoice(db, id, user)
    await db.commit()
    return invoice


@router.post("/{id}/void", response_model=TripInvoiceRead)
async def void_invoice(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    invoice = await void_trip_invoice(db, id, user)
    await db.commit()
    return invoice


@router.delete("/{id}")
async def delete_invoice(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    from app.models.trip_invoice import TripInvoice
    from fastapi import HTTPException
    invoice = await db.get(TripInvoice, id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    await db.delete(invoice)
    await db.commit()
    return {"ok": True}
