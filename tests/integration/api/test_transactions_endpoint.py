from fastapi.testclient import TestClient
from src.api.main import app

# Arrange
client = TestClient(app)


def test_get_transaction_welcome():
    """
    Tests the welcome endpoint of the transactions router.

    It verifies that the endpoint:
    1. Returns a successful 200 OK status code.
    2. Returns the correct JSON payload.
    """
    # Act
    response = client.get("/transactions/welcome")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        'message': 'Welcome to transactions endpoint!!'}
