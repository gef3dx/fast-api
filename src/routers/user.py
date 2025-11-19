from fastapi import APIRouter, Depends, status
from typing import Annotated, List
from uuid import UUID

from models import UserModel
from services import UserService
from dependencies import get_user_service, get_current_user
from schemas import UserCreateSchemas, UserUpdateSchemas, UserResponseSchemas

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=UserResponseSchemas
)
async def create_user(
    user_data: UserCreateSchemas,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponseSchemas:
    """Создать нового пользователя"""
    return await service.create_user(user_data)


# Статические маршруты ПЕРЕД динамическими
@router.get("/list", response_model=List[UserResponseSchemas])
async def list_users(
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
) -> List[UserResponseSchemas]:
    """Получить список пользователей"""
    return await service.list_users(skip=skip, limit=limit)


@router.get("/active", response_model=List[UserResponseSchemas])
async def list_active_users(
    service: Annotated[UserService, Depends(get_user_service)],
    skip: int = 0,
    limit: int = 100,
) -> List[UserResponseSchemas]:
    """Получить список активных пользователей"""
    return await service.get_active_users(skip=skip, limit=limit)


# Динамический маршрут {user_id} ПОСЛЕ всех статических
@router.get("/{user_id}", response_model=UserResponseSchemas)
async def get_user(
    user_id: UUID, service: Annotated[UserService, Depends(get_user_service)]
) -> UserResponseSchemas:
    """Получить пользователя по ID"""
    return await service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponseSchemas)
async def update_user(
    user_id: UUID,
    user_data: UserUpdateSchemas,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponseSchemas:
    """Обновить данные пользователя"""
    return await service.update_user(user_id, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID, service: Annotated[UserService, Depends(get_user_service)]
):
    """Удалить пользователя"""
    await service.delete_user(user_id)


@router.post("/{user_id}/activate", response_model=UserResponseSchemas)
async def activate_user(
    user_id: UUID, service: Annotated[UserService, Depends(get_user_service)]
) -> UserResponseSchemas:
    """Активировать пользователя"""
    return await service.activate_user(user_id)


@router.post("/{user_id}/deactivate", response_model=UserResponseSchemas)
async def deactivate_user(
    user_id: UUID, service: Annotated[UserService, Depends(get_user_service)]
) -> UserResponseSchemas:
    """Деактивировать пользователя"""
    return await service.deactivate_user(user_id)
