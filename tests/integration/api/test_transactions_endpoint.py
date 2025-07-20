import pytest
from decimal import Decimal
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.dependencies import get_transaction_service
from src.core.entities import Transaction
from src.core.enums import TransactionStatus
from src.core.interfaces import ITransactionService

# Address I will use for filtering
FILTER_ADDRESS = "0x1111111111111111111111111111111111111111"

# list of transactions mocked
MOCK_HISTORY_DATA = [
    Transaction(
        tx_hash="0xabc1",
        asset="ETH",
        from_address=FILTER_ADDRESS,
        to_address="0xTo1",
        value=Decimal("1.0"),
        status=TransactionStatus.CONFIRMED,
        effective_cost=Decimal("0.01")
    ),
    Transaction(
        tx_hash="0xdef2",
        asset="USDC",
        from_address="0xFrom2",
        to_address=FILTER_ADDRESS,
        value=Decimal("100.0"),
        status=TransactionStatus.VALIDATED,
        effective_cost=Decimal("0.02")
    ),
    Transaction(
        tx_hash="0xghi3",
        asset="ETH",
        from_address="0xAnotherAddress",
        to_address="0xYetAnother",
        value=Decimal("5.0"),
        status=TransactionStatus.PENDING,
        effective_cost=Decimal("0.0")
    )
]

# TODO: Use base_url (DRY)


@pytest.mark.asyncio
class TestGetHistoryEndpoint:
    """
    Test suite for the GET /history endpoint.
    """

    def setup_method(self):
        """Clears dependency overrides before each test."""
        app.dependency_overrides.clear()

    async def test_get_all_history_success(self, test_client: TestClient):
        """
        Scenario 1: Tests fetching the complete history successfully.
        """
        # Arrange
        mock_service = AsyncMock(spec=ITransactionService)
        mock_service.get_all_transaction_history.return_value = MOCK_HISTORY_DATA
        app.dependency_overrides[get_transaction_service] = lambda: mock_service

        # Act
        response = test_client.get("/api/v1/transactions/history")

        # Assert
        assert response.status_code == 200

        response_data = response.json()

        assert len(response_data["history"]) == 3
        assert response_data["history"][0]["tx_hash"] == "0xabc1"
        assert response_data["history"][2]["tx_hash"] == "0xghi3"

        # Ensure the correct service method was called
        mock_service.get_all_transaction_history.assert_awaited_once()

    async def test_get_history_filtered_by_address_success(self, test_client: TestClient):
        """
        Scenario 2: Tests fetching the history filtered by a specific address.
        """
        # Arrange
        filtered_data = [tx for tx in MOCK_HISTORY_DATA if FILTER_ADDRESS in (
            tx.from_address, tx.to_address)]
        mock_service = AsyncMock(spec=ITransactionService)
        mock_service.get_transaction_history_for_address.return_value = filtered_data
        app.dependency_overrides[get_transaction_service] = lambda: mock_service

        # Act
        response = test_client.get(
            f"/api/v1/transactions/history?address={FILTER_ADDRESS}")

        # Assert
        assert response.status_code == 200

        response_data = response.json()

        assert len(response_data["history"]) == 2
        assert response_data["history"][0]["tx_hash"] == "0xabc1"
        assert response_data["history"][1]["tx_hash"] == "0xdef2"

        # Ensure the filtering service method was called with the correct address
        mock_service.get_transaction_history_for_address.assert_awaited_once_with(
            FILTER_ADDRESS)

    async def test_get_history_returns_empty_list_when_no_transactions(self, test_client: TestClient):
        """
        Scenario 3: Tests the case where there are no transactions in the history.
        """
        # Arrange
        mock_service = AsyncMock(spec=ITransactionService)
        mock_service.get_all_transaction_history.return_value = []
        app.dependency_overrides[get_transaction_service] = lambda: mock_service

        # Act
        response = test_client.get("/api/v1/transactions/history")

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["history"] == []

    async def test_get_history_returns_500_on_service_error(self, test_client: TestClient):
        """
        Scenario 4: Tests that the endpoint returns a 500 error if the service fails.
        """
        # Arrange
        mock_service = AsyncMock(spec=ITransactionService)
        mock_service.get_all_transaction_history.side_effect = Exception(
            "Database connection failed")
        app.dependency_overrides[get_transaction_service] = lambda: mock_service

        # Act
        response = test_client.get("/api/v1/transactions/history")

        # Assert
        assert response.status_code == 500
        assert "Failed to retrieve transaction history" in response.json()[
            "detail"]
