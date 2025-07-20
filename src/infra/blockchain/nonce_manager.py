import asyncio
from typing import Dict
from src.core.interfaces import INonceManager, IAddressRepository, IBlockchainService


class NonceManager(INonceManager):
    """
    In-memory, async-safe implementation of the nonce manager.

    NOTE: This implementation is suitable for a single-instance application.
    In a distributed environment (e.g., multiple pods on K8S), this state would need
    to be managed in a centralized datastore like Redis.
    """

    def __init__(self, address_repo: IAddressRepository, blockchain_service: IBlockchainService):
        self._address_repo = address_repo
        self._blockchain_service = blockchain_service
        self._nonces: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def initialize_nonces(self) -> None:
        addresses_to_manage = await self._address_repo.get_all()

        async with self._lock:
            for address_entity in addresses_to_manage:
                address = address_entity.public_address
                # Fetch the current transaction count from the blockchain
                tx_count = await self._blockchain_service.get_transaction_count(address)
                self._nonces[address] = tx_count
                # Added for logging
                print(f"Initialized nonce for {address}: {tx_count}")

    async def get_next_nonce(self, address: str) -> int:
        """
        Atomically gets the current nonce for an address and increments it for the next use.
        """
        async with self._lock:
            current_nonce = self._nonces.get(address)

            if current_nonce is None:
                # This could happen if a new address was added after startup.
                # A robust implementation might re-sync here.
                # For now, I will raise an error.
                raise ValueError(
                    f"Nonce for address {address} is not managed. Please restart the API.")

            # Increment the nonce for the next request
            self._nonces[address] = current_nonce + 1

            return current_nonce
