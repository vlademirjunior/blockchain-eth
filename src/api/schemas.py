from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import List, Optional
from src.core.enums import TransactionStatus


# TODO: Separate in files

class TransactionValidateRequest(BaseModel):
    """Request body to validate a transaction."""
    tx_hash: str = Field(..., min_length=66, max_length=66,
                         description="The hash of the transaction to be validated.")


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


class TransactionCreateRequest(BaseModel):
    """Request body to create a new transaction."""
    from_address: str = Field(...,
                              description="The source address of the transfer.")
    to_address: str = Field(...,
                            description="The destination address of the transfer.")
    asset: str = Field(...,
                       description="The asset to be transferred (e.g., 'ETH').")
    value: Decimal = Field(..., gt=0,
                           description="The amount to be transferred.")


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


class AddressCreateRequest(BaseModel):
    """Request body to create new addresses."""
    count: int = Field(..., gt=0, le=100,
                       description="The number of new addresses to generate (1-100).")


class AddressResponse(BaseModel):
    """Represents a single public address in a response."""
    public_address: str


class AddressCreateResponse(BaseModel):
    """Response after successfully creating new addresses."""
    message: str
    created_addresses: List[AddressResponse]


class AddressListResponse(BaseModel):
    """Response for the endpoint that lists all managed addresses."""
    addresses: List[AddressResponse]
