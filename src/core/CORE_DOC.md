# Transaction Objects

[The Miro link references](https://miro.com/app/board/uXjVJdxGUcs=/?moveToWidget=3458764635031604392&cot=14)

## Exceptions

- In the real world, I don't recommend throw Exceptions because Exceptions have costs.
  - I use the Notification Pattern and Domain Validations with Rich Domain to Solve it!

## Why Enums?

- In the real world, using Postgres by example, just change my `TransactionDB`:
  - `from sqlalchemy.dialects.postgresql import ENUM`
  - `status = Column(Enum(TransactionStatus), nullable=False)`
  - Safer to use enums
    - Easy to mantain (avoid bugs)

## Wei vs Ether Units

[The miro link reference](https://miro.com/app/board/uXjVJdxGUcs=/?moveToWidget=3458764635039293293&cot=14)

- The lib web3.py and the EVM operate almost exclusively on the smallest unit of Ether, the Wei!!
- Ethereum network. One ether = 1,000,000,000,000,000,000 wei (10^18). The other way to look at it is one wei is one quintillionth of an ether.
- Conversion to and from human-readable formats (such as Decimal representing Ether) should be done in my core services or even the API layer... using the Web3.to_wei() and Web3.from_wei() functions, `keeping internal calculations` in `Wei format prevents precision errors`.
  - **My blockchain_service should receive and return values in Wei (as `int`).**

## The web3.py lib and Ethereum Blockchain

[The miro reference](https://miro.com/app/board/uXjVJdxGUcs=/?moveToWidget=3458764635039850504&cot=14)

- The web3 exposes the properties and methods to interact with the RPC APIs of the ETH Blockchain.

## AsyncHTTPProvider vs HTTPProvider (Web3)

- Because using synchronous HTTPProvider will degrade my API performance.
**Any operation that waits for a network response (I/O-bound) must be `async` so as not to block the entire server.**

## RPC node with Try Except

[The miro link reference](https://miro.com/app/board/uXjVJdxGUcs=/?moveToWidget=3458764635039549111&cot=14)

- An RPC node, or Remote Procedure Call node, is a computer that acts as a bridge between decentralized applications (dApps) and a blockchain network
  - What happens if the RPC node is offline?
  - What happens if a transaction is not found?

## ABI ERC-20 (JSON)

[The miro link reference](https://miro.com/app/board/uXjVJdxGUcs=/?moveToWidget=3458764634804591096&cot=10)

- The Application Binary Interface (ABI) is a JSON that describes the functions of a contract.
- Web3.py needs the ABI to know how to encode a call to the transfer() function and how to decode its events as well.

## CHAIN_ID

- Chain IDs are public, standard numbers.
- I'm using the Sepolia testnet, and its CHAIN_ID is 11155111
- [For other networks, a fantastic resource to find the correct CHAIN_ID is the website Chainlist.org.](https://chainlist.org/)

## MIN_CONFIRMATIONS

[The Miro Reference](https://miro.com/app/board/uXjVJdxGUcs=/?moveToWidget=3458764635046362117&cot=14)

- In blockchain transactions, confirmation refers to how many blocks have been added to the blockchain since a transaction was included in a block.
- The more confirmations a transaction has, the more secure and irreversible it is considered.
- While one confirmation indicates the transaction is recorded, it's not fully secure or irreversible. Generally, `6` confirmations are considered "safe" for `most` transactions.
  - I'm using `12` because is enough.
  - Different blockchains and platforms may have different confirmation requirements.
- On the Ethereum network, it generally takes about 20 minutes to add a new block, meaning 12 confirmations would take about 20 minutes.
