from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from src.core.services import ITransactionService
from src.api.dependencies import get_transaction_service
from src.api.schemas import (
    TransactionRequest,
    TransactionResponse,
    TransactionValidationRequest,
    TransactionValidationResponse,
    TransactionHistoryResponse
)


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


@router.post(
    "/create",
    response_model=TransactionResponse,
    status_code=202,  # 202 Accepted for background task
    summary="Create and broadcast a new on-chain transaction",
    description="Initiates a new Ethereum or ERC-20 token transfer. The transaction is broadcast immediately, and its confirmation status is updated in the background."
)
async def create_transaction_endpoint(
    request: TransactionRequest,
    background_tasks: BackgroundTasks,
    transaction_service: ITransactionService = Depends(get_transaction_service)
):
    try:
        # Initial creation and broadcast (fast part)
        transaction_entity = await transaction_service.create_onchain_transaction(
            from_address=request.from_address,
            to_address=request.to_address,
            asset=request.asset,
            value=request.value
        )

        # Schedule the background task to wait for confirmation and update status
        background_tasks.add_task(
            transaction_service.wait_for_and_update_transaction_status,
            tx_hash=transaction_entity.tx_hash
        )

        return TransactionResponse.model_validate(transaction_entity.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create transaction: {str(e)}")


@router.post(
    "/validate",
    response_model=TransactionValidationResponse,
    summary="Validate an on-chain transaction",
    description="Validates an Ethereum transaction by checking its status, confirmations, and if it's a credit to a managed address."
)
async def validate_transaction_endpoint(
    request: TransactionValidationRequest,
    transaction_service: ITransactionService = Depends(get_transaction_service)
):
    try:
        validated_tx = await transaction_service.validate_onchain_transaction(request.tx_hash)

        if validated_tx:
            return TransactionValidationResponse(
                is_valid=True,
                transaction_details=TransactionResponse.model_validate(
                    validated_tx.model_dump()),
                message="Transaction is valid, secure, and credited to a managed address."
            )
        else:
            return TransactionValidationResponse(
                is_valid=False,
                transaction_details=None,
                message="Transaction could not be validated or does not meet security criteria."
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Transaction validation failed: {str(e)}")


@router.get(
    "/history",
    response_model=TransactionHistoryResponse,
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
            transactions = await transaction_service.get_transaction_history_for_address(address)
        else:
            transactions = await transaction_service.get_all_transaction_history()

        return TransactionHistoryResponse(transactions=[TransactionResponse.model_validate(tx.model_dump()) for tx in transactions])
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve transaction history: {str(e)}")
