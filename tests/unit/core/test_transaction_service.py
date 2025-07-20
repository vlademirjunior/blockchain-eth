import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from eth_account import Account
from src.core.services import TransactionService
from src.core.entities import Transaction as TransactionEntity, Address as AddressEntity
from src.core.enums import TransactionStatus
from src.core.interfaces import (
    ITransactionRepository,
    IAddressRepository,
    IBlockchainService,
    IEncryptionService,
    INonceManager
)

# --- Mock Fixtures ---
# TODO: Separate in files


@pytest.fixture
def mock_transaction_repo() -> ITransactionRepository:
    """Provides a mock for ITransactionRepository."""
    return AsyncMock(spec=ITransactionRepository)


@pytest.fixture
def mock_address_repo() -> IAddressRepository:
    """Provides a mock for IAddressRepository."""
    return AsyncMock(spec=IAddressRepository)


@pytest.fixture
def mock_blockchain_service() -> IBlockchainService:
    mock = AsyncMock(spec=IBlockchainService)
    mock.erc20_abi = []
    return mock


@pytest.fixture
def mock_encryption_service() -> IEncryptionService:
    """Provides a mock for IEncryptionService."""
    return MagicMock(spec=IEncryptionService)


@pytest.fixture
def mock_nonce_manager() -> INonceManager:
    """Provides a mock for INonceManager."""
    return AsyncMock(spec=INonceManager)


@pytest.fixture
def transaction_service(
    mock_transaction_repo,
    mock_address_repo,
    mock_blockchain_service,
    mock_encryption_service,
    mock_nonce_manager
) -> TransactionService:
    """Provides a TransactionService instance with all dependencies mocked."""
    return TransactionService(
        transaction_repo=mock_transaction_repo,
        address_repo=mock_address_repo,
        blockchain_service=mock_blockchain_service,
        encryption_service=mock_encryption_service,
        nonce_manager=mock_nonce_manager
    )

# --- Tests for validate_onchain_transaction ---


@pytest.mark.asyncio
class TestValidateOnchainTransaction:

    async def test_validation_success_for_eth_transfer(self, transaction_service: TransactionService, mock_address_repo: IAddressRepository, mock_blockchain_service: IBlockchainService, mock_transaction_repo: ITransactionRepository):
        """
        Tests the success case for validating an ETH transfer.
        """
        # Arrange
        tx_hash = "0x" + "a" * 64
        managed_address = Account.create().address  # Use a valid checksum address
        sender_address = "0x" + "c" * 40

        mock_blockchain_service.get_transaction_details.return_value = {
            'hash': tx_hash, 'from': sender_address, 'to': managed_address, 'value': 10**18, 'input': '0x'
        }
        mock_blockchain_service.get_transaction_receipt.return_value = {
            'status': 1, 'blockNumber': 100, 'gasUsed': 21000, 'effectiveGasPrice': 10**9
        }
        # Ensures 13 confirmations
        mock_blockchain_service.get_latest_block_number.return_value = 112
        mock_address_repo.find_by_public_address.return_value = AddressEntity(
            public_address=managed_address, encrypted_private_key="key")

        # Act
        result = await transaction_service.validate_onchain_transaction(tx_hash)

        # Assert
        assert result is not None
        assert isinstance(result, TransactionEntity)
        assert result.asset == "ETH"
        # Case-insensitive comparison for checksum addresses
        assert result.to_address.lower() == managed_address.lower()
        assert result.value == Decimal("1.0")
        mock_transaction_repo.create.assert_awaited_once()

    async def test_validation_fails_if_not_enough_confirmations(self, transaction_service: TransactionService, mock_blockchain_service: IBlockchainService):
        """
        Tests if validation fails if the transaction does not have enough confirmations.
        """
        # Arrange
        tx_hash = "0x_unconfirmed_tx"
        mock_blockchain_service.get_transaction_details.return_value = {
            'to': '0x' + 'd' * 40, 'value': 1}
        mock_blockchain_service.get_transaction_receipt.return_value = {
            'status': 1, 'blockNumber': 100}
        mock_blockchain_service.get_latest_block_number.return_value = 105  # Only 6 confirmations

        # Act
        result = await transaction_service.validate_onchain_transaction(tx_hash)

        # Assert
        assert result is None

    async def test_validation_fails_if_destination_not_managed(self, transaction_service: TransactionService, mock_address_repo: IAddressRepository, mock_blockchain_service: IBlockchainService):
        """
        Tests if validation fails if the destination address is not managed by the service.
        """
        # Arrange
        tx_hash = "0x_other_tx"
        # Provide a complete mock dictionary to avoid KeyError
        mock_blockchain_service.get_transaction_details.return_value = {
            'to': '0x' + 'e' * 40, 'value': 1, 'input': '0x', 'from': '0x' + 'f' * 40
        }
        mock_blockchain_service.get_transaction_receipt.return_value = {
            'status': 1, 'blockNumber': 100, 'gasUsed': 21000, 'effectiveGasPrice': 10**9}
        mock_blockchain_service.get_latest_block_number.return_value = 120
        mock_address_repo.find_by_public_address.return_value = None  # Address not found

        # Act
        result = await transaction_service.validate_onchain_transaction(tx_hash)

        # Assert
        assert result is None

# --- Tests for create_onchain_transaction ---


@pytest.mark.asyncio
class TestCreateOnchainTransaction:

    async def test_creation_success(self, transaction_service: TransactionService, mock_address_repo: IAddressRepository, mock_nonce_manager: INonceManager, mock_encryption_service: IEncryptionService, mock_blockchain_service: IBlockchainService, mock_transaction_repo: ITransactionRepository):
        """
        Tests the success case for creating, signing, and broadcasting a transaction.
        """
        # Arrange
        sender_account = Account.create()
        receiver_account = Account.create()
        from_addr = sender_account.address
        to_addr = receiver_account.address
        value = Decimal("0.5")

        mock_nonce_manager.get_next_nonce.return_value = 10
        mock_address_repo.find_by_public_address.return_value = AddressEntity(
            public_address=from_addr, encrypted_private_key="encrypted_key")
        mock_encryption_service.decrypt.return_value = sender_account.key
        mock_blockchain_service.get_base_fee.return_value = 20 * 10**9
        mock_blockchain_service.estimate_gas.return_value = 21000
        mock_blockchain_service.broadcast_transaction.return_value = "0x_new_tx_hash"

        # Act
        result = await transaction_service.create_onchain_transaction(from_addr, to_addr, "ETH", value)

        # Assert
        assert result is not None
        assert result.tx_hash == "0x_new_tx_hash"
        assert result.status == TransactionStatus.PENDING

        # Verify that dependencies were called correctly
        mock_nonce_manager.get_next_nonce.assert_awaited_with(from_addr)
        mock_encryption_service.decrypt.assert_called_once()
        mock_blockchain_service.broadcast_transaction.assert_awaited_once()
        mock_transaction_repo.create.assert_awaited_once()

    async def test_creation_fails_if_from_address_not_managed(self, transaction_service: TransactionService, mock_address_repo: IAddressRepository):
        """
        Tests if creation fails if the source address is not managed by the service.
        """
        # Arrange
        mock_address_repo.find_by_public_address.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Source address not managed by this service."):
            await transaction_service.create_onchain_transaction("0x" + "a" * 40, "0x" + "b" * 40, "ETH", Decimal("1"))
