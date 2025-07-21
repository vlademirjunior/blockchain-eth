from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.interfaces import IAddressRepository
from src.core.entities.address import Address
from .. import models


class AddressRepository(IAddressRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_many(self, addresses: List[Address]) -> None:
        db_addresses = [
            models.AddressDB(**address.model_dump()) for address in addresses
        ]

        self.db.add_all(db_addresses)

        await self.db.commit()

    async def get_all(self) -> List[Address]:
        query = select(models.AddressDB)

        result = await self.db.execute(query)

        db_addresses = result.scalars().all()

        return [Address.model_validate(addr) for addr in db_addresses]

    async def find_by_public_address(self, public_address: str) -> Optional[Address]:
        query = select(models.AddressDB).where(
            models.AddressDB.public_address == public_address)

        result = await self.db.execute(query)

        db_address = result.scalar_one_or_none()

        return Address.model_validate(db_address) if db_address else None
