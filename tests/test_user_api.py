import pytest
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from uuid import uuid4

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from dependencies import get_async_session
from models.base import BaseModelSql
from settings import config


# Тестовая база данных
TEST_DATABASE_URL = f"postgresql+asyncpg://{config.DB_USER}:{config.DB_PASS}@{config.DB_HOST}:{config.DB_PORT}/test_{config.DB_NAME}"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


# Фикстура для создания/удаления тестовой БД
@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Создать тестовую базу данных перед тестами"""
    # Подключаемся к postgres для создания тестовой БД
    engine = create_async_engine(
        f"postgresql+asyncpg://{config.DB_USER}:{config.DB_PASS}@{config.DB_HOST}:{config.DB_PORT}/postgres",
        isolation_level="AUTOCOMMIT",
    )

    async with engine.connect() as conn:
        # Удаляем тестовую БД если существует
        await conn.execute(text(f"DROP DATABASE IF EXISTS test_{config.DB_NAME}"))
        # Создаем тестовую БД
        await conn.execute(text(f"CREATE DATABASE test_{config.DB_NAME}"))

    await engine.dispose()

    # Создаем таблицы
    async with test_engine.begin() as conn:
        await conn.run_sync(BaseModelSql.metadata.create_all)

    yield

    # Очистка после всех тестов
    await test_engine.dispose()

    # Удаляем тестовую БД
    engine = create_async_engine(
        f"postgresql+asyncpg://{config.DB_USER}:{config.DB_PASS}@{config.DB_HOST}:{config.DB_PORT}/postgres",
        isolation_level="AUTOCOMMIT",
    )
    async with engine.connect() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS test_{config.DB_NAME}"))
    await engine.dispose()


# Фикстура для сессии БД
@pytest.fixture
async def db_session():
    """Получить тестовую сессию БД"""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


# Фикстура для переопределения зависимости
@pytest.fixture
async def override_get_db(db_session):
    """Переопределить зависимость get_async_session"""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_async_session] = _override_get_db
    yield
    app.dependency_overrides.clear()


# Фикстура для HTTP клиента
@pytest.fixture
async def client(override_get_db):
    """Получить HTTP клиент для тестирования"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Фикстура для тестовых данных пользователя
@pytest.fixture
def user_data():
    """Тестовые данные для создания пользователя"""
    return {
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "user_name": f"testuser_{uuid4().hex[:8]}",
        "name": "TestNme",
        "first_name": "Test",
        "last_name": "User",
        "phone": f"+7909{uuid4().hex[:7]}",
        "password": "TestPassword123!",
    }


# ============= ТЕСТЫ ROOT ЭНДПОИНТОВ =============


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Тест корневого эндпоинта"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check(client):
    """Тест health check эндпоинта"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


# ============= ТЕСТЫ СОЗДАНИЯ ПОЛЬЗОВАТЕЛЯ =============


@pytest.mark.asyncio
async def test_create_user_success(client, user_data):
    """Тест успешного создания пользователя"""
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["user_name"] == user_data["user_name"]
    assert data["name"] == user_data["name"]
    assert data["first_name"] == user_data["first_name"]
    assert data["last_name"] == user_data["last_name"]
    assert data["is_active"] is True
    assert data["is_admin"] is False
    assert "uuid" in data
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client, user_data):
    """Тест создания пользователя с дублирующимся email"""
    # Создаем первого пользователя
    await client.post("/api/v1/users/", json=user_data)

    # Пытаемся создать второго с тем же email
    user_data["user_name"] = f"another_{uuid4().hex[:8]}"
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_user_invalid_email(client, user_data):
    """Тест создания пользователя с невалидным email"""
    user_data["email"] = "invalid-email"
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_short_password(client, user_data):
    """Тест создания пользователя с коротким паролем"""
    user_data["password"] = "123"
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_short_username(client, user_data):
    """Тест создания пользователя с коротким username"""
    user_data["user_name"] = "ab"
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422


# ============= ТЕСТЫ ПОЛУЧЕНИЯ ПОЛЬЗОВАТЕЛЯ =============


@pytest.mark.asyncio
async def test_get_user_by_uuid(client, user_data):
    """Тест получения пользователя по UUID"""
    # Создаем пользователя
    create_response = await client.post("/api/v1/users/", json=user_data)
    user_uuid = create_response.json()["uuid"]

    # Получаем пользователя
    response = await client.get(f"/api/v1/users/{user_uuid}")
    assert response.status_code == 200

    data = response.json()
    assert data["uuid"] == user_uuid
    assert data["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_get_user_not_found(client):
    """Тест получения несуществующего пользователя"""
    fake_uuid = str(uuid4())
    response = await client.get(f"/api/v1/users/{fake_uuid}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user_invalid_uuid(client):
    """Тест получения пользователя с невалидным UUID"""
    response = await client.get("/api/v1/users/invalid-uuid")
    assert response.status_code == 422


# ============= ТЕСТЫ СПИСКА ПОЛЬЗОВАТЕЛЕЙ =============


@pytest.mark.asyncio
async def test_list_users(client, user_data):
    """Тест получения списка пользователей"""
    # Создаем несколько пользователей
    for i in range(3):
        data = user_data.copy()
        data["email"] = f"test{i}_{uuid4().hex[:8]}@example.com"
        data["user_name"] = f"testuser{i}_{uuid4().hex[:8]}"
        data["phone"] = f"+7909{uuid4().hex[:7]}"
        await client.post("/api/v1/users/", json=data)

    # Получаем список
    response = await client.get("/api/v1/users/list")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_list_users_with_pagination(client, user_data):
    """Тест пагинации списка пользователей"""
    # Создаем пользователей
    for i in range(5):
        data = user_data.copy()
        data["email"] = f"test{i}_{uuid4().hex[:8]}@example.com"
        data["user_name"] = f"testuser{i}_{uuid4().hex[:8]}"
        data["phone"] = f"+7909{uuid4().hex[:7]}"
        await client.post("/api/v1/users/", json=data)

    # Тест пагинации
    response = await client.get("/api/v1/users/list?skip=0&limit=2")
    assert response.status_code == 200
    assert len(response.json()) <= 2

    response = await client.get("/api/v1/users/list?skip=2&limit=2")
    assert response.status_code == 200
    assert len(response.json()) <= 2


# ============= ТЕСТЫ ОБНОВЛЕНИЯ ПОЛЬЗОВАТЕЛЯ =============


@pytest.mark.asyncio
async def test_update_user(client, user_data):
    """Тест обновления пользователя"""
    # Создаем пользователя
    create_response = await client.post("/api/v1/users/", json=user_data)
    user_uuid = create_response.json()["uuid"]

    # Обновляем данные
    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "phone": "+79991111111",
    }
    response = await client.patch(f"/api/v1/users/{user_uuid}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"
    assert data["phone"] == "+79991111111"
    assert data["email"] == user_data["email"]  # email не изменился


@pytest.mark.asyncio
async def test_update_user_not_found(client):
    """Тест обновления несуществующего пользователя"""
    fake_uuid = str(uuid4())
    update_data = {"first_name": "Test"}
    response = await client.patch(f"/api/v1/users/{fake_uuid}", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_duplicate_email(client, user_data):
    """Тест обновления с дублирующимся email"""
    # Создаем двух пользователей
    response1 = await client.post("/api/v1/users/", json=user_data)
    user1_uuid = response1.json()["uuid"]

    user_data2 = user_data.copy()
    user_data2["email"] = f"another_{uuid4().hex[:8]}@example.com"
    user_data2["user_name"] = f"another_{uuid4().hex[:8]}"
    user_data2["phone"] = f"+7909{uuid4().hex[:7]}"
    response2 = await client.post("/api/v1/users/", json=user_data2)

    # Пытаемся обновить email первого пользователя на email второго
    update_data = {"email": user_data2["email"]}
    response = await client.patch(f"/api/v1/users/{user1_uuid}", json=update_data)
    assert response.status_code == 400


# ============= ТЕСТЫ УДАЛЕНИЯ ПОЛЬЗОВАТЕЛЯ =============


@pytest.mark.asyncio
async def test_delete_user(client, user_data):
    """Тест удаления пользователя"""
    # Создаем пользователя
    create_response = await client.post("/api/v1/users/", json=user_data)
    user_uuid = create_response.json()["uuid"]

    # Удаляем пользователя
    response = await client.delete(f"/api/v1/users/{user_uuid}")
    assert response.status_code == 204

    # Проверяем, что пользователь удален
    get_response = await client.get(f"/api/v1/users/{user_uuid}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_not_found(client):
    """Тест удаления несуществующего пользователя"""
    fake_uuid = str(uuid4())
    response = await client.delete(f"/api/v1/users/{fake_uuid}")
    assert response.status_code == 404


# ============= ТЕСТЫ АКТИВАЦИИ/ДЕАКТИВАЦИИ =============


@pytest.mark.asyncio
async def test_deactivate_user(client, user_data):
    """Тест деактивации пользователя"""
    # Создаем пользователя
    create_response = await client.post("/api/v1/users/", json=user_data)
    user_uuid = create_response.json()["uuid"]

    # Деактивируем
    response = await client.post(f"/api/v1/users/{user_uuid}/deactivate")
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_activate_user(client, user_data):
    """Тест активации пользователя"""
    # Создаем и деактивируем пользователя
    create_response = await client.post("/api/v1/users/", json=user_data)
    user_uuid = create_response.json()["uuid"]
    await client.post(f"/api/v1/users/{user_uuid}/deactivate")

    # Активируем
    response = await client.post(f"/api/v1/users/{user_uuid}/activate")
    assert response.status_code == 200
    assert response.json()["is_active"] is True


@pytest.mark.asyncio
async def test_activate_already_active_user(client, user_data):
    """Тест активации уже активного пользователя"""
    # Создаем пользователя (по умолчанию активен)
    create_response = await client.post("/api/v1/users/", json=user_data)
    user_uuid = create_response.json()["uuid"]

    # Пытаемся активировать
    response = await client.post(f"/api/v1/users/{user_uuid}/activate")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_deactivate_already_inactive_user(client, user_data):
    """Тест деактивации уже неактивного пользователя"""
    # Создаем и деактивируем пользователя
    create_response = await client.post("/api/v1/users/", json=user_data)
    user_uuid = create_response.json()["uuid"]
    await client.post(f"/api/v1/users/{user_uuid}/deactivate")

    # Пытаемся деактивировать снова
    response = await client.post(f"/api/v1/users/{user_uuid}/deactivate")
    assert response.status_code == 400


# ============= ТЕСТЫ АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ =============


@pytest.mark.asyncio
async def test_list_active_users(client, user_data):
    """Тест получения списка активных пользователей"""
    # Создаем активного пользователя
    response1 = await client.post("/api/v1/users/", json=user_data)

    # Создаем и деактивируем второго пользователя
    user_data2 = user_data.copy()
    user_data2["email"] = f"inactive_{uuid4().hex[:8]}@example.com"
    user_data2["user_name"] = f"inactive_{uuid4().hex[:8]}"
    user_data2["phone"] = f"+7909{uuid4().hex[:7]}"
    response2 = await client.post("/api/v1/users/", json=user_data2)
    user2_uuid = response2.json()["uuid"]
    await client.post(f"/api/v1/users/{user2_uuid}/deactivate")

    # Получаем список активных пользователей
    response = await client.get("/api/v1/users/active")
    assert response.status_code == 200

    active_users = response.json()
    # Все пользователи в списке должны быть активными
    for user in active_users:
        assert user["is_active"] is True
