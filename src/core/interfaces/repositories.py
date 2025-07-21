from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import Address, Transaction


class ITransactionRepository(ABC):
    @abstractmethod
    async def create(self, transaction) -> None:
        pass

    @abstractmethod
    async def update(self, transaction: Transaction) -> None:
        pass

    @abstractmethod
    async def find_by_hash(self, tx_hash: str):
        pass

    @abstractmethod
    async def get_history(self, address: str) -> List:
        pass

    @abstractmethod
    async def get_all(self) -> List[Address]:
        pass


class IAddressRepository(ABC):
    @abstractmethod
    async def create_many(self, addresses: List[Address]) -> None:
        pass

    @abstractmethod
    async def get_all(self) -> List[Address]:
        pass

    @abstractmethod
    async def find_by_public_address(self, public_address: str) -> Optional[Address]:
        """Finds a single address by its public key."""
        pass
