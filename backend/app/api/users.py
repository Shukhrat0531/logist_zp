from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.schemas import UserRead, UserCreate, UserUpdate
from app.core.security import hash_password
from sqlalchemy import select

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserRead])
async def list_users(db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()


@router.post("", response_model=UserRead)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    # Check unique
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already exists")

    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        employee_id=data.employee_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/{id}", response_model=UserRead)
async def update_user(id: int, data: UserUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    user = await db.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_dict = data.model_dump(exclude_unset=True)
    if "password" in update_dict:
        user.hashed_password = hash_password(update_dict.pop("password"))
    for k, v in update_dict.items():
        setattr(user, k, v)

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{id}")
async def delete_user(id: int, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    user = await db.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"ok": True}
