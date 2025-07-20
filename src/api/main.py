from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from src.api.endpoints import transactions
from src.infra.database.config import engine
from src.infra.database import models as db_models
from src.api.dependencies import (
    initialize_nonce_manager,
    get_blockchain_service,
    get_address_repository,
    get_db
)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for the API.
    Executes code on startup and shutdown.
    """
    # Code to run on startup
    print("API is starting up...")

    async with engine.begin() as conn:
        await conn.run_sync(db_models.Base.metadata.create_all)

    print("Initializing Nonce Manager...")
    # We need a short-lived database session just for initialization
    async for session in get_db():
        try:
            address_repo = get_address_repository(session)
            blockchain_service = get_blockchain_service()

            # Create the singleton NonceManager instance
            initialize_nonce_manager(
                address_repo=address_repo,
                blockchain_service=blockchain_service
            )

            # Get the instance and call its initialization method
            from src.api.dependencies import nonce_manager_instance
            if nonce_manager_instance:
                await nonce_manager_instance.initialize_nonces()

            print("Nonce Manager initialized.")
        finally:
            # Ensure the session is closed
            await session.close()
        break  # Exit after one iteration

    yield  # The API runs here

    # Code to run on shutdown
    print("API is shutting down...")


app = FastAPI(
    title="Ethereum Interaction API",
    description="A secure API to interact with the Ethereum blockchain.",
    version="1.0.0",
    lifespan=lifespan  # Use the lifespan handler
)


# Include the API routers
app.include_router(
    transactions.router,
    prefix="/api/v1/transactions",
    tags=["Transactions"]
)
# app.include_router(
#     addresses.router,
#     prefix="/api/v1/addresses",
#     tags=["Addresses"]
# )


@app.get("/")
async def read_main():
    """Root endpoint for health checks."""
    return {"msg": "Blockchain Ethereum API is running"}
