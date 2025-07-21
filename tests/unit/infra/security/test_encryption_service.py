import pytest
from cryptography.fernet import Fernet, InvalidToken
from src.infra.security.encryption import EncryptionService


class TestEncryptionService:
    """
    Unit test suite for the EncryptionService.
    """

    def test_successful_initialization(self, monkeypatch):
        """
        Tests that the service initializes correctly with a valid key.
        """
        # Arrange
        key = Fernet.generate_key().decode()
        monkeypatch.setenv("ENCRYPTION_KEYS", key)

        # Act
        service = EncryptionService()

        # Assert
        assert isinstance(service, EncryptionService)
        assert hasattr(service, 'multi_fernet')

    @pytest.mark.parametrize("env_value, expected_error_msg", [
        (None, "ENCRYPTION_KEYS environment variable not set or is empty."),
        ("", "ENCRYPTION_KEYS environment variable not set or is empty."),
        ("not-a-valid-key", "One of the keys in ENCRYPTION_KEYS is invalid"),
        (f"{Fernet.generate_key().decode()},invalid-key",
         "One of the keys in ENCRYPTION_KEYS is invalid"),
    ])
    def test_initialization_fails_with_invalid_env(self, monkeypatch, env_value, expected_error_msg):
        """
        Tests that the service raises a ValueError if the environment variable is
        missing, empty, or contains invalid keys.
        """
        # Arrange
        if env_value is not None:
            monkeypatch.setenv("ENCRYPTION_KEYS", env_value)
        else:
            monkeypatch.delenv("ENCRYPTION_KEYS", raising=False)

        # Act & Assert
        with pytest.raises(ValueError) as ex:
            EncryptionService()

        assert expected_error_msg in str(ex.value)

    def test_encrypt_decrypt_roundtrip(self, monkeypatch):
        """
        Tests that data encrypted by the service can be decrypted successfully.
        """
        # Arrange
        key = Fernet.generate_key().decode()
        monkeypatch.setenv("ENCRYPTION_KEYS", key)
        service = EncryptionService()
        original_data = b"this is a secret message"

        # Act
        encrypted_data = service.encrypt(original_data)
        decrypted_data = service.decrypt(encrypted_data)

        # Assert
        assert encrypted_data != original_data
        assert decrypted_data == original_data

    def test_key_rotation_successful(self, monkeypatch):
        """
        Tests the core key rotation logic of MultiFernet.
        It should be able to decrypt data with an old key after a new one is added.
        """
        # Arrange
        # Setup with an old key
        old_key = Fernet.generate_key().decode()

        monkeypatch.setenv("ENCRYPTION_KEYS", old_key)

        service_with_old_key = EncryptionService()

        secret_data = b"data encrypted with the old key"

        # Encrypt data using only the old key
        encrypted_with_old_key = service_with_old_key.encrypt(secret_data)

        # Act
        # Rotate the key by prepending a new key
        new_key = Fernet.generate_key().decode()

        rotated_keys = f"{new_key},{old_key}"

        monkeypatch.setenv("ENCRYPTION_KEYS", rotated_keys)

        # Create a new service instance with the rotated keys
        service_with_rotated_keys = EncryptionService()

        # Encrypt new data, which should use the new key
        new_secret_data = b"data encrypted with the new key"
        encrypted_with_new_key = service_with_rotated_keys.encrypt(
            new_secret_data)

        # Assert:
        # The new service can decrypt data encrypted with the OLD key.
        decrypted_old_data = service_with_rotated_keys.decrypt(
            encrypted_with_old_key)

        assert decrypted_old_data == secret_data

        # The new service can decrypt data encrypted with the NEW key.
        decrypted_new_data = service_with_rotated_keys.decrypt(
            encrypted_with_new_key)

        assert decrypted_new_data == new_secret_data

    def test_decrypt_fails_with_invalid_token(self, monkeypatch):
        """
        Tests that decrypting tampered or invalid data raises an InvalidToken error.
        """
        # Arrange
        key = Fernet.generate_key().decode()

        monkeypatch.setenv("ENCRYPTION_KEYS", key)

        service = EncryptionService()

        invalid_data = b"this is not a valid fernet token"

        # Act & Assert
        with pytest.raises(InvalidToken) as ex:
            service.decrypt(invalid_data)

        assert "Failed to decrypt data with any of the provided keys." in str(
            ex.value)

    @pytest.mark.parametrize("invalid_input", [123, "a string", {"a": "dict"}])
    def test_encrypt_raises_type_error_for_non_bytes(self, monkeypatch, invalid_input):
        """
        Tests that encrypt raises TypeError if input is not bytes.
        """
        # Arrange
        key = Fernet.generate_key().decode()

        monkeypatch.setenv("ENCRYPTION_KEYS", key)

        service = EncryptionService()

        # Act & Assert
        with pytest.raises(TypeError, match="Data to be encrypted must be bytes."):
            service.encrypt(invalid_input)

    @pytest.mark.parametrize("invalid_input", [123, "a string", {"a": "dict"}])
    def test_decrypt_raises_type_error_for_non_bytes(self, monkeypatch, invalid_input):
        """
        Tests that decrypt raises TypeError if input is not bytes.
        """
        # Arrange
        key = Fernet.generate_key().decode()

        monkeypatch.setenv("ENCRYPTION_KEYS", key)

        service = EncryptionService()

        # Act & Assert
        with pytest.raises(TypeError, match="Data to be decrypted must be bytes."):
            service.decrypt(invalid_input)
