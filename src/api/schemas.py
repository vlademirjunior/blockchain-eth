from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from src.core.enums import TransactionStatus


class TransactionRequest(BaseModel):
    """
    Request model for creating a new on-chain transaction.
    """
    from_address: str = Field(...,
                              description="The sender's Ethereum address.")
    to_address: str = Field(...,
                            description="The recipient's Ethereum address.")
    asset: str = Field(...,
                       description="The asset to transfer (e.g., 'ETH', 'ERC-20_TOKEN').")
    value: Decimal = Field(..., gt=0,
                           description="The amount of asset to transfer.")


class TransactionResponse(BaseModel):
    """
    Response model for a transaction, used for both creation and history.
    """
    tx_hash: str = Field(..., description="The hash of the transaction.")
    asset: str = Field(...,
                       description="The asset involved in the transaction.")
    from_address: str = Field(...,
                              description="The sender's Ethereum address.")
    to_address: str = Field(...,
                            description="The recipient's Ethereum address.")
    value: Decimal = Field(...,
                           description="The value transferred in decimal format.")
    status: TransactionStatus = Field(...,
                                      description="The current status of the transaction.")
    effective_cost: Decimal = Field(
        ..., description="The effective cost of the transaction in ETH (gasUsed * effectiveGasPrice).")


class TransactionValidationRequest(BaseModel):
    """
    Request model for validating an on-chain transaction.
    """
    tx_hash: str = Field(..., description="The transaction hash to validate.")


class TransactionValidationResponse(BaseModel):
    """
    Response model for the transaction validation endpoint.
    """
    is_valid: bool = Field(...,
                           description="Indicates if the transaction is valid and secure.")
    transaction_details: Optional[TransactionResponse] = Field(
        None, description="Details of the validated transaction if valid.")
    message: str = Field(...,
                         description="A message describing the validation result.")


class TransactionHistoryResponse(BaseModel):
    """
    Response model for retrieving the transaction history.
    """
    transactions: List[TransactionResponse] = Field(
        ..., description="List of recorded transaction history.")
