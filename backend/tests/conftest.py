import os

# Force an isolated test database + mock engine before app import.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_sentinel.db")
os.environ.setdefault("FORCE_MOCK_LLM", "true")
os.environ.setdefault("ENABLE_HEAVY_ML", "false")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def _reset_sse_exit_event():
    """sse-starlette caches a module-global exit Event bound to the first event
    loop it sees; pytest-asyncio uses a fresh loop per test, so reset it before
    each test to avoid 'Event bound to a different event loop' across SSE tests."""
    try:
        from sse_starlette.sse import AppStatus

        AppStatus.should_exit_event = None
    except Exception:
        pass
    yield


@pytest_asyncio.fixture
async def client():
    from app.db.session import init_db
    from app.main import app

    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
