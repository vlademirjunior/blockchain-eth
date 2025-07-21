from abc import ABC, abstractmethod


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
