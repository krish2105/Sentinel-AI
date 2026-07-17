import os

# Force an isolated test database + mock engine before app import.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_sentinel.db")
os.environ.setdefault("FORCE_MOCK_LLM", "true")
os.environ.setdefault("ENABLE_HEAVY_ML", "false")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client():
    from app.db.session import init_db
    from app.main import app

    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
