import pytest
from decimal import Decimal
from eth_account import Account
from src.core.services import TransactionService
from src.core.entities import Transaction as TransactionEntity, Address as AddressEntity
from src.core.enums import TransactionStatus
from src.core.interfaces import (
    ITransactionRepository,
    IAddressRepository,
    IBlockchainService,
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
