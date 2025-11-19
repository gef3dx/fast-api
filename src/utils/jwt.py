from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

from settings import config


class TokenData(BaseModel):
    """Данные из токена"""

    user_id: int
    email: str
    exp: datetime


def create_access_token(user_id: int, email: str) -> str:
    """
    Создать access токен

    Args:
        user_id: ID пользователя
        email: Email пользователя

    Returns:
        str: JWT токен
    """
    expire = datetime.utcnow() + timedelta(
        minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {"user_id": user_id, "email": email, "exp": expire, "type": "access"}

    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def create_refresh_token(user_id: int, email: str) -> str:
    """
    Создать refresh токен

    Args:
        user_id: ID пользователя
        email: Email пользователя

    Returns:
        str: JWT токен
    """
    expire = datetime.utcnow() + timedelta(days=config.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {"user_id": user_id, "email": email, "exp": expire, "type": "refresh"}

    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """
    Проверить и декодировать токен

    Args:
        token: JWT токен
        token_type: Тип токена (access/refresh)

    Returns:
        TokenData или None если токен невалидный
    """
    try:
        payload = jwt.decode(
            token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM]
        )

        # Проверяем тип токена
        if payload.get("type") != token_type:
            return None

        return TokenData(
            user_id=payload.get("user_id"),
            email=payload.get("email"),
            exp=datetime.fromtimestamp(payload.get("exp")),
        )
    except InvalidTokenError:
        return None


def decode_token_no_verify(token: str) -> Optional[dict]:
    """
    Декодировать токен без проверки (для отладки)

    Args:
        token: JWT токен

    Returns:
        dict с данными или None
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception:
        return None
