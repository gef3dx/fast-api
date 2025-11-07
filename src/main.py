from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import user
from database.postgres import async_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление lifecycle приложения
    - startup: действия при запуске приложения
    - shutdown: действия при остановке приложения
    """
    # Startup - код выполняется при запуске
    print("🚀 Starting up application...")

    # Здесь можно инициализировать соединения, кэши и т.д.
    # Например, проверка подключения к БД
    try:
        async with async_engine.begin():
            print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

    yield  # Приложение работает

    # Shutdown - код выполняется при остановке
    print("🛑 Shutting down application...")
    await async_engine.dispose()
    print("✅ Database connections closed")


# Создание FastAPI приложения
app = FastAPI(
    title="User Management API",
    description="API для управления пользователями с использованием Repository и Service паттернов",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# Настройка CORS (если необходимо для frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключение роутеров
app.include_router(
    user.router, prefix="/api/v1", tags=["users"]  # Префикс для версионирования API
)


# Корневой эндпоинт
@app.get("/", tags=["root"])
async def root():
    """Корневой эндпоинт для проверки работы API"""
    return {
        "message": "Welcome to User Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


# Эндпоинт для health check
@app.get("/health", tags=["health"])
async def health_check():
    """Проверка состояния приложения"""
    return {"status": "healthy", "database": "connected"}


# Обработчик ошибок (опционально)
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Not Found",
        "message": "The requested resource was not found",
        "path": str(request.url),
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {
        "error": "Internal Server Error",
        "message": "An internal error occurred. Please try again later.",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Автоперезагрузка при изменении кода (только для development)
        log_level="info",
    )
