import asyncio
import sys
import os
sys.path.append(os.getcwd())
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from app.core.config import settings
from app.db.base import Base

# Import all models
from app.models.user import User
from app.models.employee import Employee
from app.models.reference import Carrier, Buyer, Material, Vehicle, Machinery, ObjectPlace
from app.models.trip_invoice import TripInvoice, DeliveryAct
from app.models.machinery_session import MachinerySession
from app.models.payroll import PayrollPeriod, PayrollLine, PaymentRecord, SalaryAdvance
from app.models.audit_log import AuditLog
from app.models.settings import SystemSettings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = settings.DATABASE_URL
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


from sqlalchemy.ext.asyncio import create_async_engine

async def run_migrations_online():
    connectable = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
