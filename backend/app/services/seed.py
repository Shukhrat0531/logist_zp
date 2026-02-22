from sqlalchemy import select
from app.db.session import async_session
from app.models.user import User, UserRole
from app.models.employee import Employee, EmployeeType
from app.models.reference import Carrier, Buyer, Material, Vehicle, Machinery
from app.models.settings import SystemSettings
from app.core.security import hash_password


async def run_seed():
    """Seed initial data if database is empty."""
    async with async_session() as db:
        # Check if admin exists
        result = await db.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            return  # Already seeded

        # ── Admin user ──
        admin = User(
            username="admin",
            hashed_password=hash_password("admin123"),
            full_name="Администратор",
            role=UserRole.admin,
        )
        db.add(admin)

        # ── Dispatcher user ──
        dispatcher = User(
            username="dispatcher",
            hashed_password=hash_password("disp123"),
            full_name="Диспетчер",
            role=UserRole.dispatcher,
        )
        db.add(dispatcher)

        # ── Carriers ──
        carriers = [
            Carrier(name="Карьер Северный", price_per_trip=15000),
            Carrier(name="Карьер Южный", price_per_trip=18000),
            Carrier(name="Карьер Восточный", price_per_trip=12000),
            Carrier(name="Карьер Западный", price_per_trip=20000),
        ]
        for c in carriers:
            db.add(c)

        # ── Materials ──
        materials = [
            Material(name="Щебень"),
            Material(name="Песок"),
            Material(name="Грунт"),
            Material(name="ПГС"),
        ]
        for m in materials:
            db.add(m)

        # ── Buyers ──
        buyers = [
            Buyer(name="Стройка-1 ул. Мира"),
            Buyer(name="Стройка-2 пр. Ленина"),
            Buyer(name="Склад Центральный"),
        ]
        for b in buyers:
            db.add(b)

        # ── Drivers ──
        drivers = [
            Employee(full_name="Иванов Пётр", employee_type=EmployeeType.driver),
            Employee(full_name="Сидоров Алексей", employee_type=EmployeeType.driver),
            Employee(full_name="Козлов Дмитрий", employee_type=EmployeeType.driver),
        ]
        for d in drivers:
            db.add(d)

        # ── Operators ──
        operators = [
            Employee(full_name="Петров Сергей", employee_type=EmployeeType.operator),
            Employee(full_name="Николаев Андрей", employee_type=EmployeeType.operator),
        ]
        for o in operators:
            db.add(o)

        # ── Vehicles ──
        vehicles = [
            Vehicle(plate_number="А001АА 01"),
            Vehicle(plate_number="В002ВВ 01"),
            Vehicle(plate_number="С003СС 01"),
        ]
        for v in vehicles:
            db.add(v)

        # ── Machinery ────
        machinery = [
            Machinery(name="Экскаватор CAT-320"),
            Machinery(name="Экскаватор Komatsu PC-200"),
        ]
        for m in machinery:
            db.add(m)

        # ── Settings ──
        db.add(SystemSettings(key="machinery_hour_rate", value="5000"))

        await db.commit()
        print("✅ Seed data created successfully")
