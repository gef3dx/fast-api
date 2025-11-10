from typing import Protocol, Optional, List
from uuid import UUID

from fastapi import HTTPException, status

from repositories import UserRepository

from schemas import (
    UserCreateSchemas,
    UserResponseSchemas,
    UserUpdateSchemas,
)
from models import UserModel
from utils.security import hash_password


class UserService(Protocol):
    """Протокол для сервиса пользователей"""

    async def create_user(self, user_data: UserCreateSchemas) -> UserResponseSchemas:
        """Создать нового пользователя с валидацией"""
        ...

    async def get_user(self, user_uuid: UUID) -> UserResponseSchemas:
        """Получить пользователя по ID"""
        ...

    async def get_user_by_email(self, email: str) -> Optional[UserResponseSchemas]:
        """Найти пользователя по email"""
        ...

    async def list_users(
        self, skip: int = 0, limit: int = 100
    ) -> List[UserResponseSchemas]:
        """Получить список пользователей с пагинацией"""
        ...

    async def update_user(
        self, user_uuid: UUID, user_data: UserUpdateSchemas
    ) -> UserResponseSchemas:
        """Обновить данные пользователя"""
        ...

    async def delete_user(self, user_uuid: UUID) -> bool:
        """Удалить пользователя"""
        ...

    async def activate_user(self, user_uuid: UUID) -> UserResponseSchemas:
        """Активировать пользователя"""
        ...

    async def deactivate_user(self, user_uuid: UUID) -> UserResponseSchemas:
        """Деактивировать пользователя"""
        ...

    async def get_active_users(
        self, skip: int = 0, limit: int = 100
    ) -> List[UserResponseSchemas]:
        """Получить список активных пользователей"""
        ...


class ImpUserService:
    """Реализация сервиса пользователей с бизнес-логикой"""

    def __init__(self, user_repository: UserRepository):
        self.repository = user_repository

    async def create_user(self, user_data: UserCreateSchemas) -> UserResponseSchemas:
        """Создать нового пользователя с валидацией"""

        # Проверка уникальности email
        existing_user = await self.repository.get_by_email(user_data.email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Валидация бизнес-правил
        if len(user_data.email.split("@")[0]) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email username must be at least 3 characters",
            )

        # Хеширование пароля и автогенерация name
        user_dict = user_data.model_dump()

        # Автоматически генерируем полное имя, если его нет
        if "name" not in user_dict or not user_dict.get("name"):
            user_dict["name"] = f"{user_dict['first_name']} {user_dict['last_name']}"

        if "password" in user_dict:
            user_dict["hashed_password"] = hash_password(user_dict.pop("password"))

        # Создание пользователя
        user = UserModel(**user_dict)
        created_user = await self.repository.create(user)

        return UserResponseSchemas.model_validate(created_user)

    async def get_user(self, user_uuid: UUID) -> UserResponseSchemas:
        """Получить пользователя по ID"""
        user = await self.repository.get_by_uuid(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_uuid} not found",
            )
        return UserResponseSchemas.model_validate(user)

    async def get_user_by_email(self, email: str) -> Optional[UserResponseSchemas]:
        """Найти пользователя по email"""
        user = await self.repository.get_by_email(email)
        if user:
            return UserResponseSchemas.model_validate(user)
        return None

    async def list_users(
        self, skip: int = 0, limit: int = 100
    ) -> List[UserResponseSchemas]:
        """Получить список пользователей с пагинацией"""
        # Валидация параметров пагинации
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip parameter must be non-negative",
            )
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 1000",
            )

        users = await self.repository.get_all(skip=skip, limit=limit)
        return [UserResponseSchemas.model_validate(user) for user in users]

    async def update_user(
        self, user_uuid: UUID, user_data: UserUpdateSchemas
    ) -> UserResponseSchemas:
        """Обновить данные пользователя"""
        # Проверка существования
        existing_user = await self.repository.get_by_uuid(user_uuid)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_uuid} not found",
            )

        # Если обновляется email, проверяем уникальность
        update_dict = user_data.model_dump(exclude_unset=True)
        if "email" in update_dict:
            email_user = await self.repository.get_by_email(update_dict["email"])
            if email_user and email_user.id != user_uuid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use",
                )

        # Если обновляется пароль, хешируем его
        if "password" in update_dict:
            update_dict["hashed_password"] = hash_password(update_dict.pop("password"))

        updated_user = await self.repository.update(user_uuid, **update_dict)
        return UserResponseSchemas.model_validate(updated_user)

    async def delete_user(self, user_uuid: UUID) -> bool:
        """Удалить пользователя"""
        # Проверка существования
        user = await self.repository.get_by_uuid(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_uuid} not found",
            )

        # Бизнес-правило: нельзя удалить активного админа
        if (
            hasattr(user, "is_admin")
            and user.is_admin
            and hasattr(user, "is_active")
            and user.is_active
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete active admin user",
            )

        return await self.repository.delete(user_uuid)

    async def activate_user(self, user_uuid: UUID) -> UserResponseSchemas:
        """Активировать пользователя"""
        user = await self.repository.get_by_uuid(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_uuid} not found",
            )

        if hasattr(user, "is_active") and user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User is already active"
            )

        updated_user = await self.repository.update(user_uuid, is_active=True)
        return UserResponseSchemas.model_validate(updated_user)

    async def deactivate_user(self, user_uuid: UUID) -> UserResponseSchemas:
        """Деактивировать пользователя"""
        user = await self.repository.get_by_uuid(user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_uuid} not found",
            )

        if hasattr(user, "is_active") and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already inactive",
            )

        updated_user = await self.repository.update(user_uuid, is_active=False)
        return UserResponseSchemas.model_validate(updated_user)

    async def get_active_users(
        self, skip: int = 0, limit: int = 100
    ) -> List[UserResponseSchemas]:
        """Получить список активных пользователей"""
        all_users = await self.repository.get_all(skip=skip, limit=limit)
        active_users = [
            user for user in all_users if hasattr(user, "is_active") and user.is_active
        ]
        return [UserResponseSchemas.model_validate(user) for user in active_users]
