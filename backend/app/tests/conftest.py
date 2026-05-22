import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db

_TEST_DB_URL = "sqlite://"  # in-memory, isolated per test


@pytest_asyncio.fixture
async def client():
    # Lazy import: fails with ModuleNotFoundError until app/main.py exists,
    # keeping test_models.py unaffected during collection.
    from app.main import app
    from httpx import ASGITransport, AsyncClient

    engine = create_engine(_TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
