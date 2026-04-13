from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import AppContainer, create_app


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def test_env(repo_root: Path):
    os.environ.setdefault("APP_DATA_DIR", "data")
    os.environ.setdefault("SESSION_DB_PATH", str(repo_root / "artifacts" / "generated" / "test_sessions.db"))
    os.environ.setdefault("EMBEDDING_BACKEND", "tfidf")
    os.environ.setdefault("LLM_BACKEND", "heuristic")
    yield


@pytest.fixture(scope="session")
def container(repo_root: Path) -> AppContainer:
    return AppContainer(repo_root)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())
