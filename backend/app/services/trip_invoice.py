from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from app.models.trip_invoice import TripInvoice, TripStatus
from app.models.reference import Carrier
from app.models.employee import Employee
from app.models.reference import Vehicle, Buyer, Material, ObjectPlace
from app.models.user import User, UserRole
from app.schemas.schemas import TripInvoiceCreate, TripInvoiceUpdate
from app.services.audit import write_audit


async def create_trip_invoice(
    db: AsyncSession, data: TripInvoiceCreate, user: User
) -> TripInvoice:
    # Fetch carrier price
    carrier = await db.get(Carrier, data.carrier_id)
    if not carrier:
        raise HTTPException(status_code=400, detail="Carrier not found")

    # Check duplicate by invoice_number
    if data.invoice_number:
        exists = await db.execute(
            select(TripInvoice).where(
                TripInvoice.invoice_number == data.invoice_number,
                TripInvoice.trip_date == data.trip_date,
                TripInvoice.vehicle_id == data.vehicle_id,
                TripInvoice.status != TripStatus.void,
            )
        )
        if exists.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="Duplicate invoice: same invoice_number + trip_date + vehicle already exists",
            )

    invoice = TripInvoice(
        trip_date=data.trip_date,
        driver_id=data.driver_id,
        vehicle_id=data.vehicle_id,
        carrier_id=data.carrier_id,
        buyer_id=data.buyer_id,
        material_id=data.material_id,
        invoice_number=data.invoice_number,
        trip_price_fixed=carrier.price_per_trip,
        status=TripStatus.draft,
        created_by=user.id,
        fuel_liters=data.fuel_liters,
        volume_m3=data.volume_m3,
        place_id=data.place_id,
    )
    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def update_trip_invoice(
    db: AsyncSession, invoice_id: int, data: TripInvoiceUpdate, user: User
) -> TripInvoice:
    invoice = await db.get(TripInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.status == TripStatus.locked and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Cannot edit locked invoice")

    old_data = {
        "trip_date": str(invoice.trip_date),
        "driver_id": invoice.driver_id,
        "carrier_id": invoice.carrier_id,
        "buyer_id": invoice.buyer_id,
        "material_id": invoice.material_id,
    }

    update_dict = data.model_dump(exclude_unset=True)

    # If carrier changed, update price
    if "carrier_id" in update_dict:
        carrier = await db.get(Carrier, update_dict["carrier_id"])
        if not carrier:
            raise HTTPException(status_code=400, detail="Carrier not found")
        invoice.trip_price_fixed = carrier.price_per_trip

    for field, value in update_dict.items():
        setattr(invoice, field, value)

    if invoice.status == TripStatus.locked:
        await write_audit(db, user.id, "update_locked", "TripInvoice", invoice.id, old_data, update_dict)

    await db.flush()
    await db.refresh(invoice)
    return invoice


async def confirm_trip_invoice(db: AsyncSession, invoice_id: int, user: User) -> TripInvoice:
    invoice = await db.get(TripInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status != TripStatus.draft:
        raise HTTPException(status_code=400, detail=f"Cannot confirm invoice in status '{invoice.status}'")
    invoice.status = TripStatus.confirmed
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def void_trip_invoice(db: AsyncSession, invoice_id: int, user: User) -> TripInvoice:
    invoice = await db.get(TripInvoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == TripStatus.locked and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Cannot void locked invoice")
    if invoice.status == TripStatus.void:
        raise HTTPException(status_code=400, detail="Already voided")

    old_status = invoice.status
    invoice.status = TripStatus.void
    await write_audit(db, user.id, "void", "TripInvoice", invoice.id, {"status": old_status}, {"status": "void"})
    await db.flush()
    await db.refresh(invoice)
    return invoice


async def get_trip_invoices(
    db: AsyncSession,
    page: int = 1,
    size: int = 50,
    trip_date_from=None,
    trip_date_to=None,
    driver_id: int | None = None,
    carrier_id: int | None = None,
    buyer_id: int | None = None,
    status_filter: str | None = None,
):
    query = (
        select(
            TripInvoice,
            Employee.full_name.label("driver_name"),
            Vehicle.plate_number.label("vehicle_plate"),
            Carrier.name.label("carrier_name"),
            Buyer.name.label("buyer_name"),
            Material.name.label("material_name"),
            ObjectPlace.name.label("place_name"),
        )
        .outerjoin(Employee, TripInvoice.driver_id == Employee.id)
        .outerjoin(Vehicle, TripInvoice.vehicle_id == Vehicle.id)
        .outerjoin(Carrier, TripInvoice.carrier_id == Carrier.id)
        .outerjoin(Buyer, TripInvoice.buyer_id == Buyer.id)
        .outerjoin(Material, TripInvoice.material_id == Material.id)
        .outerjoin(ObjectPlace, TripInvoice.place_id == ObjectPlace.id)
    )

    filters = []
    if trip_date_from:
        filters.append(TripInvoice.trip_date >= trip_date_from)
    if trip_date_to:
        filters.append(TripInvoice.trip_date <= trip_date_to)
    if driver_id:
        filters.append(TripInvoice.driver_id == driver_id)
    if carrier_id:
        filters.append(TripInvoice.carrier_id == carrier_id)
    if buyer_id:
        filters.append(TripInvoice.buyer_id == buyer_id)
    if status_filter:
        filters.append(TripInvoice.status == status_filter)

    if filters:
        query = query.where(and_(*filters))

    # Count
    count_q = select(func.count()).select_from(TripInvoice)
    if filters:
        count_q = count_q.where(and_(*filters))
    total_result = await db.execute(count_q)
    total = total_result.scalar()

    query = query.order_by(TripInvoice.trip_date.desc(), TripInvoice.id.desc())
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    rows = result.all()

    items = []
    for row in rows:
        inv = row[0]
        items.append({
            "id": inv.id,
            "trip_date": str(inv.trip_date),
            "driver_id": inv.driver_id,
            "vehicle_id": inv.vehicle_id,
            "carrier_id": inv.carrier_id,
            "buyer_id": inv.buyer_id,
            "material_id": inv.material_id,
            "invoice_number": inv.invoice_number,
            "trip_price_fixed": float(inv.trip_price_fixed),
            "status": inv.status.value,
            "created_by": inv.created_by,
            "created_at": inv.created_at.isoformat(),
            "updated_at": inv.updated_at.isoformat(),
            "fuel_liters": float(inv.fuel_liters) if inv.fuel_liters else None,
            "volume_m3": float(inv.volume_m3) if inv.volume_m3 else None,
            "place_id": inv.place_id,
            "delivery_act_id": inv.delivery_act_id,
            "driver_name": row[1],
            "vehicle_plate": row[2],
            "carrier_name": row[3],
            "buyer_name": row[4],
            "material_name": row[5],
            "place_name": row[6],
        })

    return {"items": items, "total": total, "page": page, "size": size}
