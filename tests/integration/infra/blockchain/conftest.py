import pytest_asyncio
import json
from web3 import AsyncWeb3
from web3.providers.eth_tester import AsyncEthereumTesterProvider
from src.infra.blockchain.web3_service import Web3BlockchainService

with open("src/infra/blockchain/erc20_abi.json") as f:
    ERC20_ABI = json.load(f)


@pytest_asyncio.fixture(scope="module")
async def web3_instance() -> AsyncWeb3:
    """
    Provides an ASYNCHRONOUS web3 instance connected to a clean,
    in-memory Ethereum tester blockchain.
    """
    provider = AsyncEthereumTesterProvider()
    return AsyncWeb3(provider)


@pytest_asyncio.fixture(scope="function")
async def blockchain_service(web3_instance: AsyncWeb3, monkeypatch) -> Web3BlockchainService:
    """
    Provides an instance of Web3BlockchainService for testing,
    injecting our async test web3 instance.
    """
    # Bypasses the real __init__ to inject the test instance
    monkeypatch.setattr(Web3BlockchainService, "__init__",
                        lambda s, rpc_url: None)

    # Create the service instance (rpc_url can be a dummy value due to mocking)
    service = Web3BlockchainService(rpc_url="http://test-rpc")

    # IMPORTANT: Replace the real web3 instance with our test instance
    service.web3 = web3_instance
    service.erc20_abi = ERC20_ABI

    return service
