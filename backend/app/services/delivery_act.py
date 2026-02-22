from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update
from fastapi import HTTPException
from app.models.trip_invoice import TripInvoice, TripStatus, DeliveryAct, ActStatus
from app.models.reference import Buyer
from app.models.user import User, UserRole
from app.schemas.schemas import DeliveryActRead

async def get_delivery_acts(
    db: AsyncSession,
    buyer_id: int | None = None,
    page: int = 1,
    size: int = 50
):
    query = select(DeliveryAct)
    if buyer_id:
        query = query.where(DeliveryAct.buyer_id == buyer_id)
    
    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    
    query = query.order_by(DeliveryAct.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {"items": items, "total": total, "page": page, "size": size}


async def create_delivery_act(
    db: AsyncSession,
    buyer_id: int,
    start_date: date,
    end_date: date,
    user: User
) -> DeliveryAct:
    # Check if buyer exists
    buyer = await db.get(Buyer, buyer_id)
    if not buyer:
        raise HTTPException(404, "Buyer not found")

    # Validate dates
    if start_date > end_date:
        raise HTTPException(400, "Start date must be before end date")
        
    # Find trips to include
    # Confirmed trips for this buyer in range, not yet in an act
    trips_q = select(TripInvoice).where(
        TripInvoice.buyer_id == buyer_id,
        TripInvoice.trip_date >= start_date,
        TripInvoice.trip_date <= end_date,
        TripInvoice.status == TripStatus.confirmed,
        TripInvoice.delivery_act_id.is_(None)
    )
    trips = (await db.execute(trips_q)).scalars().all()
    
    if not trips:
        raise HTTPException(400, "No confirmed trips found for this period")
        
    total_trips = len(trips)
    total_volume = sum(float(t.volume_m3 or 0) for t in trips)
    
    # Create Act
    act = DeliveryAct(
        buyer_id=buyer_id,
        start_date=start_date,
        end_date=end_date,
        total_trips=total_trips,
        total_volume=total_volume,
        status=ActStatus.open
    )
    db.add(act)
    await db.flush()
    await db.refresh(act)
    
    # Link trips to act
    curr_ids = [t.id for t in trips]
    await db.execute(
        update(TripInvoice)
        .where(TripInvoice.id.in_(curr_ids))
        .values(delivery_act_id=act.id)
    )
    
    await db.commit()
    return act

async def delete_delivery_act(db: AsyncSession, id: int, user: User):
    act = await db.get(DeliveryAct, id)
    if not act:
        raise HTTPException(404, "Act not found")
        
    # Unlink trips
    await db.execute(
        update(TripInvoice)
        .where(TripInvoice.delivery_act_id == act.id)
        .values(delivery_act_id=None)
    )
    
    await db.delete(act)
    await db.commit()
    return {"ok": True}
