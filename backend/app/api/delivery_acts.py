from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.schemas import DeliveryActRead, DeliveryActCreate, DeliveryActList
from app.services.delivery_act import get_delivery_acts, create_delivery_act, delete_delivery_act

router = APIRouter(prefix="/delivery-acts", tags=["Delivery Acts"])

@router.get("", response_model=DeliveryActList)
async def list_acts(
    buyer_id: int | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await get_delivery_acts(db, buyer_id, page, size)

@router.post("", response_model=DeliveryActRead)
async def create_act(
    data: DeliveryActCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return await create_delivery_act(db, data.buyer_id, data.start_date, data.end_date, user)

@router.delete("/{id}")
async def delete_act(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    return await delete_delivery_act(db, id, user)
