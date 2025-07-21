from pydantic import BaseModel
from typing import List


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
