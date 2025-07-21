import pytest
from decimal import Decimal
from web3.exceptions import TimeExhausted
from src.core.services import TransactionService
from src.core.entities.transaction import Transaction as TransactionEntity
from src.core.enums import TransactionStatus
from src.core.interfaces import ITransactionRepository, IBlockchainService
from src.core.constants import TRANSACTION_CONFIRMATION_TIMEOUT_SECONDS


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
            tx_hash, timeout=TRANSACTION_CONFIRMATION_TIMEOUT_SECONDS)
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
