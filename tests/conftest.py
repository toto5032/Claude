import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.environ.get("APP_DATABASE_URL", "sqlite:///./test.db")

connect_args = {}
if TEST_DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(TEST_DATABASE_URL, connect_args=connect_args)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_header(client):
    """Register a test user and return an Authorization header dict."""
    client.post(
        "/auth/register",
        json={
            "username": "fixtureuser",
            "email": "fixture@example.com",
            "password": "testpass",
        },
    )
    resp = client.post(
        "/auth/login",
        data={"username": "fixtureuser", "password": "testpass"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _register_and_set_role(client, db, username, email, role):
    """Helper: register user, set role, return auth header."""
    from app.models.user import User

    client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": "testpass"},
    )
    user = db.query(User).filter(User.username == username).first()
    user.role = role
    db.commit()
    resp = client.post(
        "/auth/login",
        data={"username": username, "password": "testpass"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_header(client, db):
    """Return auth header for an admin user."""
    return _register_and_set_role(client, db, "adminuser", "admin@test.com", "admin")


@pytest.fixture()
def member_header(client, db):
    """Return auth header for a member user."""
    return _register_and_set_role(
        client, db, "memberuser", "member@test.com", "member"
    )


@pytest.fixture()
def fan_header(client, db):
    """Return auth header for a fan user."""
    return _register_and_set_role(client, db, "fanuser", "fan@test.com", "fan")
