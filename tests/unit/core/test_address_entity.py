import pytest
from pydantic import ValidationError
from src.core.entities.address import Address


class TestAddressEntity:
    """
    Test suite for the Address domain entity.
    """

    def test_address_creation_successful(self):
        """
        Tests that an Address object can be successfully created with valid data.
        """
        # Arrange
        valid_data = {
            "public_address": "0x12345678",
            "encrypted_private_key": "some_long_encrypted_string_of_data"
        }

        # Act
        address = Address(**valid_data)

        # Assert
        assert address.public_address == valid_data["public_address"]
        assert address.encrypted_private_key == valid_data["encrypted_private_key"]

    @pytest.mark.parametrize("missing_field", ["public_address", "encrypted_private_key"])
    def test_address_creation_fails_with_missing_field(self, missing_field):
        """
        Tests that creating an Address fails with a ValidationError
        if a required field is missing.
        """
        # Arrange
        invalid_data = {
            "public_address": "0x12345678",
            "encrypted_private_key": "some_long_encrypted_string_of_data"
        }

        del invalid_data[missing_field]

        # Act & Assert
        with pytest.raises(ValidationError) as ex:
            Address(**invalid_data)

        assert missing_field in str(ex.value)
        assert "Field required" in str(ex.value)
