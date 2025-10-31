from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean
from src.models.base import BaseModelSql


class Users(BaseModelSql):
    user_name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
    )
    name: Mapped[str] = mapped_column(
        String(50),
    )
    first_name: Mapped[str] = mapped_column(
        String(50),
    )
    last_name: Mapped[str] = mapped_column(
        String(50),
    )
    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )
