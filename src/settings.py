from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Union, List


class Settings(BaseSettings):
    """Класс настроек проекта"""

    # Database PostgreSQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_NAME: str = "fastapi_db"

    # Database SQLite
    DB_SQLITE: str = "database.db"

    # App settings
    app_name: str = "FastAPI test"
    debug: bool = True

    # CORS
    cors_origins: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Directories
    static_dir: str = "static"
    images_dir: str = "static/images"

    @property
    def database_url_sqlite(self) -> str:
        """URL для SQLite базы данных"""
        return f"sqlite+aiosqlite:///{self.DB_SQLITE}"

    @property
    def database_url_asyncpg(self) -> str:
        """URL для PostgreSQL базы данных"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


config = Settings()
