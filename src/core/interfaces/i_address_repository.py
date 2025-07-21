from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import Address


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
