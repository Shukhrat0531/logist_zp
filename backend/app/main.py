from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base

# Import all models so Alembic/create_all can see them
from app.models import user, employee, reference, trip_invoice, machinery_session, payroll, audit_log, settings as settings_model  # noqa

from app.api import auth, references, users, trip_invoices, machinery_sessions, payroll as payroll_api, dashboard, delivery_acts, salary_advances


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (dev convenience; use alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Run seed
    from app.services.seed import run_seed
    await run_seed()

    yield


app = FastAPI(
    title="Logist ZP",
    description="Logistics Payroll Management System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(references.router)
app.include_router(users.router)
app.include_router(trip_invoices.router)
app.include_router(machinery_sessions.router)
app.include_router(payroll_api.router)
app.include_router(delivery_acts.router)
app.include_router(salary_advances.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
