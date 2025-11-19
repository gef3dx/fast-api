from typing import Annotated
from fastapi import APIRouter, Depends, Response, status, Request, HTTPException
from fastapi.responses import JSONResponse

from services.auth import AuthService, ImpAuthService
from repositories import UserRepository
from dependencies import get_user_repository
from dependencies import get_current_user, get_current_active_user
from schemas.auth import LoginSchema, TokenResponse, RefreshTokenSchema, TokenPayload
from schemas import UserResponseSchemas
from models import UserModel


router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    """Dependency для получения сервиса аутентификации"""
    return ImpAuthService(repository)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginSchema,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """
    Войти в систему

    Возвращает токены и устанавливает их в cookies
    """
    tokens = await service.login(credentials)

    # Устанавливаем токены в httpOnly cookies
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=True,  # Только для HTTPS в production
        samesite="lax",
        max_age=15 * 60,  # 15 минут
    )

    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,  # Только для HTTPS в production
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 дней
    )

    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """
    Обновить токены используя refresh токен из cookies
    """
    # Получаем refresh токен из cookies
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Обновляем токены
    tokens = await service.refresh_token(refresh_token)

    # Обновляем cookies
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=15 * 60,
    )

    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )

    return tokens


@router.post("/logout")
async def logout(response: Response) -> dict:
    """
    Выйти из системы

    Удаляет токены из cookies
    """
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponseSchemas)
async def get_me(
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
) -> UserResponseSchemas:
    """
    Получить информацию о текущем пользователе

    Требует аутентификации
    """
    return UserResponseSchemas.model_validate(current_user)


@router.get("/verify")
async def verify_token_endpoint(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> TokenPayload:
    """
    Проверить токен

    Возвращает данные пользователя если токен валидный
    """
    return TokenPayload(user_id=current_user.id, email=current_user.email)
