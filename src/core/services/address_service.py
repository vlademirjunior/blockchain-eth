from typing import List
from eth_account import Account
from ..entities import Address
from ..constants import MAX_ADDRESSES_TO_GENERATE
from ..interfaces import (
    IAddressRepository,
    IEncryptionService,
    IAddressService
)


class AddressService(IAddressService):
    """
    Implements the business logic for managing Ethereum addresses.
    """

    def __init__(
        self,
        address_repo: IAddressRepository,
        encryption_service: IEncryptionService
    ):
        self.address_repo = address_repo
        self.encryption_service = encryption_service

    def _create_and_encrypt_address(self) -> Address:
        # Generate a new key pair in memory
        new_account = Account.create()

        # Encrypt the private key immediately
        private_key_bytes = new_account.key
        encrypted_key = self.encryption_service.encrypt(private_key_bytes)

        # Create the address entity
        return Address(
            public_address=new_account.address,
            encrypted_private_key=encrypted_key.decode(
                'utf-8')  # Store as string
        )

    async def create_new_addresses(self, count: int) -> List[Address]:
        if not 0 < count <= MAX_ADDRESSES_TO_GENERATE:  # Basic validation
            raise ValueError(
                f"Number of addresses to create must be between 1 and {MAX_ADDRESSES_TO_GENERATE}."
            )

        new_addresses = [self._create_and_encrypt_address()
                         for _ in range(count)]
        await self.address_repo.create_many(new_addresses)

        # Return only the public parts of the addresses
        return [Address(public_address=addr.public_address, encrypted_private_key='') for addr in new_addresses]

    async def get_all_addresses(self) -> List[Address]:
        return await self.address_repo.get_all()
