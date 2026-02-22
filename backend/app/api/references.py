from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.employee import Employee, EmployeeType
from app.models.reference import Carrier, Buyer, Material, Vehicle, Machinery, ObjectPlace, MachineryTariff
from app.models.settings import SystemSettings
from app.schemas.schemas import (
    CarrierRead, CarrierCreate, CarrierUpdate,
    BuyerRead, BuyerCreate, BuyerUpdate,
    MaterialRead, MaterialCreate, MaterialUpdate,
    VehicleRead, VehicleCreate, VehicleUpdate,
    MachineryRead, MachineryCreate, MachineryUpdate, MachineryTariffRead, MachineryTariffCreate, MachineryTariffUpdate,
    ObjectPlaceRead, ObjectPlaceCreate, ObjectPlaceUpdate,
    EmployeeRead, EmployeeCreate, EmployeeUpdate,
    SettingRead, SettingUpdate, SettingCreate,
)
from app.core.security import hash_password

router = APIRouter(tags=["References"])


# ──── Generic CRUD helper ────
async def _list(db, model):
    result = await db.execute(select(model).order_by(model.id))
    return result.scalars().all()


async def _get(db, model, item_id):
    obj = await db.get(model, item_id)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return obj


async def _create(db, model, data):
    obj = model(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def _update(db, model, item_id, data):
    obj = await _get(db, model, item_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


async def _delete(db, model, item_id):
    obj = await _get(db, model, item_id)
    await db.delete(obj)
    await db.commit()
    return {"ok": True}


# ──── Carriers ────
@router.get("/carriers", response_model=list[CarrierRead])
async def list_carriers(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await _list(db, Carrier)

@router.post("/carriers", response_model=CarrierRead)
async def create_carrier(data: CarrierCreate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _create(db, Carrier, data)

@router.put("/carriers/{id}", response_model=CarrierRead)
async def update_carrier(id: int, data: CarrierUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _update(db, Carrier, id, data)

@router.delete("/carriers/{id}")
async def delete_carrier(id: int, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _delete(db, Carrier, id)


# ──── Buyers ────
@router.get("/buyers", response_model=list[BuyerRead])
async def list_buyers(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await _list(db, Buyer)

@router.post("/buyers", response_model=BuyerRead)
async def create_buyer(data: BuyerCreate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _create(db, Buyer, data)

@router.put("/buyers/{id}", response_model=BuyerRead)
async def update_buyer(id: int, data: BuyerUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _update(db, Buyer, id, data)

@router.delete("/buyers/{id}")
async def delete_buyer(id: int, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _delete(db, Buyer, id)


# ──── Materials ────
@router.get("/materials", response_model=list[MaterialRead])
async def list_materials(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await _list(db, Material)

@router.post("/materials", response_model=MaterialRead)
async def create_material(data: MaterialCreate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _create(db, Material, data)

@router.put("/materials/{id}", response_model=MaterialRead)
async def update_material(id: int, data: MaterialUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _update(db, Material, id, data)

@router.delete("/materials/{id}")
async def delete_material(id: int, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _delete(db, Material, id)


# ──── Vehicles ────
@router.get("/vehicles", response_model=list[VehicleRead])
async def list_vehicles(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await _list(db, Vehicle)

@router.post("/vehicles", response_model=VehicleRead)
async def create_vehicle(data: VehicleCreate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _create(db, Vehicle, data)

@router.put("/vehicles/{id}", response_model=VehicleRead)
async def update_vehicle(id: int, data: VehicleUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _update(db, Vehicle, id, data)

@router.delete("/vehicles/{id}")
async def delete_vehicle(id: int, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _delete(db, Vehicle, id)


# ──── Machinery ────
@router.get("/machinery", response_model=list[MachineryRead])
async def list_machinery(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await _list(db, Machinery)

@router.post("/machinery", response_model=MachineryRead)
async def create_machinery(data: MachineryCreate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _create(db, Machinery, data)

@router.put("/machinery/{id}", response_model=MachineryRead)
async def update_machinery(id: int, data: MachineryUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _update(db, Machinery, id, data)

@router.delete("/machinery/{id}")
async def delete_machinery(id: int, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _delete(db, Machinery, id)


# ──── Machinery Tariffs ────
@router.get("/machinery/{id}/tariffs", response_model=list[MachineryTariffRead])
async def list_machinery_tariffs(id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(MachineryTariff).where(MachineryTariff.machinery_id == id).order_by(MachineryTariff.name))
    return result.scalars().all()

@router.post("/machinery-tariffs", response_model=MachineryTariffRead)
async def create_machinery_tariff(data: MachineryTariffCreate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _create(db, MachineryTariff, data)

@router.delete("/machinery-tariffs/{id}")
async def delete_machinery_tariff(id: int, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _delete(db, MachineryTariff, id)


# ──── ObjectPlaces ────
@router.get("/object-places", response_model=list[ObjectPlaceRead])
async def list_object_places(
    buyer_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user)
):
    if buyer_id:
        result = await db.execute(select(ObjectPlace).where(ObjectPlace.buyer_id == buyer_id).order_by(ObjectPlace.name))
        return result.scalars().all()
    return await _list(db, ObjectPlace)

@router.post("/object-places", response_model=ObjectPlaceRead)
async def create_object_place(data: ObjectPlaceCreate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _create(db, ObjectPlace, data)

@router.put("/object-places/{id}", response_model=ObjectPlaceRead)
async def update_object_place(id: int, data: ObjectPlaceUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _update(db, ObjectPlace, id, data)

@router.delete("/object-places/{id}")
async def delete_object_place(id: int, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _delete(db, ObjectPlace, id)


# ──── Employees ────
@router.get("/employees", response_model=list[EmployeeRead])
async def list_employees(
    employee_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    query = select(Employee).order_by(Employee.full_name)
    if employee_type:
        query = query.where(Employee.employee_type == employee_type)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/employees", response_model=EmployeeRead)
async def create_employee(data: EmployeeCreate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _create(db, Employee, data)

@router.put("/employees/{id}", response_model=EmployeeRead)
async def update_employee(id: int, data: EmployeeUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _update(db, Employee, id, data)

@router.delete("/employees/{id}")
async def delete_employee(id: int, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _delete(db, Employee, id)


# ──── Settings ────
@router.get("/settings", response_model=list[SettingRead])
async def list_settings(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await _list(db, SystemSettings)

@router.put("/settings/{id}", response_model=SettingRead)
async def update_setting(id: int, data: SettingUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    return await _update(db, SystemSettings, id, data)

@router.post("/settings", response_model=SettingRead)
async def create_setting(data: SettingCreate, db: AsyncSession = Depends(get_db), _=Depends(require_roles(UserRole.admin))):
    obj = SystemSettings(key=data.key, value=data.value)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj
