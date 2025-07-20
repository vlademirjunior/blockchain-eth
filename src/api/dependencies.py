import os
from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.interfaces import (
    IBlockchainService, IEncryptionService, ITransactionRepository,
    IAddressRepository, INonceManager, ITransactionService, IAddressService
)
from src.infra.database.config import SessionLocal
from src.infra.blockchain.web3_service import Web3BlockchainService
from src.infra.security.encryption import EncryptionService
from src.infra.database.repositories import TransactionRepository, AddressRepository
from src.infra.blockchain.nonce_manager import NonceManager
from src.core.services import AddressService, TransactionService


# --- Infrastructure Dependencies ---

async def get_db() -> AsyncSession:  # type: ignore
    async with SessionLocal() as session:
        yield session


def get_encryption_service() -> IEncryptionService:
    return EncryptionService()


def get_blockchain_service() -> IBlockchainService:
    rpc_url = os.getenv("ETHEREUM_RPC_URL")
    if not rpc_url:
        raise ValueError("ETHEREUM_RPC_URL environment variable is not set.")
    return Web3BlockchainService(rpc_url=rpc_url)

# --- Repository Dependencies ---


def get_address_repository(db: AsyncSession = Depends(get_db)) -> IAddressRepository:
    return AddressRepository(db)


def get_transaction_repository(db: AsyncSession = Depends(get_db)) -> ITransactionRepository:
    return TransactionRepository(db)


# --- Cached Singleton Instance ---
# This will hold our single NonceManager instance once created.
_nonce_manager_singleton: Optional[INonceManager] = None


async def get_nonce_manager(
    address_repo: IAddressRepository = Depends(get_address_repository),
    blockchain_service: IBlockchainService = Depends(get_blockchain_service)
) -> INonceManager:
    """
    Dependency to get the singleton NonceManager instance.
    On the first call, it creates, initializes, and caches the instance.
    Subsequent calls will return the cached instance.
    """
    global _nonce_manager_singleton
    if _nonce_manager_singleton is None:
        _nonce_manager_singleton = NonceManager(
            address_repo=address_repo,
            blockchain_service=blockchain_service
        )
        await _nonce_manager_singleton.initialize_nonces()
    return _nonce_manager_singleton

# --- Service Dependencies ---


def get_transaction_service(
    transaction_repo: ITransactionRepository = Depends(
        get_transaction_repository),
    address_repo: IAddressRepository = Depends(get_address_repository),
    blockchain_service: IBlockchainService = Depends(get_blockchain_service),
    encryption_service: IEncryptionService = Depends(get_encryption_service),
    nonce_manager: INonceManager = Depends(get_nonce_manager)
) -> ITransactionService:
    return TransactionService(
        transaction_repo=transaction_repo,
        address_repo=address_repo,
        blockchain_service=blockchain_service,
        encryption_service=encryption_service,
        nonce_manager=nonce_manager
    )


def get_address_service(
    address_repo: IAddressRepository = Depends(get_address_repository),
    encryption_service: IEncryptionService = Depends(get_encryption_service)
) -> IAddressService:
    """
    Dependency that provides an AddressService instance.
    """
    return AddressService(
        address_repo=address_repo,
        encryption_service=encryption_service
    )
