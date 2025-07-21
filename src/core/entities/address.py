from pydantic import BaseModel, ConfigDict


class Address(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_address: str
    encrypted_private_key: str
