from typing import Protocol, Optional
from fastapi import HTTPException, status

from repositories import UserRepository
from schemas.auth import LoginSchema, TokenResponse
from utils.security import verify_password
from utils.jwt import create_access_token, create_refresh_token, verify_token
from models import UserModel


class AuthService(Protocol):
    """Протокол сервиса аутентификации"""

    async def login(self, credentials: LoginSchema) -> TokenResponse:
        """Войти в систему"""
        ...

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Обновить токены"""
        ...


class ImpAuthService:
    """Реализация сервиса аутентификации"""

    def __init__(self, user_repository: UserRepository):
        self.repository = user_repository

    async def login(self, credentials: LoginSchema) -> TokenResponse:
        """
        Войти в систему

        Args:
            credentials: Данные для входа (email, password)

        Returns:
            TokenResponse: Access и refresh токены

        Raises:
            HTTPException: 401 если неверные credentials
        """
        # Получаем пользователя по email
        user = await self.repository.get_by_email(credentials.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Проверяем пароль
        if not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Проверяем активность
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
            )

        # Создаем токены
        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id, user.email)

        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Обновить токены по refresh токену

        Args:
            refresh_token: Refresh токен

        Returns:
            TokenResponse: Новые access и refresh токены

        Raises:
            HTTPException: 401 если токен невалидный
        """
        # Проверяем refresh токен
        token_data = verify_token(refresh_token, token_type="refresh")

        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Проверяем существование пользователя
        user = await self.repository.get_by_email(token_data.email)

        if not user:
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

        # Создаем новые токены
        new_access_token = create_access_token(user.id, user.email)
        new_refresh_token = create_refresh_token(user.id, user.email)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )
