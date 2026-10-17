import json
import os
from typing import Dict, Generator

import pytest
from fastapi.testclient import TestClient

os.environ["ENV"] = "test"
os.environ["DB"] = "sqlite"

from campus_grid.core.config import configs
from campus_grid.core.container import Container
from campus_grid.core.security import get_password_hash
from campus_grid.main import AppCreator
from campus_grid.model.base_model import Base
from campus_grid.model.resource import Resource
from campus_grid.model.user import User, UserRole

# Pre-compute password hash once to speed up test execution
PRECOMPUTED_HASH = get_password_hash("Password123!")


def seed_test_database(session_factory):
    with session_factory() as session:
        # Seed Users
        with open("./tests/test_data/users.json", "r") as f:
            users_data = json.load(f)
            for u in users_data:
                user = User(
                    email=u["email"],
                    hashed_password=PRECOMPUTED_HASH,
                    role=UserRole(u["role"]),
                    is_active=u["is_active"],
                )
                session.add(user)

        # Seed Resources
        with open("./tests/test_data/resources.json", "r") as f:
            resources_data = json.load(f)
            for r in resources_data:
                resource = Resource(
                    name=r["name"],
                    category=r["category"],
                    total_quantity=r["total_quantity"],
                    available_quantity=r["available_quantity"],
                    status=r["status"],
                )
                session.add(resource)

        session.commit()


@pytest.fixture(scope="session")
def app_instance():
    app_creator = AppCreator()
    return app_creator.app


@pytest.fixture
def client(app_instance) -> Generator[TestClient, None, None]:
    # Reset in-memory database per test run
    app_creator = AppCreator()
    engine = app_creator.db._engine
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    seed_test_database(app_creator.db.session)

    with TestClient(app_instance) as test_client:
        yield test_client


@pytest.fixture
def container():
    return Container()


@pytest.fixture
def student_auth_headers(client) -> Dict[str, str]:
    resp = client.post("/api/v1/auth/sign-in", json={"email": "student1@campus.edu", "password": "Password123!"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student2_auth_headers(client) -> Dict[str, str]:
    resp = client.post("/api/v1/auth/sign-in", json={"email": "student2@campus.edu", "password": "Password123!"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def faculty_auth_headers(client) -> Dict[str, str]:
    resp = client.post("/api/v1/auth/sign-in", json={"email": "faculty@campus.edu", "password": "Password123!"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client) -> Dict[str, str]:
    resp = client.post("/api/v1/auth/sign-in", json={"email": "admin@campus.edu", "password": "Password123!"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
