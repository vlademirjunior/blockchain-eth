import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from web3.exceptions import TimeExhausted
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


@pytest.mark.asyncio
class TestValidateOnchainTransaction:

    @pytest.fixture
    def common_mocks(self, mock_address_repo: IAddressRepository, mock_blockchain_service: IBlockchainService):
        """Fixture to set up common mock return values for validation tests."""
        tx_hash = "0x" + "a" * 64
        managed_address = Account.create().address
        sender_address = "0x" + "c" * 40

        mock_blockchain_service.get_transaction_details.return_value = {
            'hash': tx_hash, 'from': sender_address, 'to': managed_address, 'value': 10**18, 'input': '0x'
        }
        mock_blockchain_service.get_transaction_receipt.return_value = {
            'status': 1, 'blockNumber': 100, 'gasUsed': 21000, 'effectiveGasPrice': 10**9
        }
        mock_blockchain_service.get_latest_block_number.return_value = 112
        mock_address_repo.find_by_public_address.return_value = AddressEntity(
            public_address=managed_address, encrypted_private_key="key")

        return tx_hash, managed_address

    async def test_validation_creates_new_record_for_incoming_tx(self, transaction_service: TransactionService, common_mocks, mock_transaction_repo: ITransactionRepository):
        """
        Tests the success case where an incoming transaction (not previously in our DB)
        is validated and a NEW record is created.
        """
        # Arrange
        tx_hash, _ = common_mocks
        mock_transaction_repo.find_by_hash.return_value = None

        # Act
        result = await transaction_service.validate_onchain_transaction(tx_hash)

        # Assert
        assert result is not None

        # Verify that the 'create' method was called, not 'update'
        mock_transaction_repo.create.assert_awaited_once()
        mock_transaction_repo.update.assert_not_awaited()

    async def test_validation_updates_existing_record_for_outgoing_tx(self, transaction_service: TransactionService, common_mocks, mock_transaction_repo: ITransactionRepository):
        """
        Tests the success case where a transaction we created (status=PENDING)
        is validated and the EXISTING record is updated.
        """
        # Arrange
        tx_hash, managed_address = common_mocks
        # Simulate that the transaction already exists in our DB with a PENDING status
        existing_pending_tx = TransactionEntity(
            tx_hash=tx_hash, asset="ETH", from_address="0xFrom", to_address=managed_address,
            value=Decimal("1.0"), status=TransactionStatus.PENDING, effective_cost=Decimal("0")
        )
        mock_transaction_repo.find_by_hash.return_value = existing_pending_tx

        # Act
        result = await transaction_service.validate_onchain_transaction(tx_hash)

        # Assert
        assert result is not None

        # Verify that the 'update' method was called, not 'create'
        mock_transaction_repo.update.assert_awaited_once()
        mock_transaction_repo.create.assert_not_awaited()

        # Check that the entity passed to update has the correct new status
        updated_entity_arg = mock_transaction_repo.update.await_args[0][0]

        assert updated_entity_arg.status == TransactionStatus.VALIDATED
        assert updated_entity_arg.effective_cost > 0

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


@pytest.mark.asyncio
class TestWaitForConfirmation:
    """
    Test suite for the wait_for_confirmation background task method.
    """

    async def test_wait_for_confirmation_success(self, transaction_service: TransactionService, mock_blockchain_service: IBlockchainService, mock_transaction_repo: ITransactionRepository):
        """
        Scenario: Tests that the transaction status is updated to CONFIRMED
        when a successful receipt is returned.
        """
        # Arrange
        tx_hash = "0x_confirmed_tx"

        # Mock the blockchain service to return a successful receipt
        mock_receipt = {'status': 1, 'gasUsed': 50000,
                        'effectiveGasPrice': 20 * 10**9}
        mock_blockchain_service.wait_for_transaction_receipt.return_value = mock_receipt

        # Mock the repository to return a pending transaction that needs updating
        pending_tx = TransactionEntity(
            tx_hash=tx_hash, asset="ETH", from_address="0xFrom", to_address="0xTo",
            value=Decimal("1"), status=TransactionStatus.PENDING, effective_cost=Decimal("0")
        )
        mock_transaction_repo.find_by_hash.return_value = pending_tx

        # Act
        await transaction_service.wait_for_confirmation(tx_hash)

        # Assert
        mock_blockchain_service.wait_for_transaction_receipt.assert_awaited_once_with(
            tx_hash, timeout=300)
        mock_transaction_repo.find_by_hash.assert_awaited_once_with(tx_hash)

        # Verify that the update method was called with the correct, updated entity
        mock_transaction_repo.update.assert_awaited_once()
        updated_entity_arg = mock_transaction_repo.update.await_args[0][0]
        assert updated_entity_arg.status == TransactionStatus.CONFIRMED
        assert updated_entity_arg.effective_cost > 0

    async def test_wait_for_confirmation_failed_tx(self, transaction_service: TransactionService, mock_blockchain_service: IBlockchainService, mock_transaction_repo: ITransactionRepository):
        """
        Scenario: Tests that the transaction status is updated to FAILED
        when a failed receipt (status 0) is returned.
        """
        # Arrange
        tx_hash = "0x_failed_tx"
        mock_receipt = {'status': 0}  # Failed transaction
        mock_blockchain_service.wait_for_transaction_receipt.return_value = mock_receipt

        pending_tx = TransactionEntity(
            tx_hash=tx_hash, asset="ETH", from_address="0xFrom", to_address="0xTo",
            value=Decimal("1"), status=TransactionStatus.PENDING, effective_cost=Decimal("0")
        )
        mock_transaction_repo.find_by_hash.return_value = pending_tx

        # Act
        await transaction_service.wait_for_confirmation(tx_hash)

        # Assert
        mock_transaction_repo.update.assert_awaited_once()
        updated_entity_arg = mock_transaction_repo.update.await_args[0][0]
        assert updated_entity_arg.status == TransactionStatus.FAILED

    async def test_wait_for_confirmation_timeout(self, transaction_service: TransactionService, mock_blockchain_service: IBlockchainService, mock_transaction_repo: ITransactionRepository):
        """
        Scenario: Tests that the transaction status is NOT updated
        if the wait for receipt times out.
        """
        # Arrange
        tx_hash = "0x_timeout_tx"
        # Configure the mock to simulate a timeout
        mock_blockchain_service.wait_for_transaction_receipt.side_effect = TimeExhausted(
            "Timeout")

        # Act
        await transaction_service.wait_for_confirmation(tx_hash)

        # Assert
        # The most important assertion is that the update method was NEVER called
        mock_transaction_repo.update.assert_not_awaited()
