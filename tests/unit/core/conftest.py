import pytest
from unittest.mock import AsyncMock, MagicMock
from src.core.services import TransactionService
from src.core.interfaces import (
    ITransactionRepository,
    IAddressRepository,
    IBlockchainService,
    IEncryptionService,
    INonceManager
)


@pytest.fixture
def mock_transaction_repo() -> ITransactionRepository:
    """Provides a mock for ITransactionRepository."""
    return AsyncMock(spec=ITransactionRepository)


@pytest.fixture
def mock_address_repo() -> IAddressRepository:
    """Provides a mock for IAddressRepository."""
    return AsyncMock(spec=IAddressRepository)


@pytest.fixture
def mock_blockchain_service() -> IBlockchainService:
    mock = AsyncMock(spec=IBlockchainService)
    mock.erc20_abi = []
    return mock


@pytest.fixture
def mock_encryption_service() -> IEncryptionService:
    """Provides a mock for IEncryptionService."""
    return MagicMock(spec=IEncryptionService)


@pytest.fixture
def mock_nonce_manager() -> INonceManager:
    """Provides a mock for INonceManager."""
    return AsyncMock(spec=INonceManager)


@pytest.fixture
def transaction_service(
    mock_transaction_repo,
    mock_address_repo,
    mock_blockchain_service,
    mock_encryption_service,
    mock_nonce_manager
) -> TransactionService:
    """Provides a TransactionService instance with all dependencies mocked."""
    return TransactionService(
        transaction_repo=mock_transaction_repo,
        address_repo=mock_address_repo,
        blockchain_service=mock_blockchain_service,
        encryption_service=mock_encryption_service,
        nonce_manager=mock_nonce_manager
    )
