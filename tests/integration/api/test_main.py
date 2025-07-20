from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health_checks():
    """
    Tests if the Blockchain Ethereum API is healthy.

    It verifies that the endpoint:
    1. Returns a successful 200 OK status code.
    2. Returns the correct JSON payload.
    """
    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        'healthy': True}
