from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException, status
from app.models.machinery_session import MachinerySession, SessionStatus
from app.models.employee import Employee
from app.models.reference import Machinery, Buyer
from app.models.user import User, UserRole
from app.schemas.schemas import MachinerySessionCreate, MachinerySessionClose, MachinerySessionUpdate
from app.services.audit import write_audit


async def create_session(db: AsyncSession, data: MachinerySessionCreate, user: User) -> MachinerySession:
    # Check no open session for operator
    existing_op = await db.scalar(
        select(MachinerySession).where(
            MachinerySession.operator_id == data.operator_id,
            MachinerySession.status == SessionStatus.open,
        )
    )
    if existing_op:
        raise HTTPException(status_code=409, detail="Operator already has an open session")

    # Check no open session for machinery
    existing_mach = await db.scalar(
        select(MachinerySession).where(
            MachinerySession.machinery_id == data.machinery_id,
            MachinerySession.status == SessionStatus.open,
        )
    )
    if existing_mach:
        raise HTTPException(status_code=409, detail="Machinery already has an open session")

    session = MachinerySession(
        work_date=data.start_at.date(),
        operator_id=data.operator_id,
        machinery_id=data.machinery_id,
        buyer_id=data.buyer_id,
        start_at=data.start_at,
        hourly_rate=data.hourly_rate,
        status=SessionStatus.open,
        notes=data.notes,
        created_by=user.id,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def close_session(db: AsyncSession, session_id: int, data: MachinerySessionClose, user: User) -> MachinerySession:
    session = await db.get(MachinerySession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != SessionStatus.open:
        raise HTTPException(status_code=400, detail="Session is not open")
    if data.end_at <= session.start_at:
        raise HTTPException(status_code=400, detail="end_at must be after start_at")

    session.end_at = data.end_at
    session.status = SessionStatus.closed
    await db.flush()
    await db.refresh(session)
    return session


async def update_session(db: AsyncSession, session_id: int, data: MachinerySessionUpdate, user: User) -> MachinerySession:
    session = await db.get(MachinerySession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == SessionStatus.locked and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Cannot edit locked session")

    update_dict = data.model_dump(exclude_unset=True)
    old_data = {"operator_id": session.operator_id, "machinery_id": session.machinery_id}

    for field, value in update_dict.items():
        setattr(session, field, value)
        if field == "start_at" and value:
            session.work_date = value.date()

    if session.status == SessionStatus.locked:
        await write_audit(db, user.id, "update_locked", "MachinerySession", session.id, old_data, update_dict)

    await db.flush()
    await db.refresh(session)
    return session


def calc_pay_hours(start_at: datetime, end_at: datetime | None) -> float:
    if not end_at:
        return 0.0
    diff = (end_at - start_at).total_seconds() / 3600
    return max(1.0, round(diff, 2))


async def get_sessions(
    db: AsyncSession,
    page: int = 1,
    size: int = 50,
    date_from=None,
    date_to=None,
    operator_id: int | None = None,
    status_filter: str | None = None,
    only_open: bool = False,
):
    query = (
        select(
            MachinerySession,
            Employee.full_name.label("operator_name"),
            Machinery.name.label("machinery_name"),
            Buyer.name.label("buyer_name"),
        )
        .outerjoin(Employee, MachinerySession.operator_id == Employee.id)
        .outerjoin(Machinery, MachinerySession.machinery_id == Machinery.id)
        .outerjoin(Buyer, MachinerySession.buyer_id == Buyer.id)
    )

    filters = []
    if only_open:
        filters.append(MachinerySession.status == SessionStatus.open)
    if date_from:
        filters.append(MachinerySession.work_date >= date_from)
    if date_to:
        filters.append(MachinerySession.work_date <= date_to)
    if operator_id:
        filters.append(MachinerySession.operator_id == operator_id)
    if status_filter and not only_open:
        filters.append(MachinerySession.status == status_filter)

    if filters:
        query = query.where(and_(*filters))

    count_q = select(func.count()).select_from(MachinerySession)
    if filters:
        count_q = count_q.where(and_(*filters))
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(MachinerySession.work_date.desc(), MachinerySession.id.desc())
    query = query.offset((page - 1) * size).limit(size)

    rows = (await db.execute(query)).all()

    items = []
    for row in rows:
        s = row[0]
        items.append({
            "id": s.id,
            "work_date": s.work_date,
            "operator_id": s.operator_id,
            "machinery_id": s.machinery_id,
            "buyer_id": s.buyer_id,
            "start_at": s.start_at,
            "end_at": s.end_at,
            "hourly_rate": s.hourly_rate,
            "status": s.status,
            "notes": s.notes,
            "created_by": s.created_by,
            "created_at": s.created_at,
            "operator_name": row[1],
            "machinery_name": row[2],
            "buyer_name": row[3],
            "pay_hours": calc_pay_hours(s.start_at, s.end_at),
        })

    return {"items": items, "total": total, "page": page, "size": size}
