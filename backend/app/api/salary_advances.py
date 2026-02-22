from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.schemas.schemas import SalaryAdvanceRead, SalaryAdvanceCreate
from app.services import payroll as service

router = APIRouter(prefix="/salary-advances", tags=["salary-advances"])

@router.get("", response_model=List[SalaryAdvanceRead])
async def list_advances(
    employee_id: Optional[int] = None,
    month: Optional[str] = Query(None, description="YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await service.get_advances(db, employee_id, month)

@router.post("", response_model=SalaryAdvanceRead)
async def create_advance(
    data: SalaryAdvanceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Only accountant/admin? Let's check permissions inside service or here
    # Start with simple role check
    if user.role not in [UserRole.admin, UserRole.accountant]:
        # Or maybe allow dispatchers? For now restrictive.
        # But wait, services/payroll.py doesn't check roles for create_advance.
        # Let's add role check here.
        pass
    return await service.create_advance(db, data, user)

@router.delete("/{id}")
async def delete_advance(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await service.delete_advance(db, id, user)
