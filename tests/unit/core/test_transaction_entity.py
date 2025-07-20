from decimal import Decimal
import pytest
from pydantic import ValidationError
from src.core.entities import Transaction


class TestTransactionEntity:
    """
    Test suite for the Transaction domain entity.
    """

    def test_transaction_creation_successful(self):
        """
        Tests that a Transaction object can be successfully created with valid data.
        """
        # Arrange
        valid_data = {
            "tx_hash": "0x12345678",
            "asset": "ETH",
            "from_address": "0xFromAddress",
            "to_address": "0x2ToAddress",
            "value": Decimal('1.5'),
            "status": "confirmed",
            "effective_cost": Decimal('0.0021')
        }

        # Act
        transaction = Transaction(**valid_data)

        # Assert
        assert transaction.tx_hash == valid_data["tx_hash"]
        assert transaction.asset == valid_data["asset"]
        assert transaction.from_address == valid_data["from_address"]
        assert transaction.to_address == valid_data["to_address"]
        assert transaction.value == valid_data["value"]
        assert transaction.status == valid_data["status"]
        assert transaction.effective_cost == valid_data["effective_cost"]

    def test_transaction_creation_with_type_coercion(self):
        """
        Tests that Pydantic correctly coerces compatible types 
        (e.g., int or float) to guarantee more security in code.
        """
        # Arrange
        data_with_int = {
            "tx_hash": "0x12345678",
            "asset": "ETH",
            "from_address": "0xFromAddress",
            "to_address": "0xToAddress",
            "value": 100,
            "status": "pending",
            "effective_cost": 0.01
        }

        # Act
        transaction = Transaction(**data_with_int)

        # Assert
        assert isinstance(transaction.value, Decimal)
        assert transaction.value == Decimal('100')

        assert isinstance(transaction.effective_cost, Decimal)
        assert transaction.effective_cost == Decimal('0.01')

    def test_transaction_creation_fails_with_invalid_data_type(self):
        """
        Tests that creating a Transaction fails with a ValidationError
        if a field receives an incompatible data type.
        """
        # Arrange
        invalid_data = {
            "tx_hash": "0x12345678",
            "asset": "ETH",
            "from_address": "0xFromAddress",
            "to_address": "0xToAddress",
            "value": "MY_INVALID_TYPE",
            "status": "failed",
            "effective_cost":  Decimal('0.0')
        }

        # Act & Assert:
        with pytest.raises(ValidationError) as ex:
            Transaction(**invalid_data)

        assert "value" in str(ex.value)
        assert "Input should be a valid decimal" in str(ex.value)

    def test_transaction_creation_fails_with_missing_field(self):
        """
        Tests that creating a Transaction fails with a ValidationError
        if a required field is missing.
        """
        # Arrange
        missing_field_data = {
            "tx_hash": "0x12345678",
            # "asset": "ETH",
            "from_address": "0xFromAddress",
            "to_address": "0x2ToAddress",
            "value": Decimal('1.5'),
            "status": "confirmed",
            "effective_cost": Decimal('0.123')
        }

        # Act & Assert:
        with pytest.raises(ValidationError) as ex:
            Transaction(**missing_field_data)

        # Assert
        assert "asset" in str(ex.value)
        assert "Field required" in str(ex.value)
