from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


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
