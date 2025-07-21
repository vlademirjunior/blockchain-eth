import pytest
from decimal import Decimal
from eth_account import Account
from src.core.services import TransactionService
from src.core.entities import Address as AddressEntity
from src.core.enums import TransactionStatus
from src.core.interfaces import (
    ITransactionRepository,
    IAddressRepository,
    IBlockchainService,
    IEncryptionService,
    INonceManager
)


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
