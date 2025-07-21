import pytest
from decimal import Decimal
from unittest.mock import AsyncMock
from fastapi import status
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.dependencies import get_transaction_service
from src.core.entities.transaction import Transaction as TransactionEntity
from src.core.enums import TransactionStatus
from src.core.interfaces import ITransactionService
from tests.constants import MOCK_TX_HASH, DEFAULT_ASSET, DEFAULT_VALUE_DECIMAL, DEFAULT_EFFECTIVE_COST_DECIMAL


# Address I will use for filtering
FILTER_ADDRESS = "0x1111111111111111111111111111111111111111"

# list of transactions mocked
MOCK_HISTORY_DATA = [
    TransactionEntity(
        tx_hash="0xabc1", asset="ETH", from_address=FILTER_ADDRESS, to_address="0xTo1",
        value=Decimal("1.0"), status=TransactionStatus.CONFIRMED, effective_cost=Decimal("0.01")
    ),
    TransactionEntity(
        tx_hash="0xdef2", asset="USDC", from_address="0xFrom2", to_address=FILTER_ADDRESS,
        value=Decimal("100.0"), status=TransactionStatus.VALIDATED, effective_cost=Decimal("0.02")
    ),
    TransactionEntity(
        tx_hash="0xghi3", asset="ETH", from_address="0xAnotherAddress", to_address="0xYetAnother",
        value=Decimal("5.0"), status=TransactionStatus.PENDING, effective_cost=Decimal("0.0")
    )
]


class BaseEndpointTest:
    def setup_method(self):
        """Clears dependency overrides before each test."""
        app.dependency_overrides.clear()

    def teardown_method(self):
        """Ensures overrides are cleared after each test."""
        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestGetHistoryEndpoint(BaseEndpointTest):
    """Test suite for the GET /history endpoint."""

    async def test_get_all_history_success(self, test_client: TestClient, base_url: str):
        mock_service = AsyncMock(spec=ITransactionService)
        mock_service.get_all_transaction_history.return_value = MOCK_HISTORY_DATA

        app.dependency_overrides[get_transaction_service] = lambda: mock_service

        response = test_client.get(f"{base_url}/transactions/history")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["history"]) == 3

        mock_service.get_all_transaction_history.assert_awaited_once()

    async def test_get_history_filtered_by_address_success(self, test_client: TestClient, base_url: str):
        filtered_data = [tx for tx in MOCK_HISTORY_DATA if FILTER_ADDRESS in (
            tx.from_address, tx.to_address)]

        mock_service = AsyncMock(spec=ITransactionService)
        mock_service.get_transaction_history_for_address.return_value = filtered_data

        app.dependency_overrides[get_transaction_service] = lambda: mock_service

        response = test_client.get(
            f"{base_url}/transactions/history?address={FILTER_ADDRESS}")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["history"]) == 2

        mock_service.get_transaction_history_for_address.assert_awaited_once_with(
            FILTER_ADDRESS)


@pytest.mark.asyncio
class TestValidateTransactionEndpoint(BaseEndpointTest):
    """Test suite for the POST /validate endpoint."""

    async def test_validate_transaction_success(self, test_client: TestClient, base_url: str):
        """Scenario: Tests successful validation of a transaction."""
        # Arrange
        tx_hash = "0x" + "a" * 64
        mock_validated_tx = TransactionEntity(
            tx_hash=MOCK_TX_HASH, asset=DEFAULT_ASSET, from_address="0xFrom", to_address="0xTo",
            value=DEFAULT_VALUE_DECIMAL, status=TransactionStatus.VALIDATED, effective_cost=DEFAULT_EFFECTIVE_COST_DECIMAL
        )
        mock_service = AsyncMock(spec=ITransactionService)
        mock_service.validate_onchain_transaction.return_value = mock_validated_tx
        app.dependency_overrides[get_transaction_service] = lambda: mock_service

        # Act
        response = test_client.post(
            f"{base_url}/transactions/validate", json={"tx_hash": tx_hash})

        # Assert
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["is_valid"] is True
        assert response_data["transfer"]["asset"] == "ETH"

        mock_service.validate_onchain_transaction.assert_awaited_once_with(
            tx_hash)

    async def test_validate_transaction_not_found(self, test_client: TestClient, base_url: str):
        """Scenario: Tests response when the transaction is not found or invalid."""
        # Arrange
        tx_hash = "0x" + "b" * 64
        mock_service = AsyncMock(spec=ITransactionService)
        mock_service.validate_onchain_transaction.return_value = None  # Service returns None
        app.dependency_overrides[get_transaction_service] = lambda: mock_service

        # Act
        response = test_client.post(
            f"{base_url}/transactions/validate", json={"tx_hash": tx_hash})

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found, invalid, or not relevant" in response.json()[
            "detail"]


@pytest.mark.asyncio
class TestCreateTransactionEndpoint(BaseEndpointTest):
    """Test suite for the POST /create endpoint."""

    async def test_create_transaction_success(self, test_client: TestClient, base_url: str):
        """Scenario: Tests successful acceptance of a new transaction request."""
        # Arrange
        request_body = {
            "from_address": "0x" + "a" * 40,
            "to_address": "0x" + "b" * 40,
            "asset": "ETH",
            "value": 1.5
        }
        mock_pending_tx = TransactionEntity(
            tx_hash="0x_new_tx_hash", asset="ETH", from_address=request_body["from_address"],
            to_address=request_body["to_address"], value=Decimal("1.5"),
            status=TransactionStatus.PENDING, effective_cost=Decimal("0")
        )
        mock_service = AsyncMock(spec=ITransactionService)
        mock_service.create_onchain_transaction.return_value = mock_pending_tx
        app.dependency_overrides[get_transaction_service] = lambda: mock_service

        # Act
        response = test_client.post(
            f"{base_url}/transactions/create", json=request_body)

        # Assert
        assert response.status_code == status.HTTP_202_ACCEPTED

        response_data = response.json()

        assert response_data["status"] == "pending"
        assert response_data["tx_hash"] == "0x_new_tx_hash"

        mock_service.create_onchain_transaction.assert_awaited_once()

    async def test_create_transaction_service_error(self, test_client: TestClient, base_url: str):
        """Scenario: Tests a 400 Bad Request error if the service raises a ValueError."""
        # Arrange
        request_body = {"from_address": "0xUnmanaged",
                        "to_address": "0xTo", "asset": "ETH", "value": 1}
        mock_service = AsyncMock(spec=ITransactionService)
        mock_service.create_onchain_transaction.side_effect = ValueError(
            "Source address not managed")
        app.dependency_overrides[get_transaction_service] = lambda: mock_service

        # Act
        response = test_client.post(
            f"{base_url}/transactions/create", json=request_body)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Source address not managed" in response.json()["detail"]

    async def test_create_transaction_validation_error(self, test_client: TestClient, base_url: str):
        """Scenario: Tests a 422 Unprocessable Entity for invalid input data."""
        # Arrange
        mock_service = AsyncMock(spec=ITransactionService)
        mock_service.create_onchain_transaction.side_effect = ValueError(
            "Invalid value")
        app.dependency_overrides[get_transaction_service] = lambda: mock_service

        request_body = {"from_address": "0xFrom",
                        "to_address": "0xTo", "asset": "ETH", "value": -1}

        # Act
        response = test_client.post(
            f"{base_url}/transactions/create", json=request_body)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
