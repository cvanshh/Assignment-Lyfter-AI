import os, tempfile
os.environ.update(LLM_API_KEYS="test-a,test-b", LLM_MOCK="true", ENABLE_FAILURE_SIMULATION="true",
                  DATABASE_URL=f"sqlite:///{tempfile.mkdtemp()}/test.db")
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
