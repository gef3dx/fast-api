from pydantic import BaseModel, EmailStr, UUID4, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Базовая схема с общими полями"""

    email: EmailStr
    user_name: str = Field(min_length=3, max_length=50, description="Username")
    first_name: str = Field(min_length=2, max_length=50, description="First name")
    last_name: str = Field(min_length=2, max_length=50, description="Last name")
    phone: str = Field(
        min_length=6,
        max_length=12,
        pattern=r"^\+?[0-9]{6,12}$",
        description="Phone number",
    )


class UserCreateSchemas(UserBase):
    """Схема для создания пользователя"""

    password: str = Field(min_length=8, max_length=128, description="User password")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "user_name": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+79991234567",
                "password": "SecurePass123!",
            }
        }
    )


class UserUpdateSchemas(BaseModel):
    """Схема для обновления пользователя (все поля опциональны)"""

    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=2, max_length=100)  # Добавлено
    user_name: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    phone: Optional[str] = Field(
        None, min_length=6, max_length=12, pattern=r"^\+?[0-9]{6,12}$"
    )
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "+79991234568",
            }
        }
    )


class UserResponseSchemas(UserBase):
    """Схема для ответа с информацией о пользователе"""

    id: int = Field(description="Database ID")
    uuid: UUID4 = Field(description="User UUID")
    name: Optional[str] = Field(None, description="Full name")  # Добавлено
    is_active: bool = Field(default=True, description="User active status")
    is_admin: bool = Field(default=False, description="Admin privileges")
    created_at: datetime = Field(description="Registration date")
    updated_at: Optional[datetime] = Field(None, description="Last update date")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "user_name": "johndoe",
                "name": "John Doe",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+79991234567",
                "is_active": True,
                "is_admin": False,
                "created_at": "2025-11-06T14:13:00",
                "updated_at": "2025-11-06T14:13:00",
            }
        },
    )


class UserListResponseSchemas(BaseModel):
    """Схема для списка пользователей с пагинацией"""

    total: int = Field(description="Total users count")
    items: list[UserResponseSchemas] = Field(description="Users list")
    skip: int = Field(ge=0, description="Number of skipped records")
    limit: int = Field(ge=1, le=1000, description="Number of records per page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 100,
                "items": [
                    {
                        "id": 1,
                        "uuid": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "user@example.com",
                        "user_name": "johndoe",
                        "name": "John Doe",
                        "first_name": "John",
                        "last_name": "Doe",
                        "phone": "+79991234567",
                        "is_active": True,
                        "is_admin": False,
                        "created_at": "2025-11-06T14:13:00",
                        "updated_at": None,
                    }
                ],
                "skip": 0,
                "limit": 100,
            }
        }
    )


class UserInDBSchemas(UserResponseSchemas):
    """Схема для работы с БД (включая хешированный пароль)"""

    hashed_password: str = Field(description="Hashed password")
