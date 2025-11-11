from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.postgres import async_session_factory

from repositories import UserRepository, ImpUserRepository
from services import UserService, ImpUserService


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
