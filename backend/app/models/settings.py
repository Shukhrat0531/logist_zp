from sqlalchemy import String, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False, default="")
