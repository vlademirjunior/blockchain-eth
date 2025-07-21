from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.interfaces import ITransactionRepository
from src.core.entities import Transaction
from .. import models


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

        return [Transaction.model_validate(tx) for tx in db_transactions]

    async def get_all(self) -> List[Transaction]:
        query = select(models.TransactionDB)

        result = await self.db.execute(query)

        db_transactions = result.scalars().all()

        return [Transaction.model_validate(tx) for tx in db_transactions]
