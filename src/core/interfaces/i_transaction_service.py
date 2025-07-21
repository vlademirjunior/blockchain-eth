from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional
from ..entities import Transaction


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
