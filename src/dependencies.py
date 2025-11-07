from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.postgres import get_async_session
from repositories import UserRepository, ImpUserRepository
from services import UserService, ImpUserService


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
