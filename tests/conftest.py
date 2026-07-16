import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.dependencies import get_db
from app.config import settings

TEST_DATABASE_URL = settings.DATABASE_URL


def make_engine():
    return create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"ssl": "require"},
        pool_pre_ping=True,
    )


async def override_get_db():
    engine = make_engine()
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
    await engine.dispose()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def registered_user(client):
    import uuid
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Test User",
        "email": unique_email,
        "password": "testpass123"
    }
    await client.post("/auth/register", json=payload)
    return payload


@pytest_asyncio.fixture(scope="function")
async def auth_headers(client, registered_user):
    response = await client.post("/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"]
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}