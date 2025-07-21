from sqlalchemy import Column, String, Numeric
from ..config import Base


class TransactionDB(Base):
    __tablename__ = "transactions"

    tx_hash = Column(String, primary_key=True, index=True)
    asset = Column(String, nullable=False)
    from_address = Column(String, index=True, nullable=False)
    to_address = Column(String, index=True, nullable=False)
    value = Column(Numeric(36, 18), nullable=False)
    status = Column(String, nullable=False)
    effective_cost = Column(Numeric(36, 18), nullable=False)
