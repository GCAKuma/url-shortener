import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite:///./test.db", connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Fresh tables for every test so tests don't leak state into each other."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ui_page_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "URL Shortener" in response.text


def test_shorten_url_returns_short_code():
    response = client.post("/shorten", json={"url": "https://www.example.com"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["short_code"]) == 6
    assert data["original_url"] == "https://www.example.com/"


def test_shorten_rejects_invalid_url():
    response = client.post("/shorten", json={"url": "not-a-url"})
    assert response.status_code == 422


def test_redirect_follows_to_original_url():
    shorten_response = client.post("/shorten", json={"url": "https://www.example.com"})
    short_code = shorten_response.json()["short_code"]

    redirect_response = client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://www.example.com/"


def test_redirect_unknown_code_returns_404():
    response = client.get("/doesnotexist", follow_redirects=False)
    assert response.status_code == 404


def test_stats_track_click_count():
    shorten_response = client.post("/shorten", json={"url": "https://www.example.com"})
    short_code = shorten_response.json()["short_code"]

    client.get(f"/{short_code}", follow_redirects=False)
    client.get(f"/{short_code}", follow_redirects=False)

    stats_response = client.get(f"/stats/{short_code}")
    assert stats_response.status_code == 200
    assert stats_response.json()["clicks"] == 2


def test_stats_unknown_code_returns_404():
    response = client.get("/stats/doesnotexist")
    assert response.status_code == 404
