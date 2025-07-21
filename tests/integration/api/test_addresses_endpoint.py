import pytest
from unittest.mock import AsyncMock
from fastapi import status
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.dependencies import get_address_service
from src.core.entities.address import Address as AddressEntity
from src.core.interfaces import IAddressService


@pytest.mark.asyncio
class TestCreateAddressesEndpoint:
    """
    Test suite for the POST /addresses endpoint.
    """

    def setup_method(self):
        """Clears dependency overrides before each test."""
        app.dependency_overrides.clear()

    async def test_create_addresses_success(self, test_client: TestClient, base_url: str):
        """
        Scenario 1: Tests successful creation of new addresses.
        """
        # Arrange
        mock_created_addresses = [
            AddressEntity(public_address="0xAddr1",
                          encrypted_private_key="key1"),
            AddressEntity(public_address="0xAddr2",
                          encrypted_private_key="key2"),
        ]
        mock_service = AsyncMock(spec=IAddressService)
        mock_service.create_new_addresses.return_value = mock_created_addresses
        app.dependency_overrides[get_address_service] = lambda: mock_service

        # Act
        response = test_client.post(
            f"{base_url}/addresses/", json={"count": 2})

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

        response_data = response.json()

        assert "Successfully created 2 new addresses" in response_data["message"]
        assert len(response_data["created_addresses"]) == 2
        assert response_data["created_addresses"][0]["public_address"] == "0xAddr1"

        # Ensure the service was called with the correct count
        mock_service.create_new_addresses.assert_awaited_once_with(2)

    @pytest.mark.parametrize("invalid_count", [0, -5, 101])
    async def test_create_addresses_fails_with_invalid_count(self, test_client: TestClient, base_url: str, invalid_count: int):
        """
        Scenario 2: Tests that the request fails with an invalid count.
        """
        # Act:
        response = test_client.post(
            f"{base_url}/addresses/", json={"count": invalid_count})

        # Assert
        # Pydantic validation should return a 422 error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_create_addresses_handles_service_error(self, test_client: TestClient, base_url: str):
        """
        Scenario 3: Tests that a 500 error is returned if the service raises an unexpected exception.
        """
        # Arrange
        mock_service = AsyncMock(spec=IAddressService)
        mock_service.create_new_addresses.side_effect = Exception(
            "Database write failed")
        app.dependency_overrides[get_address_service] = lambda: mock_service

        # Act
        response = test_client.post(
            f"{base_url}/addresses/", json={"count": 5})

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "An unexpected error occurred" in response.json()["detail"]


@pytest.mark.asyncio
class TestListAddressesEndpoint:
    """
    Test suite for the GET /addresses endpoint.
    """

    def setup_method(self):
        app.dependency_overrides.clear()

    async def test_list_addresses_success(self, test_client: TestClient, base_url: str):
        """
        Scenario 1: Tests successfully listing all managed addresses.
        """
        # Arrange
        mock_address_list = [
            AddressEntity(public_address="0xAddr1",
                          encrypted_private_key="key1"),
            AddressEntity(public_address="0xAddr2",
                          encrypted_private_key="key2"),
        ]
        mock_service = AsyncMock(spec=IAddressService)
        mock_service.get_all_addresses.return_value = mock_address_list
        app.dependency_overrides[get_address_service] = lambda: mock_service

        # Act
        response = test_client.get(f"{base_url}/addresses/")

        # Assert
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert len(response_data["addresses"]) == 2
        assert response_data["addresses"][1]["public_address"] == "0xAddr2"

    async def test_list_addresses_returns_empty_list(self, test_client: TestClient, base_url: str):
        """
        Scenario 2: Tests the case where no addresses are managed yet.
        """
        # Arrange
        mock_service = AsyncMock(spec=IAddressService)
        mock_service.get_all_addresses.return_value = []
        app.dependency_overrides[get_address_service] = lambda: mock_service

        # Act
        response = test_client.get(f"{base_url}/addresses/")

        # Assert
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["addresses"] == []
