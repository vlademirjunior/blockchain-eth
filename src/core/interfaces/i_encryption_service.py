from abc import ABC, abstractmethod


class IEncryptionService(ABC):
    """
    Interface for a service that handles data encryption and decryption keys
    It is synchronized process because use CPU operations (CPU-bound)
    """
    @abstractmethod
    def encrypt(self, data: bytes) -> bytes:
        pass

    @abstractmethod
    def decrypt(self, encrypted_data: bytes) -> bytes:
        pass
