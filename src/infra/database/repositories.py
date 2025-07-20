from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.interfaces import ITransactionRepository, IAddressRepository
from src.core.entities import Transaction, Address
from . import models


class TransactionRepository(ITransactionRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, transaction_entity: Transaction) -> Transaction:
        db_transaction = models.TransactionDB(
            **transaction_entity.model_dump())

        self.db.add(db_transaction)

        await self.db.commit()
        await self.db.refresh(db_transaction)

        return Transaction.model_validate(db_transaction)

    async def update(self, transaction_entity: Transaction) -> Optional[Transaction]:
        """
        Finds a transaction by its hash and updates its status and effective cost.
        """
        query = select(models.TransactionDB).where(
            models.TransactionDB.tx_hash == transaction_entity.tx_hash
        )
        result = await self.db.execute(query)
        db_transaction = result.scalar_one_or_none()

        if db_transaction:
            db_transaction.status = transaction_entity.status.value
            db_transaction.effective_cost = transaction_entity.effective_cost

            await self.db.commit()
            await self.db.refresh(db_transaction)

            return Transaction.model_validate(db_transaction)

        return None

    async def find_by_hash(self, tx_hash: str) -> Optional[Transaction]:
        query = select(models.TransactionDB).where(
            models.TransactionDB.tx_hash == tx_hash)

        result = await self.db.execute(query)

        db_transaction = result.scalar_one_or_none()

        return Transaction.model_validate(db_transaction) if db_transaction else None

    async def get_history(self, address: str) -> List[Transaction]:
        query = select(models.TransactionDB).where(
            (models.TransactionDB.from_address == address) |
            (models.TransactionDB.to_address == address)
        )

        result = await self.db.execute(query)

        db_transactions = result.scalars().all()

        # TODO: cache this result on service
        return [Transaction.model_validate(tx) for tx in db_transactions]

    async def get_all(self) -> List[Transaction]:
        query = select(models.TransactionDB)

        result = await self.db.execute(query)

        db_transactions = result.scalars().all()

        return [Transaction.model_validate(tx) for tx in db_transactions]


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
