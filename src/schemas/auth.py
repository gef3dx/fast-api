from pydantic import BaseModel, EmailStr, Field, ConfigDict


class LoginSchema(BaseModel):
    """Схема для входа"""

    email: EmailStr = Field(description="Email пользователя")
    password: str = Field(min_length=8, max_length=128, description="Пароль")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user@example.com", "password": "SecurePass123!"}
        }
    )


class TokenResponse(BaseModel):
    """Схема ответа с токенами"""

    access_token: str = Field(description="Access токен")
    refresh_token: str = Field(description="Refresh токен")
    token_type: str = Field(default="bearer", description="Тип токена")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "token_type": "bearer",
            }
        }
    )


class RefreshTokenSchema(BaseModel):
    """Схема для обновления токена"""

    refresh_token: str = Field(description="Refresh токен")


class TokenPayload(BaseModel):
    """Payload JWT токена"""

    user_id: int = Field(description="ID пользователя")
    email: str = Field(description="Email пользователя")

    model_config = ConfigDict(
        json_schema_extra={"example": {"user_id": 1, "email": "user@example.com"}}
    )
