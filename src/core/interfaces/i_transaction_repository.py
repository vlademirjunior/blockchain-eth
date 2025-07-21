from abc import ABC, abstractmethod
from typing import List
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
