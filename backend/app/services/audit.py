from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


async def write_audit(
    db: AsyncSession,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    old_data: dict | None = None,
    new_data: dict | None = None,
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_data=old_data,
        new_data=new_data,
    )
    db.add(log)
    await db.flush()
