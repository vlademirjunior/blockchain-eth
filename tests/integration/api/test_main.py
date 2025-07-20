from fastapi.testclient import TestClient

from src.api.main import app

# Arrange
client = TestClient(app)


def test_read_main():
    """
    Tests the root endpoint of the transactions router.

    It verifies that the endpoint:
    1. Returns a successful 200 OK status code.
    2. Returns the correct JSON payload.
    """
    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        'msg': "Ethereum Interaction API"}
