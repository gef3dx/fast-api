# src/utils/security.py
"""
Утилиты для работы с безопасностью: хеширование паролей и их проверка
"""
import bcrypt


def hash_password(password: str) -> str:
    """
    Хеширует пароль с использованием bcrypt

    Args:
        password: Пароль в открытом виде

    Returns:
        str: Хешированный пароль
    """
    # Ограничиваем длину пароля до 72 байт (требование bcrypt)
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля его хешу

    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль из БД

    Returns:
        bool: True если пароль совпадает, False если нет
    """
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)
