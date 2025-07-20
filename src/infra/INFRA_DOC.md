# Primitive types

- I'm using Numeric to avoid floating-point errors. (recommed to financial values)
  - The precision and scale can be adjusted as needed.
    - I saw in Stackoverflow links that scale = 18 is common for crypto values.
  - Looking the Numeric docstring looks like a decimal value (good type to financial values).
    - decimal provides arbitrary-precision decimal arithmetic, ensuring that values are stored and calculated exactly as intended

## Async vs sync

- To avoid block database operations (LOCKs)
- Increase performance and tolerance to fault (REST APIs)

## Why Fernet?

- Symmetric cryptography (simplier)
  - Just need a private key to encrypt and decrypt my transactions by example
- Autentitcy cryptography (HMAC)
  - It creates a token with the encrypted data and an HMAC signature.
    - So when I call `.decrypt()`, it first verifies the signature HMAC. If the encrypted data has been modified, even by just a single bit, the verification fails and it raises an `InvalidToken` exception. Looks safer to me!?
- Few public methods (easy to use)
- Fernet use **AES-128** instead `AES-256`.
- Easy to rotate when I want using `MultiFernet` (zero downtime)
  - For maximum security, I might eventually want to re-encrypt old data with the new key with background jobs, creating a separate script that:
    1. Reads each encrypted private key from the database.
    2. Calls the .decrypt() method (which will use an old key).
    3. Calls the .encrypt() method on the result (which will re-encrypt it with the newest key).
    4. Saves the new encrypted value back to the database.
    **This process ensures that eventually, all your data is protected by the latest key, and I can safely remove the oldest keys from my .env file.**

## TX (Universal abbreviation for Transaction)

## Block Explorer

[The miro link reference](https://miro.com/app/board/uXjVJdxGUcs=/?moveToWidget=3458764635040983369&cot=14)

- A block explorer is an online tool that allows users to view and search through the data stored on a blockchain.

## Sepolia (Testnet)

[The Miro Link reference](https://miro.com/app/board/uXjVJdxGUcs=/?moveToWidget=3458764635041404411&cot=14)

- Sepolia is a testnet for the Ethereum network.
- It is primarily used to test smart contracts, decentralized applications (dApps), and other network functionalities before they are released on the `mainnet`.
- Mirrors Mainnet Features
  - It closely mimics the features and behavior of the Ethereum mainnet, making it the ideal environment for final testing before a potential production deployment.

## Nonce Manager (stateful)

- The flow needs to work with competing requests!!
  - Avoid race condition ("nonce too low").
  - A `NonceManager` solves this issue by managing the `nonce` on server-side, instead of `asking each blockchain each time`.
- I'm using Thread-Safe/Async-Safe (`locking` the dictionary)
- The "Stuck Nonce" Problem:
  - What happens if my `NonceManager` provides a nonce of `10`, but the transaction fails to be sent to the blockchain (e.g., the RPC node is offline)?
    - My `NonceManager` thinks that next nonce is `11`, but the blockchain is `still expecting 10`. **All future transactions to that address will fail with the `nonce too high` error**.
    - My solution (Enough for the Challenge) is:
      - Restart the application!
      - Upon `restart`, the *NonceManager will re-synchronize with the blockchain and obtain the correct nonces*.
    - In a production environment, I could use Redis for this because probably implement it with K8S.
- In a real application, I might want to filter for addresses that are actually used for sending transactions on my NonceManager.
