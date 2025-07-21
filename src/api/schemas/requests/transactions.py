from pydantic import BaseModel, Field
from decimal import Decimal
from src.core.constants import ETH_ASSET_IDENTIFIER


class TransactionValidateRequest(BaseModel):
    """Request body to validate a transaction."""
    tx_hash: str = Field(..., min_length=66, max_length=66,
                         description="The hash of the transaction to be validated.")


class TransactionCreateRequest(BaseModel):
    """Request body to create a new transaction."""
    from_address: str = Field(...,
                              description="The source address of the transfer.")
    to_address: str = Field(...,
                            description="The destination address of the transfer.")
    asset: str = Field(...,
                       description=f"The asset to be transferred (e.g., '{ETH_ASSET_IDENTIFIER}').")
    value: Decimal = Field(..., gt=0,
                           description="The amount to be transferred.")
