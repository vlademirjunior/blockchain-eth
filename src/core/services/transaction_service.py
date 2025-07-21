import asyncio
import os
from decimal import Decimal
from typing import List, Optional
from eth_account import Account
from web3 import Web3
from web3.exceptions import TimeExhausted
from ..entities import Transaction
from ..enums import TransactionStatus
from ..interfaces import (
    ITransactionRepository,
    IAddressRepository,
    IBlockchainService,
    IEncryptionService,
    INonceManager,
    ITransactionService,
)


class TransactionService(ITransactionService):
    def __init__(
        self,
        transaction_repo: ITransactionRepository,
        address_repo: IAddressRepository,
        blockchain_service: IBlockchainService,
        encryption_service: IEncryptionService,
        nonce_manager: INonceManager
    ):
        self.transaction_repo = transaction_repo
        self.address_repo = address_repo
        self.blockchain_service = blockchain_service
        self.encryption_service = encryption_service
        self.nonce_manager = nonce_manager
        self.min_confirmations = int(os.getenv("MIN_CONFIRMATIONS", "12"))
        self.chain_id = int(os.getenv("CHAIN_ID", "11155111"))
        self.priority_fee_gwei = int(
            os.getenv("DEFAULT_PRIORITY_FEE_GWEI", "2"))
        self.TRANSACTION_CONFIRMATION_TIMEOUT_SECONDS = int(
            os.getenv("TRANSACTION_CONFIRMATION_TIMEOUT_SECONDS", "300"))

    async def _extract_transfer_details(self, tx_hash: str, tx_details: dict) -> Optional[dict]:
        # --- Logic to handle both ETH and ERC-20 Transfers ---
        asset = "ETH"
        value_in_wei = tx_details['value']
        to_address = Web3.to_checksum_address(tx_details['to'])

        # Check if is a potential contract interaction
        if tx_details.get('input') and tx_details['input'] != '0x':
            decoded_input = await self.blockchain_service.decode_contract_transaction(
                tx_hash, self.blockchain_service.erc20_abi
            )
            # Check if is a standard 'transfer' function call
            if decoded_input and decoded_input.get('function') == 'transfer':
                params = decoded_input.get('params', {})
                recipient = params.get('_to')
                amount = params.get('_value')

                if recipient and amount is not None:
                    # Is a valid ERC-20 transfer, then update my variables
                    asset = "ERC-20_TOKEN"  # In a real app, I need look up the symbol
                    to_address = Web3.to_checksum_address(recipient)
                    value_in_wei = amount

        return {
            "asset": asset,
            "to_address": to_address,
            "value_in_wei": value_in_wei,
            "from_address": Web3.to_checksum_address(tx_details['from'])
        }

    async def validate_onchain_transaction(self, tx_hash: str) -> Optional[Transaction]:
        tx_details = await self.blockchain_service.get_transaction_details(tx_hash)
        if not tx_details:
            return None

        receipt = await self.blockchain_service.get_transaction_receipt(tx_hash)
        if not receipt or receipt.get('status') == 0:
            return None  # Transaction failed or was not confirmed

        # Check for security confirmations
        latest_block = await self.blockchain_service.get_latest_block_number()
        confirmations = (
            latest_block - receipt.get('blockNumber', latest_block)) + 1
        if confirmations < self.min_confirmations:
            return None  # Not secure enough yet

        transfer_info = await self._extract_transfer_details(tx_hash, tx_details)
        if not transfer_info:
            return None

        # Check if the FINAL destination is one managed addresses
        managed_address = await self.address_repo.find_by_public_address(transfer_info["to_address"])
        if not managed_address:
            return None  # Not a transaction for my API

        # --- Upsert Logic ---
        effective_cost = Web3.from_wei(
            receipt.get('gasUsed', 0) *
            receipt.get('effectiveGasPrice', 0), 'ether'
        )

        existing_tx = await self.transaction_repo.find_by_hash(tx_hash)
        if existing_tx:
            existing_tx.status = TransactionStatus.VALIDATED
            existing_tx.effective_cost = effective_cost
            return await self.transaction_repo.update(existing_tx)

        tx_entity = Transaction(
            tx_hash=tx_hash,
            asset=transfer_info["asset"],
            from_address=transfer_info["from_address"],
            to_address=transfer_info["to_address"],
            value=Web3.from_wei(transfer_info["value_in_wei"], 'ether'),
            status=TransactionStatus.VALIDATED,
            effective_cost=effective_cost
        )
        return await self.transaction_repo.create(tx_entity)

    async def _calculate_fees(self) -> dict:
        # Calculate fees (EIP-1559)
        base_fee = await self.blockchain_service.get_base_fee()
        priority_fee = Web3.to_wei(self.priority_fee_gwei, 'gwei')
        max_fee_per_gas = (2 * base_fee) + priority_fee
        return {
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": priority_fee
        }

    def _sign_transaction(self, tx_dict: dict, private_key_bytes: bytes) -> str:
        # Sign the transaction
        signed_tx = Account.sign_transaction(tx_dict, private_key_bytes)
        # Clear the key from memory (good practice)
        del private_key_bytes
        return signed_tx.raw_transaction.hex()

    async def _create_and_store_transaction(
        self, tx_hash: str, asset: str, from_address: str, to_address: str, value: Decimal
    ) -> Transaction:
        tx_entity = Transaction(
            tx_hash=tx_hash,
            asset=asset,
            from_address=from_address,
            to_address=to_address,
            value=value,
            status=TransactionStatus.PENDING,
            effective_cost=Decimal(0)  # Will be updated after confirmation
        )
        await self.transaction_repo.create(tx_entity)
        return tx_entity

    async def create_onchain_transaction(
        self,
        from_address: str,
        to_address: str,
        asset: str,
        value: Decimal
    ) -> Transaction:
        # Get the nonce from my secure manager
        nonce = await self.nonce_manager.get_next_nonce(from_address)

        # Get the private key
        sender_address_entity = await self.address_repo.find_by_public_address(from_address)
        if not sender_address_entity:
            raise ValueError("Source address not managed by this service.")

        private_key_bytes = self.encryption_service.decrypt(
            sender_address_entity.encrypted_private_key.encode()
        )

        fees = await self._calculate_fees()

        tx_dict = {
            "from": from_address,
            "to": to_address,
            "value": Web3.to_wei(value, 'ether'),
            "nonce": nonce,
            "maxFeePerGas": fees["maxFeePerGas"],
            "maxPriorityFeePerGas": fees["maxPriorityFeePerGas"],
            "chainId": self.chain_id,
        }

        # Estimate gas
        gas_estimate = await self.blockchain_service.estimate_gas(tx_dict)
        tx_dict["gas"] = gas_estimate

        signed_tx_hex = self._sign_transaction(tx_dict, private_key_bytes)

        # Broadcast to the network
        tx_hash = await self.blockchain_service.broadcast_transaction(signed_tx_hex)

        return await self._create_and_store_transaction(
            tx_hash, asset, from_address, to_address, value
        )

    async def get_all_transaction_history(self) -> List[Transaction]:
        db_transactions = await self.transaction_repo.get_all()
        return [Transaction.model_validate(tx) for tx in db_transactions]

    async def get_transaction_history_for_address(self, address: str) -> List[Transaction]:
        db_transactions = await self.transaction_repo.get_history(address=address)
        return [Transaction.model_validate(tx) for tx in db_transactions]

    async def _update_transaction_status(self, tx_hash: str, receipt: Optional[dict]):
        # Find the original transaction record
        tx_entity = await self.transaction_repo.find_by_hash(tx_hash)
        if not tx_entity:
            print(
                f"BACKGROUND TASK ERROR: Could not find tx_hash {tx_hash} in DB to update.")
            return

        # Update status and cost based on the receipt
        if receipt and receipt.get('status') == 1:
            tx_entity.status = TransactionStatus.CONFIRMED
            tx_entity.effective_cost = Web3.from_wei(
                receipt.get('gasUsed', 0) *
                receipt.get('effectiveGasPrice', 0), 'ether'
            )
            print(
                f"BACKGROUND TASK: Transaction {tx_hash} confirmed successfully.")
        else:
            tx_entity.status = TransactionStatus.FAILED
            print(
                f"BACKGROUND TASK: Transaction {tx_hash} failed or receipt not found.")

        # Save the final state to the database
        await self.transaction_repo.update(tx_entity)

    async def wait_for_confirmation(self, tx_hash: str):
        """
        This method is designed to be run as a background task.
        It waits for the transaction receipt and updates the DB record.
        """
        print(f"BACKGROUND TASK: Started monitoring tx_hash: {tx_hash}")
        try:
            # Wait for the transaction receipt from the blockchain
            receipt = await self.blockchain_service.wait_for_transaction_receipt(
                tx_hash, timeout=self.TRANSACTION_CONFIRMATION_TIMEOUT_SECONDS
            )
            await self._update_transaction_status(tx_hash, receipt)

        except (TimeExhausted, asyncio.TimeoutError):
            print(
                f"BACKGROUND TASK TIMEOUT: Transaction {tx_hash} was not confirmed within the timeout period.")
            # Optionally, you could set the status to a special "timed_out" state here.
        except Exception as e:
            print(
                f"BACKGROUND TASK ERROR: An unexpected error occurred while monitoring {tx_hash}: {e}")
