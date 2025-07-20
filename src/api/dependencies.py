import os
from typing import AsyncGenerator, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.services import TransactionService
from src.infra.blockchain.nonce_manager import NonceManager
from src.core.interfaces import IAddressRepository, IBlockchainService, IEncryptionService, INonceManager, ITransactionRepository, ITransactionService
from src.infra.database.config import SessionLocal
from src.infra.blockchain.web3_service import Web3BlockchainService
from src.infra.security.encryption import EncryptionService
from src.infra.database.repositories import AddressRepository, TransactionRepository


# TODO: Separate in files

# --- Infra dependencias ---

def get_encryption_service() -> IEncryptionService:
    return EncryptionService()


def get_blockchain_service() -> IBlockchainService:
    rpc_url = os.getenv("ETHEREUM_RPC_URL")
    if not rpc_url:
        raise ValueError("ETHEREUM_RPC_URL environment variable is not set.")
    return Web3BlockchainService(rpc_url=rpc_url)


async def get_db() -> AsyncSession:  # type: ignore
    """
    This is what will be replaced during testing.
    """
    async with SessionLocal() as session:
        yield session


# --- Repository Dependencies ---

def get_transaction_repository(db: AsyncSession = Depends(get_db)) -> ITransactionRepository:
    return TransactionRepository(db)


def get_address_repository(db: AsyncSession = Depends(get_db)) -> IAddressRepository:
    return AddressRepository(db)


# --- Nonce Manager Dependency (initialized via lifespan) ---
_nonce_manager_instance: Optional[INonceManager] = None


async def _get_initialized_nonce_manager(
    address_repo: IAddressRepository = Depends(get_address_repository),
    blockchain_service: IBlockchainService = Depends(get_blockchain_service)
) -> AsyncGenerator[INonceManager, None]:
    """
    Initializes the NonceManager as part of the application lifespan.
    This runs once at startup.
    """
    global _nonce_manager_instance
    if _nonce_manager_instance is None:
        print("Initializing NonceManager...")
        # Instantiate NonceManager correctly, passing address_repo and blockchain_service
        _nonce_manager_instance = NonceManager(
            address_repo=address_repo,
            blockchain_service=blockchain_service
        )

        # Call initialize_nonces() WITHOUT any arguments
        await _nonce_manager_instance.initialize_nonces()
        print("NonceManager initialized.")
    yield _nonce_manager_instance
    # Add cleanup logic here if needed, for example, saving nonces to a persistent store
    print("NonceManager shutdown logic (if any).")


def get_nonce_manager() -> INonceManager:
    """
    Provides the already initialized NonceManager instance.
    This will be called for each request requiring the NonceManager.
    """
    if _nonce_manager_instance is None:
        # This case should ideally not be hit if lifespan setup is correct
        raise RuntimeError("NonceManager has not been initialized.")
    return _nonce_manager_instance

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
