from fastapi import APIRouter

router = APIRouter()


@router.get("/welcome")
async def get_transaction_welcome():
    return {'message': 'Welcome to transactions endpoint!!'}
