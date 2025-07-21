from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from ..enums import TransactionStatus


class Transaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tx_hash: str
    asset: str
    from_address: str
    to_address: str
    value: Decimal
    status: TransactionStatus
    effective_cost: Decimal
