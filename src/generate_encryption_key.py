from cryptography.fernet import Fernet

# Generate a new URL-safe base64-encoded 32-byte key
key = Fernet.generate_key()

print("Your new Fernet key is:")
print(key.decode())
