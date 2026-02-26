from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.schemas import MachinerySessionRead, MachinerySessionCreate, MachinerySessionClose, MachinerySessionUpdate
from app.services.machinery_session import create_session, close_session, update_session, get_sessions

router = APIRouter(prefix="/machinery-sessions", tags=["Machinery Sessions"])


@router.get("")
async def list_sessions(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    date_from: date | None = None,
    date_to: date | None = None,
    operator_id: int | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await get_sessions(
        db, page=page, size=size,
        date_from=date_from, date_to=date_to,
        operator_id=operator_id, status_filter=status,
    )


@router.get("/open")
async def list_open_sessions(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await get_sessions(db, only_open=True, size=200)


@router.post("", response_model=MachinerySessionRead)
async def create_mach_session(
    data: MachinerySessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    s = await create_session(db, data, user)
    await db.commit()
    return s


@router.put("/{id}", response_model=MachinerySessionRead)
async def update_mach_session(
    id: int,
    data: MachinerySessionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    s = await update_session(db, id, data, user)
    await db.commit()
    return s


@router.post("/{id}/close", response_model=MachinerySessionRead)
async def close_mach_session(
    id: int,
    data: MachinerySessionClose,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.dispatcher)),
):
    s = await close_session(db, id, data, user)
    await db.commit()
    return s


@router.delete("/{id}")
async def delete_mach_session(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin)),
):
    from app.models.machinery_session import MachinerySession
    from fastapi import HTTPException
    session = await db.get(MachinerySession, id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"ok": True}
