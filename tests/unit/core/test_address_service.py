import pytest
from unittest.mock import MagicMock, AsyncMock, call
from src.core.services import AddressService
from src.core.entities import Address
from src.core.interfaces import IAddressRepository, IEncryptionService


@pytest.fixture
def mock_address_repo() -> IAddressRepository:
    return AsyncMock(spec=IAddressRepository)


@pytest.fixture
def mock_encryption_service() -> IEncryptionService:
    # Encryption is a synchronous CPU-bound operation, so I need to use MagicMock
    return MagicMock(spec=IEncryptionService)


@pytest.fixture
def address_service(
    mock_address_repo: IAddressRepository,
    mock_encryption_service: IEncryptionService
) -> AddressService:
    return AddressService(
        address_repo=mock_address_repo,
        encryption_service=mock_encryption_service
    )


@pytest.mark.asyncio
class TestAddressService:
    """
    Unit test suite for the AddressService.
    """

    async def test_create_new_addresses_success(
        self,
        address_service: AddressService,
        mock_address_repo: IAddressRepository,
        mock_encryption_service: IEncryptionService
    ):
        """
        Tests the successful creation of multiple new addresses.
        """
        # Arrange
        count = 3
        mock_encryption_service.encrypt.return_value = b"encrypted_key"

        # Act
        created_addresses = await address_service.create_new_addresses(count)

        # Assert
        assert len(created_addresses) == count
        assert isinstance(created_addresses[0], Address)

        # Verify that the encryption service was called for each new key
        assert mock_encryption_service.encrypt.call_count == count

        # Verify that the repository was called once to save all new addresses
        mock_address_repo.create_many.assert_awaited_once()

        # Check the content of the call to the repository
        saved_addresses_arg = mock_address_repo.create_many.await_args[0][0]
        assert len(saved_addresses_arg) == count
        assert saved_addresses_arg[0].encrypted_private_key == "encrypted_key"

    @pytest.mark.parametrize("invalid_count", [0, -1, 101])
    async def test_create_new_addresses_fails_with_invalid_count(
        self,
        address_service: AddressService,
        invalid_count: int
    ):
        """
        Tests that address creation fails if the count is outside the valid range (1-100).
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Number of addresses to create must be between 1 and 100."):
            await address_service.create_new_addresses(invalid_count)

    async def test_get_all_addresses_success(
        self,
        address_service: AddressService,
        mock_address_repo: IAddressRepository
    ):
        """
        Tests that all addresses are correctly retrieved from the repository.
        """
        # Arrange
        mock_data = [
            Address(public_address="0xAddr1",
                    encrypted_private_key="key1"),
            Address(public_address="0xAddr2",
                    encrypted_private_key="key2")
        ]
        mock_address_repo.get_all.return_value = mock_data

        # Act
        result = await address_service.get_all_addresses()

        # Assert
        assert len(result) == 2
        assert result[0].public_address == "0xAddr1"
        mock_address_repo.get_all.assert_awaited_once()
