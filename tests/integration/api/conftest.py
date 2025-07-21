import pytest
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet
from src.api.main import app
from tests.constants import API_BASE_URL


@pytest.fixture(scope="function")
def test_client(monkeypatch) -> TestClient:  # type: ignore
    """
    Provides a TestClient instance with necessary environment variables mocked.
    This fixture is function-scoped to ensure a clean environment for each test.
    """
    # Generate a valid Fernet key for testing
    valid_key = Fernet.generate_key().decode()

    monkeypatch.setenv("ENCRYPTION_KEYS", valid_key)
    monkeypatch.setenv("ETHEREUM_RPC_URL", "http://test-rpc-url.com")

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def base_url() -> str:
    """Provides the base URL for the API endpoints."""
    return API_BASE_URL
