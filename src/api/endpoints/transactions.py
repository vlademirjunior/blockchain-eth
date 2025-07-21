from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from src.api.schemas import (
    TransactionValidateRequest,
    TransactionValidateResponse,
    TransactionCreateRequest,
    TransactionCreateResponse,
    TransactionHistoryResponse,
    TransferDetail
)
from src.core.interfaces import ITransactionService
from src.api.dependencies import get_transaction_service
from web3.exceptions import Web3RPCError

router = APIRouter()


@router.post(
    "/validate",
    response_model=TransactionValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate an On-Chain Transaction",
    description="Receives a transaction hash, validates its security (confirmations) and if the destination is a managed address. If valid, it is stored in the history."
)
async def validate_transaction(
    request: TransactionValidateRequest,
    service: ITransactionService = Depends(get_transaction_service)
):
    validated_tx = await service.validate_onchain_transaction(request.tx_hash)

    if not validated_tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found, invalid, or not relevant to this service."
        )

    return TransactionValidateResponse(
        is_valid=True,
        message="Transaction successfully validated and stored in history.",
        transfer=TransferDetail(
            asset=validated_tx.asset,
            from_address=validated_tx.from_address,
            to_address=validated_tx.to_address,
            value=validated_tx.value
        )
    )


@router.post(
    "/create",
    response_model=TransactionCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create and Broadcast a New Transaction",
    description="Creates, signs, and broadcasts a new transaction to the Ethereum network. Returns immediately with a pending status."
)
async def create_transaction(
    request: TransactionCreateRequest,
    background_tasks: BackgroundTasks,
    service: ITransactionService = Depends(get_transaction_service)
):
    try:
        pending_tx = await service.create_onchain_transaction(
            from_address=request.from_address,
            to_address=request.to_address,
            asset=request.asset,
            value=request.value
        )

        background_tasks.add_task(
            service.wait_for_confirmation, pending_tx.tx_hash)

        return TransactionCreateResponse(
            status=pending_tx.status.value,
            tx_hash=pending_tx.tx_hash
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Web3RPCError as e:
        if "insufficient funds" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The source address ({request.from_address}) has insufficient funds to perform the transaction. Please fund it using a Sepolia faucet."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred with the blockchain node: {str(e)}"
        )


@router.get(
    "/history",
    response_model=TransactionHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get transaction history",
    description="Retrieves the history of all transactions, optionally filtered by a specific Ethereum address."
)
async def get_transaction_history_endpoint(
    address: Optional[str] = Query(
        None,
        description="Optional Ethereum address to filter transactions by. If not provided, all transactions are returned."
    ),
    transaction_service: ITransactionService = Depends(get_transaction_service)
):
    try:
        if address:
            history = await transaction_service.get_transaction_history_for_address(address)
        else:
            history = await transaction_service.get_all_transaction_history()

        return TransactionHistoryResponse(history=history)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve transaction history: {str(e)}")
