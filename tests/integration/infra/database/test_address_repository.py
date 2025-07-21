import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.infra.database.config import Base
from src.core.entities.address import Address
from src.infra.database.repositories import AddressRepository


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:  # type: ignore
    """
    Pytest fixture that provides a clean database session for each test function.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def address_repo(db_session: AsyncSession) -> AddressRepository:
    return AddressRepository(db_session)


@pytest.mark.asyncio
class TestAddressRepository:
    """
    Integration test suite for the AddressRepository.
    """

    async def test_create_many_and_get_all(self, address_repo: AddressRepository):
        """
        Tests if multiple addresses can be created and then retrieved successfully.
        """
        # Arrange
        address1 = Address(
            public_address="0xAddress1",
            encrypted_private_key="key1"
        )
        address2 = Address(
            public_address="0xAddress2",
            encrypted_private_key="key2"
        )
        addresses_to_create = [address1, address2]

        # Act
        await address_repo.create_many(addresses_to_create)
        all_addresses = await address_repo.get_all()

        # Assert
        assert len(all_addresses) == 2
        assert isinstance(all_addresses[0], Address)

        found_addresses = {addr.public_address for addr in all_addresses}
        assert "0xAddress1" in found_addresses
        assert "0xAddress2" in found_addresses

    async def test_find_by_public_address_success(self, address_repo: AddressRepository):
        """
        Tests finding an existing address by its public address.
        """
        # Arrange
        address_to_find = Address(
            public_address="0xAddressToFind",
            encrypted_private_key="key_to_find"
        )
        await address_repo.create_many([address_to_find])

        # Act
        found_address = await address_repo.find_by_public_address("0xAddressToFind")

        # Assert
        assert found_address is not None
        assert isinstance(found_address, Address)

        assert found_address.public_address == "0xAddressToFind"
        assert found_address.encrypted_private_key == "key_to_find"

    async def test_find_by_public_address_not_found(self, address_repo: AddressRepository):
        """
        Tests that find_by_public_address returns None for a non-existent address.
        """
        # Act
        found_address = await address_repo.find_by_public_address("0xNonExistentAddress")

        # Assert
        assert found_address is None
