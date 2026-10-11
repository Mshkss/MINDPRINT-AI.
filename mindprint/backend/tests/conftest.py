import os
os.environ['DATABASE_URL']='sqlite+aiosqlite:///:memory:'
os.environ['AI_PROVIDER']='mock'
os.environ['DEMO_MODE']='true'
os.environ['DEMO_PASSWORD']='test-only-password'
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.core.database import Base, engine, Session
from app.main import app
from app.seed import seed
from app.api.auth import attempts
from app.core.config import settings

@pytest_asyncio.fixture(autouse=True)
async def database():
    settings().ai_provider='mock'
    settings().demo_mode=True
    attempts.clear()
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.drop_all)
        await c.run_sync(Base.metadata.create_all)
    await seed()
    yield
    await engine.dispose()

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://test') as c:
        yield c

@pytest_asyncio.fixture
async def patient(client):
    response=await client.post('/api/auth/demo',json={'role':'patient'})
    assert response.status_code==200
    return client
