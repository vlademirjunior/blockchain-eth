import pytest
import pytest_asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# Ensure this path is correct for your DB models
from src.infra.database.models import Base
# Ensure this path is correct for your core entities
from src.core.entities import Transaction
# Ensure this path is correct for your enums
from src.core.enums import TransactionStatus
# Ensure this path is correct for your repository
from src.infra.database.repositories import TransactionRepository


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    """
    Pytest fixture that provides a clean database session for each test function.
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide a session to the test
    async with TestSessionLocal() as session:
        yield session

    # Clean up the database after the test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def transaction_repo(db_session: AsyncSession) -> TransactionRepository:
    return TransactionRepository(db_session)


@pytest.mark.asyncio
class TestTransactionRepository:
    """
    Integration test suite for the TransactionRepository.
    """

    async def test_create_and_find_by_hash(self, transaction_repo: TransactionRepository):
        """
        Tests if a transaction can be created and then found by its hash
        """
        # Arrange
        test_tx_entity = Transaction(
            tx_hash="0x12345_test_create",
            asset="ETH",
            from_address="0xFromAddress",
            to_address="0xToAddress",
            value=Decimal("1.5"),
            status=TransactionStatus.CONFIRMED,
            effective_cost=Decimal("0.0021")
        )

        # Act
        # The create method now returns the Transaction entity, so capture it
        created_tx = await transaction_repo.create(test_tx_entity)

        # Assert creation and returned object
        assert created_tx is not None
        # Assert it's a domain entity
        assert isinstance(created_tx, Transaction)
        assert created_tx.tx_hash == "0x12345_test_create"
        assert created_tx.to_address == "0xToAddress"
        assert created_tx.value == Decimal("1.5")
        assert created_tx.status == TransactionStatus.CONFIRMED

        # Assert finding the transaction
        found_tx = await transaction_repo.find_by_hash("0x12345_test_create")

        assert found_tx is not None
        assert isinstance(found_tx, Transaction)  # Assert it's a domain entity
        assert found_tx.tx_hash == "0x12345_test_create"
        assert found_tx.to_address == "0xToAddress"
        assert found_tx.value == Decimal("1.5")
        # Verify status is also correctly retrieved
        assert found_tx.status == TransactionStatus.CONFIRMED

    async def test_find_by_hash_not_found(self, transaction_repo: TransactionRepository):
        """
        Tests if find_by_hash returns None when the transaction does not exist.
        """
        # Act
        found_tx = await transaction_repo.find_by_hash("0x_non_existent_hash")

        # Assert
        assert found_tx is None

    async def test_get_history_for_address(self, transaction_repo: TransactionRepository):
        """
        Tests if the transaction history for a specific address is returned correctly.
        """
        # Arrange
        target_address = "address-history-test"

        tx1 = Transaction(tx_hash="0x_hist1", asset="ETH", from_address=target_address, to_address="other1", value=Decimal(
            "1"), status=TransactionStatus.CONFIRMED, effective_cost=Decimal("0.01"))
        tx2 = Transaction(tx_hash="0x_hist2", asset="BTC", from_address="other2", to_address=target_address, value=Decimal(
            "100"), status=TransactionStatus.CONFIRMED, effective_cost=Decimal("0.02"))

        tx3 = Transaction(tx_hash="0x_hist3", asset="ETH", from_address="other3", to_address="DIFFERENT", value=Decimal(
            "5"), status=TransactionStatus.CONFIRMED, effective_cost=Decimal("0.03"))

        await transaction_repo.create(tx1)
        await transaction_repo.create(tx2)
        await transaction_repo.create(tx3)

        # Act
        history = await transaction_repo.get_history(address=target_address)

        # Assert
        assert len(history) == 2
        # Ensure returned objects are domain entities
        for tx in history:
            assert isinstance(tx, Transaction)

        found_hashes = {tx.tx_hash for tx in history}
        assert "0x_hist1" in found_hashes
        assert "0x_hist2" in found_hashes

        assert "0x_hist3" not in found_hashes

    async def test_get_all(self, transaction_repo: TransactionRepository):
        """
        Tests if get_all returns all transactions in the repository.
        """
        # Arrange
        tx1 = Transaction(
            tx_hash="0x_all_1", asset="ETH", from_address="sender1", to_address="rec1",
            value=Decimal("10"), status=TransactionStatus.PENDING, effective_cost=Decimal("0.001")
        )
        tx2 = Transaction(
            tx_hash="0x_all_2", asset="ERC20", from_address="sender2", to_address="rec2",
            value=Decimal("50"), status=TransactionStatus.CONFIRMED, effective_cost=Decimal("0.002")
        )
        tx3 = Transaction(
            tx_hash="0x_all_3", asset="ETH", from_address="sender3", to_address="rec3",
            value=Decimal("2"), status=TransactionStatus.FAILED, effective_cost=Decimal("0.0005")
        )

        await transaction_repo.create(tx1)
        await transaction_repo.create(tx2)
        await transaction_repo.create(tx3)

        # Act
        all_transactions = await transaction_repo.get_all()

        # Assert
        assert len(all_transactions) == 3
        # Ensure returned objects are domain entities
        for tx in all_transactions:
            assert isinstance(tx, Transaction)

        found_hashes = {tx.tx_hash for tx in all_transactions}
        assert "0x_all_1" in found_hashes
        assert "0x_all_2" in found_hashes
        assert "0x_all_3" in found_hashes
