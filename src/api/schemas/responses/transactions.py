from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import List, Optional
from src.core.enums import TransactionStatus


class TransferDetail(BaseModel):
    """Details of a validated transfer."""
    asset: str
    from_address: str
    to_address: str
    value: Decimal


class TransactionValidateResponse(BaseModel):
    """Response from the validation endpoint."""
    is_valid: bool
    message: str
    transfer: Optional[TransferDetail] = None


class TransactionCreateResponse(BaseModel):
    """Response from the creation endpoint, indicating the transaction has been broadcast."""
    status: str
    tx_hash: str


class TransactionHistoryItem(BaseModel):
    """Represents an item in the transaction history."""
    tx_hash: str
    asset: str
    from_address: str
    to_address: str
    value: Decimal
    status: TransactionStatus
    effective_cost: Decimal

    model_config = ConfigDict(from_attributes=True)


class TransactionHistoryResponse(BaseModel):
    """Response from the history endpoint."""
    history: List[TransactionHistoryItem]
