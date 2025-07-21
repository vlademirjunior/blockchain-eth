from sqlalchemy import Column, Integer, String
from ..config import Base


class AddressDB(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    public_address = Column(String, unique=True, index=True, nullable=False)
    encrypted_private_key = Column(String, nullable=False)
