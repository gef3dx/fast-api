from typing import Protocol, Optional, List
from uuid import UUID
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import UserModel


class UserRepository(Protocol):
    """Протокол для репозитория пользователей с async методами"""

    async def create(self, user: UserModel) -> UserModel:
        """Создать нового пользователя"""
        ...

    async def get_by_uuid(self, user_uuid: UUID) -> Optional[UserModel]:
        """Получить пользователя по UUID"""
        ...

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """Получить пользователя по email"""
        ...

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """Получить список всех пользователей с пагинацией"""
        ...

    async def update(self, user_uuid: UUID, **kwargs) -> Optional[UserModel]:
        """Обновить данные пользователя"""
        ...

    async def delete(self, user_uuid: UUID) -> bool:
        """Удалить пользователя. Возвращает True если удален, False если не найден"""
        ...

    async def exists(self, user_uuid: UUID) -> bool:
        """Проверить существование пользователя"""
        ...

    async def count(self) -> int:
        """Получить общее количество пользователей"""
        ...


class ImpUserRepository:
    """Реализация репозитория пользователей с async SQLAlchemy"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: UserModel) -> UserModel:
        """Создать нового пользователя"""
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_by_uuid(self, user_uuid: UUID) -> Optional[UserModel]:
        """Получить пользователя по UUID"""
        # Преобразуем UUID в строку для сравнения
        result = await self.session.execute(
            select(UserModel).where(UserModel.uuid == str(user_uuid))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """Получить пользователя по email"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """Получить список всех пользователей с пагинацией"""
        result = await self.session.execute(
            select(UserModel).offset(skip).limit(limit).order_by(UserModel.id)
        )
        return list(result.scalars().all())

    async def update(self, user_uuid: UUID, **kwargs) -> Optional[UserModel]:
        """Обновить данные пользователя"""
        stmt = (
            update(UserModel)
            .where(UserModel.uuid == str(user_uuid))
            .values(**kwargs)
            .returning(UserModel)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete(self, user_uuid: UUID) -> bool:
        """Удалить пользователя. Возвращает True если удален, False если не найден"""
        stmt = delete(UserModel).where(UserModel.uuid == str(user_uuid))
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def exists(self, user_uuid: UUID) -> bool:
        """Проверить существование пользователя"""
        result = await self.session.execute(
            select(func.count())
            .select_from(UserModel)
            .where(UserModel.uuid == str(user_uuid))
        )
        count = result.scalar()
        return count > 0

    async def count(self) -> int:
        """Получить общее количество пользователей"""
        result = await self.session.execute(select(func.count()).select_from(UserModel))
        return result.scalar()
