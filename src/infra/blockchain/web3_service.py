import json
from typing import List, Dict, Any, Optional
from web3 import AsyncWeb3, AsyncHTTPProvider, Web3
from web3.exceptions import TransactionNotFound, TimeExhausted
from src.core.interfaces import IBlockchainService


class Web3BlockchainService(IBlockchainService):
    """
    Concrete implementation of IBlockchainService using the web3.py library.
    """

    def __init__(self, rpc_url: str):
        if not rpc_url:
            raise ValueError("RPC URL cannot be empty.")

        self.web3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))

        # More robust way, like use local cache database and block explorer or Postgres with JSON field
        with open("src/infra/blockchain/erc20_abi.json") as f:
            self.erc20_abi = json.load(f)

    async def is_connected(self) -> bool:
        return await self.web3.is_connected()

    async def get_transaction_details(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        try:
            tx = await self.web3.eth.get_transaction(tx_hash)
            return dict(tx) if tx else None
        except TransactionNotFound:
            return None

    async def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        try:
            receipt = await self.web3.eth.get_transaction_receipt(tx_hash)
            return dict(receipt) if receipt else None
        except TransactionNotFound:
            return None

    async def get_latest_block_number(self) -> int:
        return await self.web3.eth.block_number

    async def get_base_fee(self) -> int:
        latest_block = await self.web3.eth.get_block('latest')
        return latest_block.get('baseFeePerGas', 0)

    async def estimate_gas(self, transaction: Dict[str, Any]) -> int:
        return await self.web3.eth.estimate_gas(transaction)

    async def broadcast_transaction(self, signed_tx_hex: str) -> str:
        tx_hash_bytes = await self.web3.eth.send_raw_transaction(signed_tx_hex)
        return Web3.to_hex(tx_hash_bytes)

    async def get_eth_balance(self, address: str) -> int:
        if not self.web3.is_address(address):
            raise ValueError("Invalid Ethereum address provided.")
        checksum_address = self.web3.to_checksum_address(address)
        # This is an async method with the async provider
        return await self.web3.eth.get_balance(checksum_address)

    async def decode_contract_transaction(
            self,
            tx_hash: str,
            contract_abi: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        tx = await self.get_transaction_details(tx_hash)
        if not tx or not tx.get('to') or not tx.get('input'):
            return None

        try:
            # For contract interactions, web3.py handles sync/async internally
            contract = self.web3.eth.contract(
                address=tx['to'], abi=contract_abi)
            func_obj, func_params = contract.decode_function_input(tx['input'])
            return {
                "function": func_obj.fn_name,
                "params": func_params
            }
        except ValueError:
            # Could not decode input data, likely not a call to a known function
            return None

    async def get_transaction_count(self, address: str) -> int:
        if not self.web3.is_address(address):
            raise ValueError("Invalid Ethereum address provided.")

        checksum_address = self.web3.to_checksum_address(address)

        return await self.web3.eth.get_transaction_count(checksum_address)

    async def wait_for_transaction_receipt(
            self, tx_hash: str, timeout: int) -> Optional[Dict[str, Any]]:
        """
        Waits for a transaction receipt to be available and returns it.
        """
        try:
            receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout)
            return dict(receipt) if receipt else None
        except (TransactionNotFound, TimeExhausted):
            return None
