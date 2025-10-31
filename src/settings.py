from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Union, List


class Settings(BaseSettings):
    """Класс настроек проекта"""

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    DB_SQLITE: str

    app_name: str = "FastAPI test"
    debug: bool = True

    cors_origins: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    static_dir: str = "static"
    images_dir: str = "static/images"

    def database_url_sqlite(self):
        return f"sqlite:///{self.DB_SQLITE}"

    def database_url_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
