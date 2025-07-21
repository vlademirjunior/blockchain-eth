import pytest
import asyncio
from unittest.mock import AsyncMock
from src.infra.blockchain.nonce_manager import NonceManager
from src.core.entities import Address as AddressEntity
from src.core.interfaces import IAddressRepository, IBlockchainService


@pytest.fixture
def mock_address_repo() -> IAddressRepository:
    return AsyncMock(spec=IAddressRepository)


@pytest.fixture
def mock_blockchain_service() -> IBlockchainService:
    return AsyncMock(spec=IBlockchainService)


@pytest.mark.asyncio
class TestNonceManager:
    """
    Unit test suite for the in-memory NonceManager.
    """

    async def test_initialize_nonces_successfully(
        self, mock_address_repo: IAddressRepository, mock_blockchain_service: IBlockchainService
    ):
        """
        Tests that the manager correctly fetches and stores initial nonces on startup.
        """
        # Arrange
        address1 = AddressEntity(
            public_address="0xAddr1", encrypted_private_key="key1")
        address2 = AddressEntity(
            public_address="0xAddr2", encrypted_private_key="key2")

        INITIAL_NONCE_ADDR1 = 10
        INITIAL_NONCE_ADDR2 = 42

        mock_address_repo.get_all.return_value = [address1, address2]
        mock_blockchain_service.get_transaction_count.side_effect = [
            INITIAL_NONCE_ADDR1, INITIAL_NONCE_ADDR2
        ]

        manager = NonceManager(mock_address_repo, mock_blockchain_service)

        # Act
        await manager.initialize_nonces()

        # Assert
        assert manager._nonces["0xAddr1"] == INITIAL_NONCE_ADDR1
        assert manager._nonces["0xAddr2"] == INITIAL_NONCE_ADDR2
        assert mock_blockchain_service.get_transaction_count.call_count == 2

    async def test_get_next_nonce_returns_sequential_values(
        self, mock_address_repo: IAddressRepository, mock_blockchain_service: IBlockchainService
    ):
        """
        Tests that sequential calls for the same address return incrementing nonces.
        """
        # Arrange
        address1 = AddressEntity(
            public_address="0xAddr1", encrypted_private_key="key1")
        mock_address_repo.get_all.return_value = [address1]
        mock_blockchain_service.get_transaction_count.return_value = 5

        manager = NonceManager(mock_address_repo, mock_blockchain_service)

        await manager.initialize_nonces()

        # Act
        nonce1 = await manager.get_next_nonce("0xAddr1")
        nonce2 = await manager.get_next_nonce("0xAddr1")
        nonce3 = await manager.get_next_nonce("0xAddr1")

        # Assert
        assert nonce1 == 5
        assert nonce2 == 6
        assert nonce3 == 7

        # Internal counter should be updated
        assert manager._nonces["0xAddr1"] == 8

    async def test_get_next_nonce_is_async_safe(
        self, mock_address_repo: IAddressRepository, mock_blockchain_service: IBlockchainService
    ):
        """
        Tests that concurrent calls to get_next_nonce return unique, sequential nonces.
        This is the most critical test for this class.
        """
        # Arrange
        address1 = AddressEntity(
            public_address="0xAddr1", encrypted_private_key="key1")
        mock_address_repo.get_all.return_value = [address1]
        mock_blockchain_service.get_transaction_count.return_value = 100

        manager = NonceManager(mock_address_repo, mock_blockchain_service)

        await manager.initialize_nonces()

        # Act
        # Create 50 concurrent tasks that all try to get the next nonce
        concurrent_tasks = [manager.get_next_nonce(
            "0xAddr1") for _ in range(50)]
        results = await asyncio.gather(*concurrent_tasks)

        # Assert
        # The results should be a list of unique numbers from 100 to 149
        assert len(results) == 50
        assert len(set(results)) == 50  # All returned nonces must be unique

        # Check that the sequence is correct
        expected_nonces = set(range(100, 150))

        assert set(results) == expected_nonces

        # Check that the internal counter was correctly updated
        assert manager._nonces["0xAddr1"] == 150

    async def test_get_next_nonce_raises_error_for_unmanaged_address(
        self, mock_address_repo: IAddressRepository, mock_blockchain_service: IBlockchainService
    ):
        """
        Tests that a ValueError is raised if a nonce is requested for an address
        that was not initialized.
        """
        # Arrange
        mock_address_repo.get_all.return_value = []  # No addresses initialized
        manager = NonceManager(mock_address_repo, mock_blockchain_service)

        await manager.initialize_nonces()

        # Act & Assert
        with pytest.raises(ValueError, match="Nonce for address 0xUnknownAddress is not managed"):
            await manager.get_next_nonce("0xUnknownAddress")
