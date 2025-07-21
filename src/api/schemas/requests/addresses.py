from pydantic import BaseModel, Field
from src.core.constants import MAX_ADDRESSES_TO_GENERATE


class AddressCreateRequest(BaseModel):
    """Request body to create new addresses."""
    count: int = Field(..., gt=0, le=MAX_ADDRESSES_TO_GENERATE,
                       description=f"The number of new addresses to generate (1-{MAX_ADDRESSES_TO_GENERATE}).")
