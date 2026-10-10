import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.core.security import get_password_hash

TEST_DB = "./test_suite.db"
test_engine = create_engine(
    f"sqlite:///{TEST_DB}",
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create fresh isolated tables and seed demo accounts for the test suite."""
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except OSError:
            pass

    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db

    # Seed demo users in test DB
    db = TestingSessionLocal()
    try:
        demo_users = [
            ("analyst@agentsec.com", "Security Analyst", "AnalystPass123!", UserRole.REVIEWER),
            ("admin@agentsec.com", "Security Administrator", "AdminPass123!", UserRole.ADMIN),
            ("user@agentsec.com", "Standard User", "UserPass123!", UserRole.USER),
        ]
        for email, name, pwd, role in demo_users:
            db.add(User(
                email=email,
                full_name=name,
                password_hash=get_password_hash(pwd),
                role=role,
                is_active=True,
            ))
        db.commit()
    finally:
        db.close()

    yield

    # Teardown
    app.dependency_overrides.clear()
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except OSError:
            pass


@pytest.fixture
def client():
    """TestClient fixture with test dependency overrides active."""
    with TestClient(app) as c:
        yield c
