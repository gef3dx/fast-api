from typing import Annotated, AsyncGenerator
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.postgres import async_session_factory

from repositories import UserRepository, ImpUserRepository
from services import UserService, ImpUserService
from repositories import UserRepository
from utils.jwt import verify_token
from models import UserModel


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии БД"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> UserRepository:
    """Dependency для получения репозитория пользователей"""
    return ImpUserRepository(session)


def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    """Dependency для получения сервиса пользователей"""
    return ImpUserService(repository)


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserModel:
    """
    Получить текущего пользователя из access токена в cookies

    Args:
        request: FastAPI request
        session: Сессия БД
        user_repository: Репозиторий пользователей

    Returns:
        UserModel: Текущий пользователь

    Raises:
        HTTPException: 401 если токен невалидный или пользователь не найден
    """
    # Получаем токен из cookies
    access_token = request.cookies.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем токен
    token_data = verify_token(access_token, token_type="access")

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Получаем пользователя из БД
    user = await user_repository.get_by_email(token_data.email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем активность
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    return user


async def get_current_active_user(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> UserModel:
    """
    Получить текущего активного пользователя

    Args:
        current_user: Текущий пользователь

    Returns:
        UserModel: Активный пользователь

    Raises:
        HTTPException: 403 если пользователь неактивен
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
) -> UserModel:
    """
    Получить текущего пользователя-администратора

    Args:
        current_user: Текущий активный пользователь

    Returns:
        UserModel: Пользователь-администратор

    Raises:
        HTTPException: 403 если пользователь не администратор
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return current_user
