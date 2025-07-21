from fastapi import APIRouter, Depends, HTTPException, status
from src.api.schemas import (
    AddressCreateRequest,
    AddressCreateResponse,
    AddressListResponse,
    AddressResponse
)
from src.core.interfaces import IAddressService
from src.api.dependencies import get_address_service

router = APIRouter()


@router.post(
    "/",
    response_model=AddressCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Ethereum Addresses",
    description="Generates a specified number of new Ethereum addresses, encrypts their private keys, and stores them."
)
async def create_addresses(
    request: AddressCreateRequest,
    service: IAddressService = Depends(get_address_service)
):
    try:
        created_entities = await service.create_new_addresses(request.count)

        response_addresses = [
            AddressResponse(public_address=addr.public_address) for addr in created_entities
        ]

        return AddressCreateResponse(
            message=f"Successfully created {len(response_addresses)} new addresses.",
            created_addresses=response_addresses
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/",
    response_model=AddressListResponse,
    summary="List All Managed Addresses",
    description="Retrieves a list of all public addresses that are managed by this service."
)
async def list_addresses(
    service: IAddressService = Depends(get_address_service)
):
    address_entities = await service.get_all_addresses()

    response_addresses = [
        AddressResponse(public_address=addr.public_address) for addr in address_entities
    ]

    return AddressListResponse(addresses=response_addresses)
