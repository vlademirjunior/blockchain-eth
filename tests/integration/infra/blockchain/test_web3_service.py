import pytest
import json
from web3 import AsyncWeb3
from eth_account import Account
from src.infra.blockchain.web3_service import Web3BlockchainService

with open("src/infra/blockchain/erc20_abi.json") as f:
    ERC20_ABI = json.load(f)


@pytest.mark.asyncio
class TestWeb3BlockchainService:
    """
    Integration test suite for the Web3BlockchainService using an async in-memory blockchain.
    """

    async def test_is_connected(self, blockchain_service: Web3BlockchainService):
        """Tests the connection to the async test provider."""
        # Act
        connected = await blockchain_service.is_connected()

        # Assert
        assert connected is True

    async def test_get_latest_block_number(self, blockchain_service: Web3BlockchainService):
        """Tests fetching the latest block number."""
        # Act
        block_number = await blockchain_service.get_latest_block_number()

        # Assert
        assert isinstance(block_number, int)
        assert block_number >= 0

    async def test_get_eth_balance(self, blockchain_service: Web3BlockchainService, web3_instance: AsyncWeb3):
        """Tests fetching the balance of a pre-funded test account."""
        # Arrange
        test_address = (await web3_instance.eth.accounts)[0]

        # Act
        balance = await blockchain_service.get_eth_balance(test_address)

        # Assert
        assert isinstance(balance, int)
        assert balance > 0

    async def test_get_eth_balance_invalid_address(self, blockchain_service: Web3BlockchainService):
        """Tests that fetching balance for an invalid address raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid Ethereum address provided."):
            await blockchain_service.get_eth_balance("not-a-valid-address")

    async def test_transaction_lifecycle(self, blockchain_service: Web3BlockchainService, web3_instance: AsyncWeb3):
        """
        Tests the full lifecycle: broadcast, get details, and get receipt.
        """
        # Arrange
        accounts = await web3_instance.eth.accounts
        sender_account = Account.create()
        sender_address = sender_account.address
        receiver_address = accounts[1]

        # Fund the new account
        funding_tx_hash = await web3_instance.eth.send_transaction({
            "from": accounts[0],
            "to": sender_address,
            "value": web3_instance.to_wei(5, "ether")
        })
        await web3_instance.eth.wait_for_transaction_receipt(funding_tx_hash)

        tx_dict = {
            "from": sender_address,
            "to": receiver_address,
            "value": web3_instance.to_wei(1, "ether"),
            "gas": 21000,
            "gasPrice": await web3_instance.eth.gas_price,
            "nonce": await web3_instance.eth.get_transaction_count(sender_address)
        }
        signed_tx = web3_instance.eth.account.sign_transaction(
            tx_dict, sender_account.key)

        # Act
        tx_hash_hex = await blockchain_service.broadcast_transaction(signed_tx.raw_transaction.hex())

        # Assert
        assert tx_hash_hex is not None

        tx_details = await blockchain_service.get_transaction_details(tx_hash_hex)
        assert tx_details is not None
        assert tx_details['from'].lower() == sender_address.lower()

        tx_receipt = await blockchain_service.get_transaction_receipt(tx_hash_hex)

        assert tx_receipt is not None
        assert tx_receipt['status'] == 1  # 1 == Success (TODO: IMPROVE)

    async def test_get_transaction_not_found(self, blockchain_service: Web3BlockchainService):
        """
        Tests that getting receipt and details for a non-existent hash returns None.
        """
        # Arrange
        fake_hash = "0x" + "0" * 64

        # Act
        receipt = await blockchain_service.get_transaction_receipt(fake_hash)
        details = await blockchain_service.get_transaction_details(fake_hash)

        # Assert
        assert details is None
        assert receipt is None

    async def test_get_transaction_count(self, blockchain_service: Web3BlockchainService, web3_instance: AsyncWeb3):
        """Tests fetching the transaction count (nonce) and verifies it increments."""
        # Arrange
        accounts = await web3_instance.eth.accounts
        # Use a fresh account for a predictable nonce
        test_address = accounts[2]

        # Act
        initial_nonce = await blockchain_service.get_transaction_count(test_address)

        # Assert
        assert initial_nonce == 0

        # Act
        # Send a transaction from this address to increment the nonce
        await web3_instance.eth.send_transaction({
            "from": test_address,
            "to": accounts[3],
            "value": web3_instance.to_wei(0.1, "ether")
        })

        # Act
        new_nonce = await blockchain_service.get_transaction_count(test_address)

        # Assert:
        assert new_nonce == 1
