from abc import ABC, abstractmethod
from typing import List
from ..entities import Address


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
