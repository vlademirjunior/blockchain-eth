import os
from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from src.core.interfaces import IEncryptionService


class EncryptionService(IEncryptionService):
    """
    Concrete implementation of IEncryptionService using MultiFernet
    to support seamless key rotation.
    """

    def __init__(self):
        """
        Initializes the service by loading a comma-separated list of keys
        from the ENCRYPTION_KEYS environment variable.
        """
        keys_str = os.getenv("ENCRYPTION_KEYS")
        if not keys_str:
            raise ValueError(
                "ENCRYPTION_KEYS environment variable not set or is empty.")

        key_strings = keys_str.split(',')

        # Convert each key string into a Fernet instance
        try:
            # Generate by running src/generate_encryption_key.py
            fernets = [Fernet(key.encode()) for key in key_strings]
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"One of the keys in ENCRYPTION_KEYS is invalid: {e}")

        if not fernets:
            raise ValueError("ENCRYPTION_KEYS must contain at least one key.")

        # Initialize MultiFernet with the list of Fernet instances
        self.multi_fernet = MultiFernet(fernets)

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypts data using the newest key in the list.
        """
        if not isinstance(data, bytes):
            raise TypeError("Data to be encrypted must be bytes.")
        return self.multi_fernet.encrypt(data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        Decrypts data by trying each key until one succeeds.

        Raises:
            cryptography.fernet.InvalidToken: If the token is invalid or tampered with.
        """
        if not isinstance(encrypted_data, bytes):
            raise TypeError("Data to be decrypted must be bytes.")
        try:
            return self.multi_fernet.decrypt(encrypted_data)
        except InvalidToken:
            # Re-raise to provide an clear error message
            raise InvalidToken(
                "Failed to decrypt data with any of the provided keys.")
