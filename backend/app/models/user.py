import enum
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Enum, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    dispatcher = "dispatcher"
    accountant = "accountant"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.dispatcher)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    employee_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
