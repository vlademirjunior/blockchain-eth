from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, List, Optional
from ..entities import Address, Transaction


class IEncryptionService(ABC):
    """
    Interface for a service that handles data encryption and decryption keys
    It is synchronized process because use CPU operations (CPU-bound)
    """
    @abstractmethod
    def encrypt(self, data: bytes) -> bytes:
        pass

    @abstractmethod
    def decrypt(self, encrypted_data: bytes) -> bytes:
        pass


class IBlockchainService(ABC):
    """
    Interface for a service that handles all interactions with the Ethereum blockchain.
    """
    erc20_abi: List[Dict[str, Any]]

    @abstractmethod
    async def is_connected(self) -> bool:
        """Checks if the connection to the node is active."""
        pass

    @abstractmethod
    async def get_transaction_details(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_latest_block_number(self) -> int:
        pass

    @abstractmethod
    async def get_base_fee(self) -> int:
        """Gets the base fee for the latest block in Wei format."""
        pass

    @abstractmethod
    async def estimate_gas(self, transaction: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    async def broadcast_transaction(self, signed_tx_hex: str) -> str:
        """Broadcasts a signed transaction to the network."""
        pass

    @abstractmethod
    async def get_eth_balance(self, address: str) -> int:
        """Gets the ETH balance of an address in Wei format."""
        pass

    @abstractmethod
    async def decode_contract_transaction(self, tx_hash: str, contract_abi: List[Dict]) -> Optional[Dict[str, Any]]:
        """Decodes the input data of a contract interaction."""
        pass

    @abstractmethod
    async def get_transaction_count(self, address: str) -> int:
        """Gets the transaction count (nonce) for a given address."""
        pass

    @abstractmethod
    async def wait_for_transaction_receipt(self, tx_hash: str, timeout: int) -> Optional[Dict[str, Any]]:
        """
        Waits for a transaction receipt to be available and returns it.
        Returns None if the timeout is reached.
        """
        pass


class INonceManager(ABC):
    """
    Interface for a service that manages nonces for sending addresses
    in a thread-safe/async-safe manner.
    """

    @abstractmethod
    async def initialize_nonces(self) -> None:
        """
        Initializes the manager by fetching the current nonce for all
        managed sending addresses from the blockchain.
        Important when restart the API.
        """
        pass

    @abstractmethod
    async def get_next_nonce(self, address: str) -> int:
        """
        Atomically retrieves the current nonce for an address and increments
        the internal counter for the next call.
        """
        pass


class ITransactionService(ABC):
    """
    Interface for the service that orchestrates all transaction-related business logic.
    """

    @abstractmethod
    async def validate_onchain_transaction(self, tx_hash: str) -> Optional[Transaction]:
        """
        Validates an on-chain transaction and, if valid, update it.
        Returns the transaction entity if valid, otherwise None.
        """
        pass

    @abstractmethod
    async def create_onchain_transaction(
        self,
        from_address: str,
        to_address: str,
        asset: str,
        value: Decimal
    ) -> Transaction:
        """
        Creates, signs, and broadcasts a new transaction.
        Returns the pending transaction entity.
        """
        pass

    @abstractmethod
    # Changed method name
    async def get_all_transaction_history(self) -> List[Transaction]:
        """
        Retrieves the full history of all managed transactions.
        """
        pass

    @abstractmethod
    async def get_transaction_history_for_address(self, address: str) -> List[Transaction]:
        """
        Retrierives the history of managed transactions filtered by a specific Ethereum address.
        """
        pass

    @abstractmethod
    async def wait_for_confirmation(self, tx_hash: str) -> None:
        """
        Waits for a transaction to be confirmed on the blockchain and updates its
        status and effective cost in the database.
        """
        pass


class IAddressService(ABC):
    """
    Interface for the service that orchestrates address-related business logic.
    """

    @abstractmethod
    async def create_new_addresses(self, count: int) -> List[Address]:
        """
        Generates a specified number of new Ethereum addresses,
        encrypts their private keys, and persists them.
        Returns the list of created address entities.
        """
        pass

    @abstractmethod
    async def get_all_addresses(self) -> List[Address]:
        """
        Retrieves all managed addresses.
        """
        pass
