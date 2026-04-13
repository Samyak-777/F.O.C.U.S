"""
Shared fixtures used across all test modules.
Uses in-memory SQLite for speed. No file system side effects.
"""
import pytest
import numpy as np
import cv2
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient
from app import create_app
from src.db.models import Base, User, UserRole, ClassSession, ConsentRecord
from src.db.session import get_db
from datetime import datetime
from unittest.mock import patch

@pytest.fixture(autouse=True)
def bypass_password_verification():
    with patch("src.api.routes.auth.verify_password", return_value=True):
        yield

# ──────────────────────────────────────────────────────────────────────────────
# Database fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def test_engine():
    """Fresh in-memory SQLite engine per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Database session bound to in-memory engine."""
    TestingSession = sessionmaker(bind=test_engine)
    session = TestingSession()
    yield session
    session.close()


@pytest.fixture(scope="function")
def app(db_session):
    """FastAPI app with overridden DB dependency."""
    fastapi_app = create_app()

    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    return fastapi_app


@pytest.fixture(scope="function")
def client(app):
    """Synchronous test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
async def async_client(app):
    """Async test client for async route testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ──────────────────────────────────────────────────────────────────────────────
# User / Student fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def student_user(db_session):
    """A standard adult student with consent given."""
    user = User(
        roll_number="BT23CSE001",
        name="Riya Sharma",
        email="riya@vnit.ac.in",
        hashed_password="$2b$12$fake_hash",
        role=UserRole.STUDENT,
        preferred_language="hi",
        is_minor=False
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def minor_student_user(db_session):
    """A student who is a legal minor — requires guardian consent."""
    user = User(
        roll_number="BT23CSE002",
        name="Minor Student",
        email="minor@vnit.ac.in",
        hashed_password="$2b$12$fake_hash",
        role=UserRole.STUDENT,
        is_minor=True,
        guardian_consent_obtained=False
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def faculty_user(db_session):
    """A faculty member."""
    user = User(
        roll_number=None,
        name="Prof. Anand Kulkarni",
        email="anand@vnit.ac.in",
        hashed_password="$2b$12$fake_hash",
        role=UserRole.FACULTY
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session):
    """An admin user."""
    user = User(
        roll_number=None,
        name="Meera Desai",
        email="meera@vnit.ac.in",
        hashed_password="$2b$12$fake_hash",
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def active_session(db_session, faculty_user):
    """An active class session."""
    session = ClassSession(
        batch_id="CSE-3A-2026",
        faculty_id=faculty_user.id,
        room_id="LH-101",
        scheduled_start=datetime(2026, 4, 2, 9, 0, 0),
        actual_start=datetime(2026, 4, 2, 9, 0, 30),
        status="active"
    )
    db_session.add(session)
    db_session.commit()
    return session


# ──────────────────────────────────────────────────────────────────────────────
# Image / frame fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def blank_frame_720p():
    """Blank 1280×720 BGR frame for unit tests."""
    return np.zeros((720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def synthetic_face_frame():
    """
    A simple synthetic frame with a drawn ellipse representing a face.
    Does NOT require a real camera or real face. Used for shape/pipeline tests.
    """
    frame = np.ones((720, 1280, 3), dtype=np.uint8) * 200  # Light gray background
    # Draw a rough face ellipse
    cv2.ellipse(frame, (640, 360), (80, 100), 0, 0, 360, (220, 180, 150), -1)
    # Eyes
    cv2.circle(frame, (610, 330), 10, (50, 50, 50), -1)
    cv2.circle(frame, (670, 330), 10, (50, 50, 50), -1)
    return frame


@pytest.fixture
def multi_face_frame():
    """Frame with 3 synthetic face ellipses at different positions."""
    frame = np.ones((720, 1280, 3), dtype=np.uint8) * 200
    positions = [(213, 360), (640, 360), (1067, 360)]
    for cx, cy in positions:
        cv2.ellipse(frame, (cx, cy), (80, 100), 0, 0, 360, (220, 180, 150), -1)
        cv2.circle(frame, (cx - 30, cy - 30), 10, (50, 50, 50), -1)
        cv2.circle(frame, (cx + 30, cy - 30), 10, (50, 50, 50), -1)
    return frame


@pytest.fixture
def auth_headers_faculty(client, faculty_user):
    """JWT auth headers for faculty user."""
    resp = client.post("/api/auth/login", data={
        "username": "anand@vnit.ac.in",
        "password": "testpass123"
    })
    token = resp.json().get("access_token", "fake_token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_admin(client, admin_user):
    """JWT auth headers for admin user."""
    resp = client.post("/api/auth/login", data={
        "username": "meera@vnit.ac.in",
        "password": "testpass123"
    })
    token = resp.json().get("access_token", "fake_token")
    return {"Authorization": f"Bearer {token}"}